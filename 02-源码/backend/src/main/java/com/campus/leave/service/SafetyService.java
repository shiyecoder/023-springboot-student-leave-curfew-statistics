package com.campus.leave.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.campus.leave.common.BizException;
import com.campus.leave.entity.*;
import com.campus.leave.mapper.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;

/**
 * 安全闭环服务：晚归登记、返校码核验、未归核查工单、关怀记录。
 * 规则：有效请假期间的晚归不计入违规，但保留验证记录（has_leave=1, is_violation=0）。
 */
@Service
public class SafetyService {

    private final LateReturnMapper lateMapper;
    private final ReturnRecordMapper returnMapper;
    private final LeaveApplicationMapper leaveMapper;
    private final AbsenceCaseMapper caseMapper;
    private final CareRecordMapper careMapper;
    private final SysUserMapper userMapper;
    private final SysLogMapper logMapper;
    private final SysMessageMapper messageMapper;
    private final JdbcTemplate jdbc;

    public SafetyService(LateReturnMapper lateMapper, ReturnRecordMapper returnMapper, LeaveApplicationMapper leaveMapper,
                         AbsenceCaseMapper caseMapper, CareRecordMapper careMapper, SysUserMapper userMapper,
                         SysLogMapper logMapper, SysMessageMapper messageMapper, JdbcTemplate jdbc) {
        this.lateMapper = lateMapper;
        this.returnMapper = returnMapper;
        this.leaveMapper = leaveMapper;
        this.caseMapper = caseMapper;
        this.careMapper = careMapper;
        this.userMapper = userMapper;
        this.logMapper = logMapper;
        this.messageMapper = messageMapper;
        this.jdbc = jdbc;
    }

    // ---------------- 晚归 ----------------

    public IPage<LateReturn> latePage(Map<String, String> p) {
        QueryWrapper<LateReturn> qw = new QueryWrapper<>();
        if (LeaveService.hasText(p.get("keyword"))) {
            qw.like("student_name", p.get("keyword"));
        }
        if (LeaveService.hasText(p.get("className"))) {
            qw.eq("class_name", p.get("className"));
        }
        if (LeaveService.hasText(p.get("violation"))) {
            qw.eq("is_violation", p.get("violation"));
        }
        qw.orderByDesc("return_time");
        int pageNo = p.get("page") == null ? 1 : Integer.parseInt(p.get("page"));
        int size = p.get("size") == null ? 10 : Integer.parseInt(p.get("size"));
        return lateMapper.selectPage(new Page<>(pageNo, size), qw);
    }

    /** 晚归登记：自动匹配有效请假，无有效请假则计入违规并按连续晚归生成工单 */
    @Transactional
    public LateReturn addLate(Map<String, Object> body, SysUser user) {
        Long studentId = Long.valueOf(String.valueOf(body.get("studentId")));
        SysUser student = userMapper.selectById(studentId);
        if (student == null) {
            throw new BizException("学生不存在");
        }
        String returnTimeStr = String.valueOf(body.get("returnTime")).replace(" ", "T");
        LocalDateTime returnTime = LocalDateTime.parse(returnTimeStr);
        String remark = body.get("remark") == null ? "" : String.valueOf(body.get("remark"));

        // 有效请假：请假中/待销假，且返寝时间落在请假区间内
        List<LeaveApplication> valid = leaveMapper.selectList(new QueryWrapper<LeaveApplication>()
                .eq("student_id", studentId).in("status", "ON_LEAVE", "RETURN_PENDING")
                .le("start_time", returnTime).ge("end_time", returnTime));
        boolean hasLeave = !valid.isEmpty();

        LateReturn late = new LateReturn();
        late.setStudentId(studentId);
        late.setStudentName(student.getRealName());
        late.setDeptId(student.getDeptId());
        late.setDeptName(student.getDeptName());
        late.setClassName(student.getClassName());
        late.setDorm((student.getDormBuilding() == null ? "" : student.getDormBuilding()) + " " + student.getDormRoom());
        late.setReturnTime(returnTime);
        late.setReason(String.valueOf(body.get("reason")));
        late.setHasLeave(hasLeave ? 1 : 0);
        late.setLeaveId(hasLeave ? valid.get(0).getId() : null);
        late.setIsViolation(hasLeave ? 0 : 1);
        late.setRemark(remark);
        late.setImagePath(body.get("imagePath") == null ? null : String.valueOf(body.get("imagePath")));
        late.setRecorderId(user.getId());
        late.setRecorderName(user.getRealName());
        late.setRecordTime(LocalDateTime.now());
        lateMapper.insert(late);

        if (!hasLeave) {
            // 近 14 天晚归 3 次及以上 → 连续晚归工单
            Integer cnt = jdbc.queryForObject("select count(*) from late_return where student_id=? and is_violation=1 "
                    + "and return_time >= DATE_SUB(?, INTERVAL 14 DAY)", Integer.class, studentId, returnTime);
            if (cnt != null && cnt >= 3) {
                createCase(student, "REPEAT_LATE", "MID", "近 14 天违规晚归 " + cnt + " 次");
            }
        }
        SysLog log = new SysLog();
        log.setUserId(user.getId());
        log.setUserName(user.getRealName());
        log.setModule("晚归登记");
        log.setAction("新增");
        log.setBizNo("LW" + late.getId());
        log.setAfterStatus(hasLeave ? "有假晚归" : "违规晚归");
        log.setReason(remark);
        logMapper.insert(log);
        return late;
    }

    private void createCase(SysUser student, String type, String level, String desc) {
        AbsenceCase c = new AbsenceCase();
        c.setCaseNo("YC" + LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"))
                + String.format("%04d", new Random().nextInt(9999)));
        c.setStudentId(student.getId());
        c.setStudentName(student.getRealName());
        c.setDeptId(student.getDeptId());
        c.setDeptName(student.getDeptName());
        c.setClassName(student.getClassName());
        c.setCaseType(type);
        c.setLevel(level);
        c.setTriggerDesc(desc);
        c.setStatus("PENDING");
        c.setOwnerId(2L);
        c.setOwnerName("陈立");
        c.setDeadline(LocalDateTime.now().plusDays(2));
        caseMapper.insert(c);
        SysMessage m = new SysMessage();
        m.setTitle("新的未归核查工单");
        m.setContent(c.getCaseNo() + " · " + student.getRealName() + " · " + desc);
        m.setType("CASE");
        m.setBizNo(c.getCaseNo());
        m.setBizId(c.getId());
        m.setReceiverId(2L);
        m.setIsRead(0);
        messageMapper.insert(m);
    }

    // ---------------- 返校核销 ----------------

    public IPage<ReturnRecord> returnPage(Map<String, String> p) {
        QueryWrapper<ReturnRecord> qw = new QueryWrapper<>();
        if (LeaveService.hasText(p.get("status"))) {
            qw.eq("status", p.get("status"));
        }
        if (LeaveService.hasText(p.get("keyword"))) {
            qw.and(w -> w.like("student_name", p.get("keyword")).or().like("apply_no", p.get("keyword")));
        }
        qw.orderByDesc("create_time");
        int pageNo = p.get("page") == null ? 1 : Integer.parseInt(p.get("page"));
        int size = p.get("size") == null ? 10 : Integer.parseInt(p.get("size"));
        return returnMapper.selectPage(new Page<>(pageNo, size), qw);
    }

    /** 宿管扫码核验：校验码 + 有效期，通过后请假单置为已销假 */
    @Transactional
    public ReturnRecord verifyCode(String code, SysUser user) {
        if (code == null || !code.matches("\\d{6}")) {
            throw new BizException("请输入 6 位返校码");
        }
        ReturnRecord record = returnMapper.selectOne(new QueryWrapper<ReturnRecord>()
                .eq("return_code", code).eq("status", "PENDING").orderByDesc("id").last("limit 1"));
        if (record == null) {
            throw new BizException("返校码不存在或已使用");
        }
        if (record.getCodeExpire() != null && record.getCodeExpire().isBefore(LocalDateTime.now())) {
            record.setStatus("EXPIRED");
            returnMapper.updateById(record);
            throw new BizException("返校码已过期，请学生重新生成或使用人工核销");
        }
        doVerify(record, "CODE", user, "扫码核验通过");
        return record;
    }

    /** 辅导员人工核销：必须填写原因（≥5 字） */
    @Transactional
    public ReturnRecord manualVerify(Long recordId, String remark, SysUser user) {
        if (remark == null || remark.trim().length() < 5) {
            throw new BizException("人工核销必须填写不少于 5 个字的原因");
        }
        ReturnRecord record = returnMapper.selectById(recordId);
        if (record == null) {
            throw new BizException("销假记录不存在");
        }
        if (!"PENDING".equals(record.getStatus())) {
            throw new BizException("该记录已核销，不能重复操作");
        }
        doVerify(record, "MANUAL", user, remark.trim());
        return record;
    }

    private void doVerify(ReturnRecord record, String type, SysUser user, String remark) {
        record.setStatus("VERIFIED");
        record.setVerifyType(type);
        record.setVerifierId(user.getId());
        record.setVerifierName(user.getRealName());
        record.setVerifyTime(LocalDateTime.now());
        record.setRemark(remark);
        returnMapper.updateById(record);

        LeaveApplication leave = leaveMapper.selectById(record.getLeaveId());
        if (leave != null) {
            leave.setStatus("COMPLETED");
            leave.setOverdueFlag(0);
            leave.setCurrentApproverId(null);
            leave.setCurrentApproverName(null);
            leaveMapper.updateById(leave);
            SysLog log = new SysLog();
            log.setUserId(user.getId());
            log.setUserName(user.getRealName());
            log.setModule("返校销假");
            log.setAction(type.equals("CODE") ? "扫码核销" : "人工核销");
            log.setBizNo(leave.getApplyNo());
            log.setBeforeStatus("RETURN_PENDING");
            log.setAfterStatus("COMPLETED");
            log.setReason(remark);
            logMapper.insert(log);
            SysMessage m = new SysMessage();
            m.setTitle("销假完成");
            m.setContent(leave.getApplyNo() + " 已由 " + user.getRealName() + " 核销，请假流程闭环。");
            m.setType("SYSTEM");
            m.setBizNo(leave.getApplyNo());
            m.setBizId(leave.getId());
            m.setReceiverId(leave.getStudentId());
            m.setIsRead(0);
            messageMapper.insert(m);
            // 关联工单自动闭环
            for (AbsenceCase c : caseMapper.selectList(new QueryWrapper<AbsenceCase>()
                    .eq("student_id", leave.getStudentId()).eq("case_type", "OVERDUE").ne("status", "CLOSED"))) {
                c.setStatus("CLOSED");
                c.setCloseTime(LocalDateTime.now());
                caseMapper.updateById(c);
            }
        }
    }

    // ---------------- 工单 ----------------

    public IPage<AbsenceCase> casePage(Map<String, String> p) {
        QueryWrapper<AbsenceCase> qw = new QueryWrapper<>();
        if (LeaveService.hasText(p.get("caseType"))) {
            qw.eq("case_type", p.get("caseType"));
        }
        if (LeaveService.hasText(p.get("status"))) {
            qw.eq("status", p.get("status"));
        }
        if (LeaveService.hasText(p.get("keyword"))) {
            qw.and(w -> w.like("student_name", p.get("keyword")).or().like("case_no", p.get("keyword")));
        }
        qw.orderByAsc("status").orderByDesc("create_time");
        int pageNo = p.get("page") == null ? 1 : Integer.parseInt(p.get("page"));
        int size = p.get("size") == null ? 10 : Integer.parseInt(p.get("size"));
        return caseMapper.selectPage(new Page<>(pageNo, size), qw);
    }

    @Transactional
    public AbsenceCase createCaseManual(Map<String, Object> body, SysUser user) {
        Long studentId = Long.valueOf(String.valueOf(body.get("studentId")));
        SysUser student = userMapper.selectById(studentId);
        if (student == null) {
            throw new BizException("学生不存在");
        }
        createCase(student, String.valueOf(body.getOrDefault("caseType", "OVERDUE")),
                String.valueOf(body.getOrDefault("level", "MID")),
                String.valueOf(body.getOrDefault("triggerDesc", "人工登记异常")));
        return caseMapper.selectList(new QueryWrapper<AbsenceCase>().eq("student_id", studentId)
                .orderByDesc("id").last("limit 1")).stream().findFirst().orElse(null);
    }

    @Transactional
    public AbsenceCase closeCase(Long id, String remark, SysUser user) {
        AbsenceCase c = caseMapper.selectById(id);
        if (c == null) {
            throw new BizException("工单不存在");
        }
        if ("CLOSED".equals(c.getStatus())) {
            throw new BizException("工单已闭环，不能重复关闭");
        }
        if (remark == null || remark.trim().length() < 5) {
            throw new BizException("关闭工单需填写不少于 5 个字的核查结论");
        }
        c.setStatus("CLOSED");
        c.setCloseTime(LocalDateTime.now());
        c.setOwnerId(user.getId());
        c.setOwnerName(user.getRealName());
        caseMapper.updateById(c);
        CareRecord care = new CareRecord();
        care.setCaseId(c.getId());
        care.setStudentId(c.getStudentId());
        care.setStudentName(c.getStudentName());
        care.setCareWay("PHONE");
        care.setContent("核查结论：" + remark.trim());
        care.setResult("工单已闭环");
        care.setRecorderId(user.getId());
        care.setRecorderName(user.getRealName());
        care.setRecordTime(LocalDateTime.now());
        careMapper.insert(care);
        return c;
    }

    // ---------------- 关怀记录 ----------------

    public IPage<CareRecord> carePage(Map<String, String> p) {
        QueryWrapper<CareRecord> qw = new QueryWrapper<>();
        if (LeaveService.hasText(p.get("caseId"))) {
            qw.eq("case_id", p.get("caseId"));
        }
        if (LeaveService.hasText(p.get("keyword"))) {
            qw.like("student_name", p.get("keyword"));
        }
        qw.orderByDesc("record_time");
        int pageNo = p.get("page") == null ? 1 : Integer.parseInt(p.get("page"));
        int size = p.get("size") == null ? 10 : Integer.parseInt(p.get("size"));
        return careMapper.selectPage(new Page<>(pageNo, size), qw);
    }

    @Transactional
    public CareRecord addCare(Map<String, Object> body, SysUser user) {
        String content = String.valueOf(body.getOrDefault("content", ""));
        String result = String.valueOf(body.getOrDefault("result", ""));
        if (content.trim().length() < 5 || result.trim().length() < 5) {
            throw new BizException("学生情况与后续处置均不少于 5 个字");
        }
        CareRecord care = new CareRecord();
        care.setCaseId(body.get("caseId") == null ? null : Long.valueOf(String.valueOf(body.get("caseId"))));
        care.setStudentId(body.get("studentId") == null ? null : Long.valueOf(String.valueOf(body.get("studentId"))));
        care.setStudentName(String.valueOf(body.getOrDefault("studentName", "")));
        care.setCareWay(String.valueOf(body.getOrDefault("careWay", "PHONE")));
        care.setContent(content.trim());
        care.setResult(result.trim());
        care.setRecorderId(user.getId());
        care.setRecorderName(user.getRealName());
        care.setRecordTime(LocalDateTime.now());
        careMapper.insert(care);
        if (care.getCaseId() != null) {
            AbsenceCase c = caseMapper.selectById(care.getCaseId());
            if (c != null && "PENDING".equals(c.getStatus())) {
                c.setStatus("PROCESSING");
                c.setOwnerId(user.getId());
                c.setOwnerName(user.getRealName());
                caseMapper.updateById(c);
            }
        }
        return care;
    }

    /** 学生列表（宿管/辅导员登记用） */
    public List<SysUser> studentOptions(String keyword) {
        QueryWrapper<SysUser> qw = new QueryWrapper<SysUser>().eq("role_code", "STUDENT").eq("deleted", 0);
        if (LeaveService.hasText(keyword)) {
            qw.and(w -> w.like("real_name", keyword).or().like("user_no", keyword));
        }
        qw.last("limit 30");
        List<SysUser> list = userMapper.selectList(qw);
        list.forEach(u -> u.setPassword(null));
        return list;
    }
}
