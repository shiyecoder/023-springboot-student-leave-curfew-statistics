package com.campus.leave.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.campus.leave.common.BizException;
import com.campus.leave.common.CurrentUser;
import com.campus.leave.common.R;
import com.campus.leave.entity.*;
import com.campus.leave.mapper.*;
import com.campus.leave.service.RiskService;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** 规则配置：审批层级规则 + 风险分层权重（版本化发布）+ 计算结果与人工调整 */
@RestController
@RequestMapping("/api")
public class RuleController {

    private final LeaveRuleMapper ruleMapper;
    private final RiskRuleMapper riskRuleMapper;
    private final RiskScoreMapper scoreMapper;
    private final SysUserMapper userMapper;
    private final RiskService riskService;

    public RuleController(LeaveRuleMapper ruleMapper, RiskRuleMapper riskRuleMapper, RiskScoreMapper scoreMapper,
                          SysUserMapper userMapper, RiskService riskService) {
        this.ruleMapper = ruleMapper;
        this.riskRuleMapper = riskRuleMapper;
        this.scoreMapper = scoreMapper;
        this.userMapper = userMapper;
        this.riskService = riskService;
    }

    // ---------------- 审批层级规则 ----------------

    @GetMapping("/rule/list")
    public R<List<LeaveRule>> list() {
        return R.ok(ruleMapper.selectList(new QueryWrapper<LeaveRule>().orderByAsc("leave_type").orderByAsc("day_threshold")));
    }

    @PostMapping("/rule")
    public R<LeaveRule> save(@RequestBody LeaveRule rule) {
        if (rule.getLeaveType() == null || rule.getApprovalLevel() == null) {
            throw new BizException("请假类型与审批层级必须填写");
        }
        if (rule.getId() == null) {
            rule.setVersion("v3");
            rule.setEffectiveTime(LocalDateTime.now());
            ruleMapper.insert(rule);
        } else {
            ruleMapper.updateById(rule);
        }
        return R.ok(rule);
    }

    @DeleteMapping("/rule/{id}")
    public R<Void> delete(@PathVariable Long id) {
        ruleMapper.deleteById(id);
        return R.ok();
    }

    // ---------------- 风险分层规则 ----------------

    @GetMapping("/risk/rule/list")
    public R<List<RiskRule>> riskRules() {
        return R.ok(riskRuleMapper.selectList(new QueryWrapper<RiskRule>().orderByDesc("id")));
    }

    @GetMapping("/risk/rule/current")
    public R<RiskRule> current() {
        return R.ok(riskService.currentRule());
    }

    /** 发布新版本：权重合计必须 100%，旧版本自动停用 */
    @PostMapping("/risk/rule")
    public R<RiskRule> publish(@RequestBody RiskRule rule) {
        double sum = nz(rule.getWFreq()) + nz(rule.getWDays()) + nz(rule.getWLate())
                + nz(rule.getWOverdue()) + nz(rule.getWType()) + nz(rule.getWReject());
        if (Math.abs(sum - 100) > 0.01) {
            throw new BizException("权重合计必须等于 100%，当前为 " + sum + "%");
        }
        long count = riskRuleMapper.selectCount(null);
        rule.setId(null);
        rule.setVersion("v" + (count + 1));
        rule.setEnabled(1);
        rule.setEffectiveTime(LocalDateTime.now());
        rule.setCreateBy(CurrentUser.get().getRealName());
        riskRuleMapper.insert(rule);
        for (RiskRule old : riskRuleMapper.selectList(new QueryWrapper<RiskRule>().ne("id", rule.getId()))) {
            old.setEnabled(0);
            riskRuleMapper.updateById(old);
        }
        return R.ok(rule);
    }

    // ---------------- 计算结果 ----------------

    @GetMapping("/risk/score/page")
    public R<IPage<RiskScore>> scorePage(@RequestParam Map<String, String> p) {
        QueryWrapper<RiskScore> qw = new QueryWrapper<>();
        if (p.get("level") != null && !p.get("level").isBlank()) {
            qw.eq("level", p.get("level"));
        }
        if (p.get("keyword") != null && !p.get("keyword").isBlank()) {
            qw.like("student_name", p.get("keyword"));
        }
        qw.orderByDesc("calc_time");
        int pageNo = p.get("page") == null ? 1 : Integer.parseInt(p.get("page"));
        int size = p.get("size") == null ? 10 : Integer.parseInt(p.get("size"));
        return R.ok(scoreMapper.selectPage(new Page<>(pageNo, size), qw));
    }

    /** 单个学生的完整解释：输入快照 + 各项得分 + 结果 + 人工调整记录 */
    @GetMapping("/risk/score/{id}")
    public R<Map<String, Object>> scoreDetail(@PathVariable Long id) {
        RiskScore score = scoreMapper.selectById(id);
        if (score == null) {
            throw new BizException("计算结果不存在");
        }
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("score", score);
        data.put("student", userMapper.selectById(score.getStudentId()));
        data.put("levelText", levelText(score.getAdjustLevel() != null ? score.getAdjustLevel() : score.getLevel()));
        return R.ok(data);
    }

    @GetMapping("/risk/score/student/{studentId}")
    public R<RiskScore> latestOfStudent(@PathVariable Long studentId) {
        List<RiskScore> list = scoreMapper.selectList(new QueryWrapper<RiskScore>()
                .eq("student_id", studentId).orderByDesc("calc_time").last("limit 1"));
        return R.ok(list.isEmpty() ? null : list.get(0));
    }

    @PostMapping("/risk/score/{studentId}/evaluate")
    public R<RiskScore> evaluate(@PathVariable Long studentId) {
        SysUser student = userMapper.selectById(studentId);
        if (student == null) {
            throw new BizException("学生不存在");
        }
        return R.ok(riskService.evaluate(student, CurrentUser.get().getRealName()));
    }

    /** 人工调整等级：原因不少于 5 字，原始计算结果保留 */
    @PostMapping("/risk/score/{id}/adjust")
    public R<Void> adjust(@PathVariable Long id, @RequestBody Map<String, String> body) {
        riskService.adjust(id, body.get("level"), body.get("reason"), CurrentUser.get().getRealName());
        return R.ok();
    }

    private static double nz(BigDecimal v) {
        return v == null ? 0 : v.doubleValue();
    }

    private static String levelText(String level) {
        return switch (level == null ? "" : level) {
            case "HIGH" -> "高关注";
            case "MID" -> "中关注";
            case "LOW" -> "低关注";
            default -> "-";
        };
    }
}
