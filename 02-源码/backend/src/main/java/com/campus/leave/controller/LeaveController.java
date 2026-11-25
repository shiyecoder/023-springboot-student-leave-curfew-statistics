package com.campus.leave.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.campus.leave.common.BizException;
import com.campus.leave.common.CurrentUser;
import com.campus.leave.common.R;
import com.campus.leave.dto.LeaveCreateDTO;
import com.campus.leave.dto.TransitionDTO;
import com.campus.leave.entity.*;
import com.campus.leave.mapper.*;
import com.campus.leave.service.LeaveService;
import com.campus.leave.service.RiskService;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.*;

/** 请假申请：查询、详情、新建、编辑、状态流转、延期、风险计算、看板 */
@RestController
@RequestMapping("/api/student-leave")
public class LeaveController {

    private final LeaveService leaveService;
    private final RiskService riskService;
    private final LeaveRuleMapper ruleMapper;
    private final LeaveApplicationMapper leaveMapper;
    private final SysUserMapper userMapper;

    public LeaveController(LeaveService leaveService, RiskService riskService, LeaveRuleMapper ruleMapper,
                           LeaveApplicationMapper leaveMapper, SysUserMapper userMapper) {
        this.leaveService = leaveService;
        this.riskService = riskService;
        this.ruleMapper = ruleMapper;
        this.leaveMapper = leaveMapper;
        this.userMapper = userMapper;
    }

    @GetMapping("/page")
    public R<IPage<LeaveApplication>> page(@RequestParam Map<String, String> params) {
        return R.ok(leaveService.page(params, CurrentUser.get()));
    }

    @GetMapping("/{id}")
    public R<Map<String, Object>> detail(@PathVariable Long id) {
        return R.ok(leaveService.detail(id, CurrentUser.get()));
    }

    @PostMapping
    public R<LeaveApplication> create(@RequestBody LeaveCreateDTO dto) {
        return R.ok(leaveService.create(dto, CurrentUser.get()));
    }

    @PutMapping("/{id}")
    public R<LeaveApplication> update(@PathVariable Long id, @RequestBody LeaveCreateDTO dto) {
        if (dto.getDraft() == null && dto.getId() != null) {
            // 允许前端把版本号放在 id 之外的字段时容错处理
            dto.setDraft(false);
        }
        return R.ok(leaveService.update(id, dto, CurrentUser.get()));
    }

    @PostMapping("/{id}/transition")
    public R<LeaveApplication> transition(@PathVariable Long id, @RequestBody TransitionDTO dto) {
        return R.ok(leaveService.transition(id, dto, CurrentUser.get()));
    }

    @PostMapping("/{id}/extension")
    public R<LeaveExtension> extend(@PathVariable Long id, @RequestBody Map<String, String> body) {
        return R.ok(leaveService.extend(id, body, CurrentUser.get()));
    }

    @PostMapping("/extension/{extId}/approve")
    public R<Void> approveExtension(@PathVariable Long extId, @RequestBody Map<String, Object> body) {
        boolean pass = Boolean.parseBoolean(String.valueOf(body.getOrDefault("pass", true)));
        String opinion = String.valueOf(body.getOrDefault("opinion", ""));
        leaveService.approveExtension(extId, pass, opinion, CurrentUser.get());
        return R.ok();
    }

    /** 创新点：执行请假行为风险分层，返回明细依据并落库 */
    @PostMapping("/{id}/evaluate")
    public R<RiskScore> evaluate(@PathVariable Long id) {
        LeaveApplication leave = leaveMapper.selectById(id);
        if (leave == null) {
            throw new BizException("请假单不存在");
        }
        SysUser student = userMapper.selectById(leave.getStudentId());
        RiskScore score = riskService.evaluate(student, CurrentUser.get().getRealName());
        leave.setRiskScore(score.getTotalScore());
        leave.setRiskLevel(score.getLevel());
        leaveMapper.updateById(leave);
        return R.ok(score);
    }

    /** 表单选项：请假类型、审批规则、交通方式、班级 */
    @GetMapping("/options")
    public R<Map<String, Object>> options() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("rules", ruleMapper.selectList(new QueryWrapper<LeaveRule>().eq("enabled", 1).orderByAsc("leave_type")));
        data.put("types", List.of("病假", "事假", "公假", "实习", "跨省外出"));
        data.put("transports", List.of("地铁", "公交", "高铁", "飞机", "私家车", "步行"));
        List<SysUser> students = userMapper.selectList(new QueryWrapper<SysUser>()
                .eq("role_code", "STUDENT").eq("deleted", 0).orderByAsc("id"));
        students.forEach(s -> s.setPassword(null));
        data.put("students", students);
        return R.ok(data);
    }

    /** 首页/看板数据（后端聚合，前端不二次计算） */
    @GetMapping("/dashboard")
    public R<Map<String, Object>> dashboard(@RequestParam(defaultValue = "30") String range) {
        return R.ok(leaveService.dashboard(range, CurrentUser.get()));
    }

    /** 按当前筛选导出 CSV（导出任务记录发起人与时间） */
    @GetMapping("/export")
    public void export(@RequestParam Map<String, String> params, HttpServletResponse response) throws IOException {
        params.put("page", "1");
        params.put("size", "200");
        IPage<LeaveApplication> page = leaveService.page(params, CurrentUser.get());
        StringBuilder sb = new StringBuilder("\uFEFF申请编号,学生,班级,请假类型,开始时间,结束时间,天数,外出地点,审批状态,当前审批人\n");
        for (LeaveApplication l : page.getRecords()) {
            sb.append(String.join(",", l.getApplyNo(), l.getStudentName(), l.getClassName(), l.getLeaveType(),
                    String.valueOf(l.getStartTime()), String.valueOf(l.getEndTime()), String.valueOf(l.getDays()),
                    nvl(l.getDestination()), LeaveService.statusText(l.getStatus()), nvl(l.getCurrentApproverName()))).append("\n");
        }
        String fileName = URLEncoder.encode("请假记录-" + LocalDateTime.now() + ".csv", StandardCharsets.UTF_8);
        response.setContentType("text/csv;charset=UTF-8");
        response.setHeader("Content-Disposition", "attachment;filename=" + fileName);
        response.getWriter().write(sb.toString());
    }

    private static String nvl(String s) {
        return s == null ? "" : s.replace(",", " ");
    }
}
