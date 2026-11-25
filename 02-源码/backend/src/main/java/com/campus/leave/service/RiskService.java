package com.campus.leave.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.campus.leave.common.BizException;
import com.campus.leave.entity.RiskRule;
import com.campus.leave.entity.RiskScore;
import com.campus.leave.entity.SysUser;
import com.campus.leave.mapper.RiskRuleMapper;
import com.campus.leave.mapper.RiskScoreMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 创新点：请假行为风险分层
 * 计算口径：各因素归一化到 0-1 后乘以规则权重（权重合计 100），结果落库并保存输入快照与规则版本，
 * 保证「相同输入 + 相同规则版本 = 相同结果」，且原始计算结果不可被人工调整覆盖。
 */
@Service
public class RiskService {

    private final RiskRuleMapper ruleMapper;
    private final RiskScoreMapper scoreMapper;
    private final JdbcTemplate jdbc;

    public RiskService(RiskRuleMapper ruleMapper, RiskScoreMapper scoreMapper, JdbcTemplate jdbc) {
        this.ruleMapper = ruleMapper;
        this.scoreMapper = scoreMapper;
        this.jdbc = jdbc;
    }

    /** 当前生效规则（enabled=1 且版本最新） */
    public RiskRule currentRule() {
        RiskRule rule = ruleMapper.selectOne(new QueryWrapper<RiskRule>()
                .eq("enabled", 1).orderByDesc("id").last("limit 1"));
        if (rule == null) {
            throw new BizException("未配置风险分层规则，请先在规则配置页发布");
        }
        return rule;
    }

    /** 执行一次计算并落库；同一学生同一天多次计算会各留一条，便于追溯 */
    public RiskScore evaluate(SysUser student, String operator) {
        RiskRule rule = currentRule();
        LocalDateTime now = LocalDateTime.now();

        Integer freq = jdbc.queryForObject(
                "select count(*) from leave_application where deleted=0 and student_id=? and start_time>=DATE_SUB(now(), INTERVAL 30 DAY) " +
                        "and status not in ('DRAFT','REJECTED','CANCELLED')", Integer.class, student.getId());
        BigDecimal days = jdbc.queryForObject(
                "select coalesce(sum(days),0) from leave_application where deleted=0 and student_id=? and start_time>=DATE_SUB(now(), INTERVAL 90 DAY) " +
                        "and status not in ('DRAFT','REJECTED','CANCELLED')", BigDecimal.class, student.getId());
        Integer late = jdbc.queryForObject(
                "select count(*) from late_return where student_id=? and return_time>=DATE_SUB(now(), INTERVAL 30 DAY) and is_violation=1",
                Integer.class, student.getId());
        Integer overdue = jdbc.queryForObject(
                "select count(*) from leave_application where deleted=0 and student_id=? and (overdue_flag=1 or status='OVERDUE')",
                Integer.class, student.getId());
        Integer reject = jdbc.queryForObject(
                "select count(*) from leave_application where deleted=0 and student_id=? and status='REJECTED' " +
                        "and create_time>=DATE_SUB(now(), INTERVAL 180 DAY)", Integer.class, student.getId());
        Integer special = jdbc.queryForObject(
                "select count(*) from leave_application where deleted=0 and student_id=? and leave_type in ('跨省外出','公假') " +
                        "and start_time>=DATE_SUB(now(), INTERVAL 90 DAY)", Integer.class, student.getId());

        double fNorm = Math.min(freq / 8.0, 1);
        double dNorm = Math.min(days.doubleValue() / 30.0, 1);
        double lNorm = Math.min(late / 6.0, 1);
        double oNorm = Math.min(overdue / 4.0, 1);
        double tNorm = special > 0 ? 1.0 : 0.2;
        double rNorm = Math.min(reject / 3.0, 1);

        double sFreq = fNorm * rule.getWFreq().doubleValue();
        double sDays = dNorm * rule.getWDays().doubleValue();
        double sLate = lNorm * rule.getWLate().doubleValue();
        double sOver = oNorm * rule.getWOverdue().doubleValue();
        double sType = tNorm * rule.getWType().doubleValue();
        double sRej = rNorm * rule.getWReject().doubleValue();
        double total = sFreq + sDays + sLate + sOver + sType + sRej;

        String level = total >= rule.getHighThreshold().doubleValue() ? "HIGH"
                : (total >= rule.getLowThreshold().doubleValue() ? "MID" : "LOW");

        Map<String, Double> detail = new LinkedHashMap<>();
        detail.put("近30天请假次数", round(sFreq));
        detail.put("累计请假天数", round(sDays));
        detail.put("晚归次数", round(sLate));
        detail.put("逾期销假次数", round(sOver));
        detail.put("请假类型", round(sType));
        detail.put("审批驳回次数", round(sRej));

        StringBuilder sb = new StringBuilder();
        if ("HIGH".equals(level)) {
            sb.append("关注等级高：");
        } else if ("MID".equals(level)) {
            sb.append("关注等级中：");
        } else {
            sb.append("关注等级低：");
        }
        if (sOver >= 8) {
            sb.append("逾期销假贡献最高（").append(round(sOver)).append(" 分），建议优先提醒按时销假；");
        }
        if (sLate >= 6) {
            sb.append("近 30 天晚归 ").append(late).append(" 次，建议了解作息与实习安排；");
        }
        if (sDays >= 8) {
            sb.append("累计请假 ").append(days).append(" 天，占学期比例偏高；");
        }
        if (sRej >= 1) {
            sb.append("存在 ").append(reject).append(" 次驳回记录，建议核实事由真实性；");
        }
        if (sb.length() < 12) {
            sb.append("各项指标均在正常区间，保持常规关注即可。");
        }
        sb.append(" 改进项：返校后 2 小时内提交销假、离校前核对返校码有效期。");
        if (days.doubleValue() == 0) {
            sb.append(" 提示：该生暂无近 90 天请假数据，部分因素未参与计算。");
        }

        RiskScore score = new RiskScore();
        score.setStudentId(student.getId());
        score.setStudentName(student.getRealName());
        score.setClassName(student.getClassName());
        score.setRuleVersion(rule.getVersion());
        score.setSnapshot(String.format("{\"freq\":%d,\"days\":%s,\"late\":%d,\"overdue\":%d,\"special\":%d,\"reject\":%d}",
                freq, days, late, overdue, special, reject));
        score.setDetailJson(toJson(detail));
        score.setTotalScore(BigDecimal.valueOf(total).setScale(1, RoundingMode.HALF_UP));
        score.setLevel(level);
        score.setSuggest(sb.toString());
        score.setCalcTime(now);
        scoreMapper.insert(score);
        return score;
    }

    /** 人工调整最终等级：必须填原因，原始计算结果保留不覆盖 */
    public void adjust(Long id, String level, String reason, String operator) {
        if (reason == null || reason.trim().length() < 5) {
            throw new BizException("人工调整必须填写不少于 5 个字的原因");
        }
        RiskScore score = scoreMapper.selectById(id);
        if (score == null) {
            throw new BizException("计算结果不存在");
        }
        score.setAdjustLevel(level);
        score.setAdjustReason(reason.trim());
        score.setAdjustBy(operator);
        score.setAdjustTime(LocalDateTime.now());
        scoreMapper.updateById(score);
    }

    private static double round(double v) {
        return BigDecimal.valueOf(v).setScale(1, RoundingMode.HALF_UP).doubleValue();
    }

    private static String toJson(Map<String, Double> map) {
        StringBuilder sb = new StringBuilder("{");
        int i = 0;
        for (Map.Entry<String, Double> e : map.entrySet()) {
            if (i++ > 0) {
                sb.append(",");
            }
            sb.append("\"").append(e.getKey()).append("\":").append(e.getValue());
        }
        return sb.append("}").toString();
    }
}
