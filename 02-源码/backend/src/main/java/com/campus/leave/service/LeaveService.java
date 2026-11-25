package com.campus.leave.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.campus.leave.common.BizException;
import com.campus.leave.dto.LeaveCreateDTO;
import com.campus.leave.dto.TransitionDTO;
import com.campus.leave.entity.*;
import com.campus.leave.mapper.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 请假核心服务：
 * 1) 申请校验（时间冲突、天数、材料、超期未销假、联系方式）
 * 2) 规则匹配审批层级（leave_rule）
 * 3) 状态机流转（草稿→辅导员审批→院系审批→请假中→待销假→已销假）
 * 4) 返校码生成与核销、延期重审
 */
@Service
public class LeaveService {

    public static final String DRAFT = "DRAFT";
    public static final String COUNSELOR_PENDING = "COUNSELOR_PENDING";
    public static final String DEPT_PENDING = "DEPT_PENDING";
    public static final String ON_LEAVE = "ON_LEAVE";
    public static final String RETURN_PENDING = "RETURN_PENDING";
    public static final String COMPLETED = "COMPLETED";
    public static final String REJECTED = "REJECTED";
    public static final String CANCELLED = "CANCELLED";

    private final LeaveApplicationMapper leaveMapper;
    private final LeaveRuleMapper ruleMapper;
    private final LeaveApprovalMapper approvalMapper;
    private final LeaveExtensionMapper extensionMapper;
    private final ReturnRecordMapper returnMapper;
    private final SysUserMapper userMapper;
    private final SysLogMapper logMapper;
    private final SysMessageMapper messageMapper;
    private final AbsenceCaseMapper caseMapper;
    private final RiskService riskService;
    private final JdbcTemplate jdbc;

    public LeaveService(LeaveApplicationMapper leaveMapper, LeaveRuleMapper ruleMapper, LeaveApprovalMapper approvalMapper,
                        LeaveExtensionMapper extensionMapper, ReturnRecordMapper returnMapper, SysUserMapper userMapper,
                        SysLogMapper logMapper, SysMessageMapper messageMapper, AbsenceCaseMapper caseMapper,
                        RiskService riskService, JdbcTemplate jdbc) {
        this.leaveMapper = leaveMapper;
        this.ruleMapper = ruleMapper;
        this.approvalMapper = approvalMapper;
        this.extensionMapper = extensionMapper;
        this.returnMapper = returnMapper;
        this.userMapper = userMapper;
        this.logMapper = logMapper;
        this.messageMapper = messageMapper;
        this.caseMapper = caseMapper;
        this.riskService = riskService;
        this.jdbc = jdbc;
    }

    // ---------------- 查询 ----------------

    /** 数据范围：学生本人 / 辅导员所带班级 / 院系负责人本院系 / 管理员全校 */
    public IPage<LeaveApplication> page(Map<String, String> p, SysUser user) {
        refreshStatus();
        int pageNo = intOf(p.get("page"), 1);
        int size = intOf(p.get("size"), 10);
        QueryWrapper<LeaveApplication> qw = new QueryWrapper<>();
        applyScope(qw, user);
        if (hasText(p.get("keyword"))) {
            qw.and(w -> w.like("apply_no", p.get("keyword")).or().like("student_name", p.get("keyword")));
        }
        if (hasText(p.get("leaveType"))) {
            qw.eq("leave_type", p.get("leaveType"));
        }
        if (hasText(p.get("status"))) {
            qw.eq("status", p.get("status"));
        }
        if (hasText(p.get("className"))) {
            qw.eq("class_name", p.get("className"));
        }
        if (hasText(p.get("deptId"))) {
            qw.eq("dept_id", p.get("deptId"));
        }
        if (hasText(p.get("startDate"))) {
            qw.ge("start_time", p.get("startDate") + " 00:00:00");
        }
        if (hasText(p.get("endDate"))) {
            qw.le("start_time", p.get("endDate") + " 23:59:59");
        }
        if ("1".equals(p.get("overdue"))) {
            qw.eq("overdue_flag", 1);
        }
        if ("1".equals(p.get("todo"))) {
            // 待我处理：辅导员/院系待审批，或学生待销假
            if ("STUDENT".equals(user.getRoleCode())) {
                qw.eq("status", RETURN_PENDING);
            } else {
                qw.in("status", COUNSELOR_PENDING, DEPT_PENDING, RETURN_PENDING);
            }
        }
        qw.orderByDesc("update_time");
        return leaveMapper.selectPage(new Page<>(pageNo, size), qw);
    }

    public void applyScope(QueryWrapper<LeaveApplication> qw, SysUser user) {
        switch (user.getRoleCode()) {
            case "STUDENT" -> qw.eq("student_id", user.getId());
            case "COUNSELOR" -> {
                List<String> classes = splitClasses(user.getClassName());
                if (classes.isEmpty()) {
                    qw.eq("student_id", -1);
                } else {
                    qw.in("class_name", classes);
                }
            }
            case "DEPT_HEAD", "DORM" -> qw.eq("dept_id", user.getDeptId());
            default -> {
                // ADMIN：全校
            }
        }
    }

    public Map<String, Object> detail(Long id, SysUser user) {
        LeaveApplication leave = leaveMapper.selectById(id);
        if (leave == null) {
            throw new BizException("请假单不存在");
        }
        checkVisible(leave, user);
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("leave", leave);
        map.put("approvals", approvalMapper.selectList(new QueryWrapper<LeaveApproval>()
                .eq("leave_id", id).orderByAsc("create_time")));
        map.put("extensions", extensionMapper.selectList(new QueryWrapper<LeaveExtension>()
                .eq("leave_id", id).orderByDesc("apply_time")));
        map.put("returns", returnMapper.selectList(new QueryWrapper<ReturnRecord>()
                .eq("leave_id", id).orderByDesc("create_time")));
        map.put("logs", logMapper.selectList(new QueryWrapper<SysLog>()
                .eq("biz_no", leave.getApplyNo()).orderByDesc("create_time")));
        map.put("student", userMapper.selectById(leave.getStudentId()));
        return map;
    }

    private void checkVisible(LeaveApplication leave, SysUser user) {
        switch (user.getRoleCode()) {
            case "STUDENT" -> {
                if (!leave.getStudentId().equals(user.getId())) {
                    throw new BizException("无权查看他人请假记录");
                }
            }
            case "COUNSELOR" -> {
                if (!splitClasses(user.getClassName()).contains(leave.getClassName())) {
                    throw new BizException("无权查看非本人所带班级的记录");
                }
            }
            case "DEPT_HEAD", "DORM" -> {
                if (!Objects.equals(leave.getDeptId(), user.getDeptId())) {
                    throw new BizException("无权查看其他院系的记录");
                }
            }
            default -> {
            }
        }
    }

    // ---------------- 新建 / 编辑 ------------

    @Transactional
    public LeaveApplication create(LeaveCreateDTO d, SysUser user) {
        SysUser student = "STUDENT".equals(user.getRoleCode()) ? user : userMapper.selectById(d.getId() == null ? user.getId() : d.getId());
        if (student == null) {
            throw new BizException("学生信息不存在");
        }
        validate(d, student);

        LeaveRule rule = matchRule(d.getLeaveType(), d.getDays());
        boolean needDept = rule.getApprovalLevel().contains("DEPT");

        LeaveApplication leave = new LeaveApplication();
        leave.setApplyNo(nextApplyNo());
        leave.setStudentId(student.getId());
        leave.setStudentName(student.getRealName());
        leave.setDeptId(student.getDeptId());
        leave.setDeptName(student.getDeptName());
        leave.setClassName(student.getClassName());
        leave.setLeaveType(d.getLeaveType());
        leave.setStartTime(d.getStartTime());
        leave.setEndTime(d.getEndTime());
        leave.setDays(d.getDays());
        leave.setDestination(d.getDestination());
        leave.setContactName(d.getContactName());
        leave.setContactPhone(d.getContactPhone());
        leave.setTransport(d.getTransport());
        leave.setReason(d.getReason());
        leave.setAttachmentPath(d.getAttachmentPath());
        leave.setApprovalLevel(rule.getApprovalLevel());
        leave.setNeedDept(needDept ? 1 : 0);
        leave.setOverdueFlag(0);
        leave.setReturnDeadline(d.getEndTime().plusHours(2));
        leave.setVersion(0);
        boolean draft = Boolean.TRUE.equals(d.getDraft());
        leave.setStatus(draft ? DRAFT : COUNSELOR_PENDING);
        if (!draft) {
            assignCounselor(leave);
        }
        // 新建即计算一次风险分层，结果存入单据快照（可追溯）
        RiskScore score = riskService.evaluate(student, user.getRealName());
        leave.setRiskScore(score.getTotalScore());
        leave.setRiskLevel(score.getLevel());
        leaveMapper.insert(leave);

        writeLog(user, "请假申请", draft ? "保存草稿" : "提交申请", leave.getApplyNo(), null, leave.getStatus(), null);
        if (!draft) {
            pushMessage(leave.getCurrentApproverId(), "新的请假申请待审批",
                    leave.getApplyNo() + " 由 " + leave.getStudentName() + " 提交，请及时处理。", "APPROVAL", leave);
        }
        return leave;
    }

    @Transactional
    public LeaveApplication update(Long id, LeaveCreateDTO d, SysUser user) {
        LeaveApplication leave = leaveMapper.selectById(id);
        if (leave == null) {
            throw new BizException("请假单不存在");
        }
        if (!leave.getStudentId().equals(user.getId()) && !"ADMIN".equals(user.getRoleCode())) {
            throw new BizException("只能修改本人的请假申请");
        }
        if (!DRAFT.equals(leave.getStatus()) && !REJECTED.equals(leave.getStatus())) {
            throw new BizException("当前状态不允许修改，请先撤回或联系审批人");
        }
        if (d.getVersion() != null && !d.getVersion().equals(leave.getVersion())) {
            throw new BizException("数据已被他人更新，请刷新后重试");
        }
        validate(d, userMapper.selectById(leave.getStudentId()));
        LeaveRule rule = matchRule(d.getLeaveType(), d.getDays());
        leave.setLeaveType(d.getLeaveType());
        leave.setStartTime(d.getStartTime());
        leave.setEndTime(d.getEndTime());
        leave.setDays(d.getDays());
        leave.setDestination(d.getDestination());
        leave.setContactName(d.getContactName());
        leave.setContactPhone(d.getContactPhone());
        leave.setTransport(d.getTransport());
        leave.setReason(d.getReason());
        leave.setAttachmentPath(d.getAttachmentPath());
        leave.setApprovalLevel(rule.getApprovalLevel());
        leave.setNeedDept(rule.getApprovalLevel().contains("DEPT") ? 1 : 0);
        leave.setReturnDeadline(d.getEndTime().plusHours(2));
        if (!Boolean.TRUE.equals(d.getDraft())) {
            leave.setStatus(COUNSELOR_PENDING);
            assignCounselor(leave);
        }
        if (leaveMapper.updateById(leave) == 0) {
            throw new BizException("数据已被他人更新，请刷新后重试");
        }
        writeLog(user, "请假申请", "修改", leave.getApplyNo(), null, leave.getStatus(), null);
        return leave;
    }

    /** 自动校验：时间顺序、重叠、超期未销假、材料、联系方式 */
    private void validate(LeaveCreateDTO d, SysUser student) {
        if (d.getStartTime() == null || d.getEndTime() == null) {
            throw new BizException("请填写请假开始与结束时间");
        }
        if (!d.getEndTime().isAfter(d.getStartTime())) {
            throw new BizException("结束时间必须晚于开始时间");
        }
        if (d.getReason() == null || d.getReason().trim().length() < 5) {
            throw new BizException("请假事由不少于 5 个字");
        }
        if (d.getDays() == null || d.getDays().doubleValue() <= 0) {
            throw new BizException("请假天数必须大于 0");
        }
        if (d.getContactPhone() == null || !d.getContactPhone().matches("[0-9*\\-]{6,20}")) {
            throw new BizException("紧急联系电话格式不正确");
        }
        // 时间重叠校验：与在途/有效的请假区间冲突
        Integer overlap = jdbc.queryForObject(
                "select count(*) from leave_application where deleted=0 and student_id=? and status in " +
                        "('COUNSELOR_PENDING','DEPT_PENDING','ON_LEAVE','RETURN_PENDING') and start_time < ? and end_time > ?",
                Integer.class, student.getId(), d.getEndTime(), d.getStartTime());
        if (overlap != null && overlap > 0) {
            throw new BizException("与已有请假时间重叠，请调整起止时间");
        }
        // 超期未销假时不得新建普通外出假
        Integer overdue = jdbc.queryForObject(
                "select count(*) from leave_application where deleted=0 and student_id=? and (overdue_flag=1 or status='OVERDUE')",
                Integer.class, student.getId());
        if (overdue != null && overdue > 0 && !"病假".equals(d.getLeaveType())) {
            throw new BizException("存在超期未销假的请假单，请先完成销假后再申请");
        }
        LeaveRule rule = matchRule(d.getLeaveType(), d.getDays());
        boolean needProof = rule.getRequiredMaterial() != null && rule.getRequiredMaterial().contains("证明");
        if (needProof && (d.getAttachmentPath() == null || d.getAttachmentPath().isBlank())) {
            throw new BizException("该请假类型需上传" + rule.getRequiredMaterial());
        }
    }

    /** 按类型 + 天数匹配审批层级；阈值 0 表示该类型一律升级 */
    public LeaveRule matchRule(String type, BigDecimal days) {
        List<LeaveRule> rules = ruleMapper.selectList(new QueryWrapper<LeaveRule>()
                .eq("leave_type", type).eq("enabled", 1).orderByAsc("day_threshold"));
        if (rules.isEmpty()) {
            throw new BizException("该请假类型未配置审批规则");
        }
        LeaveRule hit = rules.get(0);
        for (LeaveRule r : rules) {
            if (days.doubleValue() > r.getDayThreshold().doubleValue()) {
                hit = r;
            }
        }
        return hit;
    }

    private void assignCounselor(LeaveApplication leave) {
        SysUser counselor = userMapper.selectList(new QueryWrapper<SysUser>()
                        .eq("role_code", "COUNSELOR").eq("deleted", 0).like("class_name", leave.getClassName()))
                .stream().findFirst().orElse(null);
        if (counselor == null) {
            counselor = userMapper.selectList(new QueryWrapper<SysUser>().eq("role_code", "DEPT_HEAD").eq("deleted", 0))
                    .stream().filter(u -> Objects.equals(u.getDeptId(), leave.getDeptId())).findFirst().orElse(null);
        }
        leave.setCurrentApproverId(counselor == null ? null : counselor.getId());
        leave.setCurrentApproverName(counselor == null ? "院系学工负责人" : counselor.getRealName());
    }

    private void assignDeptHead(LeaveApplication leave) {
        SysUser head = userMapper.selectList(new QueryWrapper<SysUser>().eq("role_code", "DEPT_HEAD").eq("deleted", 0))
                .stream().filter(u -> Objects.equals(u.getDeptId(), leave.getDeptId())).findFirst().orElse(null);
        leave.setCurrentApproverId(head == null ? null : head.getId());
        leave.setCurrentApproverName(head == null ? "院系学工负责人" : head.getRealName());
    }

    // ---------------- 状态流转 ----------------

    @Transactional
    public LeaveApplication transition(Long id, TransitionDTO d, SysUser user) {
        LeaveApplication leave = leaveMapper.selectById(id);
        if (leave == null) {
            throw new BizException("请假单不存在");
        }
        String action = d.getAction() == null ? "" : d.getAction().toUpperCase();
        String before = leave.getStatus();
        LocalDateTime now = LocalDateTime.now();
        switch (action) {
            case "SUBMIT" -> {
                requireOwner(leave, user);
                if (!DRAFT.equals(before) && !REJECTED.equals(before)) {
                    throw new BizException("仅草稿或已驳回的申请可以提交");
                }
                assignCounselor(leave);
                leave.setStatus(COUNSELOR_PENDING);
                pushMessage(leave.getCurrentApproverId(), "请假申请待审批", leave.getApplyNo() + " 已提交，请审批。", "APPROVAL", leave);
            }
            case "APPROVE" -> {
                requireApprover(leave, user);
                if (COUNSELOR_PENDING.equals(before)) {
                    if (leave.getNeedDept() != null && leave.getNeedDept() == 1) {
                        assignDeptHead(leave);
                        leave.setStatus(DEPT_PENDING);
                    } else {
                        leave.setStatus(ON_LEAVE);
                        leave.setCurrentApproverId(null);
                        leave.setCurrentApproverName(null);
                    }
                } else if (DEPT_PENDING.equals(before)) {
                    leave.setStatus(ON_LEAVE);
                    leave.setCurrentApproverId(null);
                    leave.setCurrentApproverName(null);
                } else {
                    throw new BizException("当前状态不允许审批通过");
                }
                writeApproval(leave, COUNSELOR_PENDING.equals(before) ? "COUNSELOR" : "DEPT", user, "APPROVE", d.getOpinion());
                pushMessage(leave.getStudentId(), "请假审批结果", leave.getApplyNo() + " 已通过审批，当前状态：" + statusText(leave.getStatus()), "APPROVAL", leave);
            }
            case "REJECT" -> {
                requireApprover(leave, user);
                String reason = firstText(d.getOpinion(), d.getReason());
                if (reason.length() < 5) {
                    throw new BizException("驳回必须填写不少于 5 个字的原因");
                }
                writeApproval(leave, DEPT_PENDING.equals(before) ? "DEPT" : "COUNSELOR", user, "REJECT", reason);
                leave.setStatus(REJECTED);
                leave.setCurrentApproverId(null);
                leave.setCurrentApproverName(null);
                pushMessage(leave.getStudentId(), "请假被驳回", leave.getApplyNo() + " 被驳回：" + reason, "APPROVAL", leave);
            }
            case "CANCEL" -> {
                requireOwner(leave, user);
                if (COMPLETED.equals(before) || CANCELLED.equals(before) || REJECTED.equals(before)) {
                    throw new BizException("当前状态不允许取消");
                }
                String reason = firstText(d.getReason(), d.getOpinion());
                if (reason.length() < 5) {
                    throw new BizException("取消请假必须填写不少于 5 个字的原因");
                }
                leave.setStatus(CANCELLED);
                leave.setCancelReason(reason);
                pushMessage(leave.getCurrentApproverId(), "请假申请已取消", leave.getApplyNo() + " 已由学生取消。", "APPROVAL", leave);
            }
            case "RETURN_CODE" -> {
                requireOwner(leave, user);
                if (!ON_LEAVE.equals(before) && !RETURN_PENDING.equals(before)) {
                    throw new BizException("仅请假中的单据可以生成返校码");
                }
                leave.setStatus(RETURN_PENDING);
                createReturnCode(leave, user);
                pushMessage(leave.getCurrentApproverId(), "学生已提交销假", leave.getApplyNo() + " 已生成返校码，等待宿管核验。", "APPROVAL", leave);
            }
            default -> throw new BizException("不支持的流转动作：" + action);
        }
        leave.setUpdateTime(now);
        if (leaveMapper.updateById(leave) == 0) {
            throw new BizException("数据已被他人更新，请刷新后重试");
        }
        writeLog(user, "请假流转", action, leave.getApplyNo(), before, leave.getStatus(), d.getReason());
        return leaveMapper.selectById(id);
    }

    /** 生成 6 位限时返校码（有效期 10 分钟） */
    private void createReturnCode(LeaveApplication leave, SysUser user) {
        String code = String.valueOf(100000 + new Random().nextInt(899999));
        ReturnRecord r = new ReturnRecord();
        r.setLeaveId(leave.getId());
        r.setApplyNo(leave.getApplyNo());
        r.setStudentId(leave.getStudentId());
        r.setStudentName(leave.getStudentName());
        r.setReturnCode(code);
        r.setCodeExpire(LocalDateTime.now().plusMinutes(10));
        r.setStatus("PENDING");
        r.setRemark("学生提交销假，返校码有效期 10 分钟");
        returnMapper.insert(r);
        writeLog(user, "返校销假", "生成返校码", leave.getApplyNo(), leave.getStatus(), RETURN_PENDING, "返校码 " + code);
    }

    // ---------------- 延期 ----------------

    @Transactional
    public LeaveExtension extend(Long leaveId, Map<String, String> body, SysUser user) {
        LeaveApplication leave = leaveMapper.selectById(leaveId);
        if (leave == null) {
            throw new BizException("请假单不存在");
        }
        requireOwner(leave, user);
        if (!ON_LEAVE.equals(leave.getStatus()) && !RETURN_PENDING.equals(leave.getStatus())) {
            throw new BizException("仅请假中的单据可以申请延期");
        }
        String newEnd = body.get("newEndTime");
        String reason = body.get("reason");
        if (newEnd == null || reason == null || reason.trim().length() < 5) {
            throw new BizException("请填写新的结束时间与不少于 5 个字的延期原因");
        }
        LocalDateTime newEndTime = LocalDateTime.parse(newEnd.replace(" ", "T"));
        if (!newEndTime.isAfter(leave.getEndTime())) {
            throw new BizException("延期后的结束时间必须晚于原结束时间");
        }
        BigDecimal addDays = BigDecimal.valueOf(Duration.between(leave.getEndTime(), newEndTime).toHours())
                .divide(BigDecimal.valueOf(10), 1, RoundingMode.HALF_UP);

        LeaveExtension ext = new LeaveExtension();
        ext.setLeaveId(leaveId);
        ext.setOldEndTime(leave.getEndTime());
        ext.setNewEndTime(newEndTime);
        ext.setAddDays(addDays);
        ext.setReason(reason.trim());
        ext.setStatus("PENDING");
        ext.setApplyTime(LocalDateTime.now());
        extensionMapper.insert(ext);

        // 延期按新总时长重新匹配审批层级（可能从辅导员升级到院系）
        BigDecimal totalDays = leave.getDays().add(addDays);
        LeaveRule rule = matchRule(leave.getLeaveType(), totalDays);
        boolean upgrade = rule.getApprovalLevel().contains("DEPT") && (leave.getNeedDept() == null || leave.getNeedDept() == 0);
        leave.setApprovalLevel(rule.getApprovalLevel());
        leave.setNeedDept(rule.getApprovalLevel().contains("DEPT") ? 1 : 0);
        leave.setStatus(COUNSELOR_PENDING);
        leave.setEndTime(newEndTime);
        leave.setDays(totalDays);
        leave.setReturnDeadline(newEndTime.plusHours(2));
        assignCounselor(leave);
        leaveMapper.updateById(leave);
        writeLog(user, "请假延期", "提交延期", leave.getApplyNo(), ON_LEAVE, COUNSELOR_PENDING,
                reason + (upgrade ? "（因延期升级为院系审批）" : ""));
        pushMessage(leave.getCurrentApproverId(), "延期申请待重新审批",
                leave.getApplyNo() + " 申请延期至 " + newEndTime + "，请按新总时长审批。", "APPROVAL", leave);
        return ext;
    }

    /** 延期审批（通过后同步更新请假单结束时间） */
    @Transactional
    public void approveExtension(Long extId, boolean pass, String opinion, SysUser user) {
        LeaveExtension ext = extensionMapper.selectById(extId);
        if (ext == null) {
            throw new BizException("延期记录不存在");
        }
        ext.setStatus(pass ? "APPROVED" : "REJECTED");
        ext.setApproverId(user.getId());
        ext.setApproverName(user.getRealName());
        ext.setApproveTime(LocalDateTime.now());
        ext.setOpinion(opinion);
        extensionMapper.updateById(ext);
        LeaveApplication leave = leaveMapper.selectById(ext.getLeaveId());
        if (leave != null) {
            leave.setEndTime(ext.getNewEndTime());
            leave.setReturnDeadline(ext.getNewEndTime().plusHours(2));
            leave.setStatus(pass ? ON_LEAVE : RETURN_PENDING);
            leaveMapper.updateById(leave);
            writeLog(user, "请假延期", pass ? "同意延期" : "驳回延期", leave.getApplyNo(),
                    COUNSELOR_PENDING, leave.getStatus(), opinion);
        }
    }

    // ---------------- 超期标记与工单 ----------------

    /**
     * 每次列表/看板访问时轻量刷新状态：
     * 已过结束时间仍在请假中 → 待销假；超过应销假时间 → 标记超期并生成未归核查工单。
     */
    public void refreshStatus() {
        jdbc.update("update leave_application set status='RETURN_PENDING', update_time=now() " +
                "where deleted=0 and status='ON_LEAVE' and end_time < now()");
        jdbc.update("update leave_application set overdue_flag=1, update_time=now() " +
                "where deleted=0 and status='RETURN_PENDING' and overdue_flag=0 and return_deadline < now()");
        List<Map<String, Object>> list = jdbc.queryForList(
                "select l.* from leave_application l where l.deleted=0 and l.overdue_flag=1 and l.status='RETURN_PENDING' " +
                        "and not exists (select 1 from absence_case c where c.case_type='OVERDUE' and c.student_id=l.student_id " +
                        "and c.status <> 'CLOSED') limit 20");
        for (Map<String, Object> row : list) {
            AbsenceCase c = new AbsenceCase();
            c.setCaseNo("YC" + LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"))
                    + String.format("%04d", new Random().nextInt(9999)));
            c.setStudentId(((Number) row.get("student_id")).longValue());
            c.setStudentName(String.valueOf(row.get("student_name")));
            c.setDeptId(row.get("dept_id") == null ? null : ((Number) row.get("dept_id")).longValue());
            c.setDeptName((String) row.get("dept_name"));
            c.setClassName((String) row.get("class_name"));
            c.setCaseType("OVERDUE");
            c.setLevel("HIGH");
            c.setTriggerDesc("请假单 " + row.get("apply_no") + " 超过应销假时间未提交销假");
            c.setStatus("PENDING");
            c.setOwnerId(2L);
            c.setOwnerName("陈立");
            c.setDeadline(LocalDateTime.now().plusDays(1));
            caseMapper.insert(c);
        }
    }

    // ---------------- 看板 ----------------

    public Map<String, Object> dashboard(String range, SysUser user) {
        refreshStatus();
        int days = switch (range == null ? "30" : range) {
            case "month" -> 30;
            case "quarter" -> 90;
            case "year" -> 365;
            default -> 30;
        };
        String scopeSql = switch (user.getRoleCode()) {
            case "STUDENT" -> " and l.student_id=" + user.getId();
            case "COUNSELOR" -> " and l.class_name in (" + quoteList(splitClasses(user.getClassName())) + ")";
            case "DEPT_HEAD", "DORM" -> " and l.dept_id=" + user.getDeptId();
            default -> "";
        };
        Map<String, Object> res = new LinkedHashMap<>();
        // 核心指标
        res.put("leaveCount", jdbc.queryForObject("select count(*) from leave_application l where l.deleted=0 "
                + "and l.create_time >= DATE_SUB(now(), INTERVAL " + days + " DAY)" + scopeSql, Integer.class));
        res.put("studentCount", jdbc.queryForObject("select count(distinct l.student_id) from leave_application l "
                + "where l.deleted=0 and l.create_time >= DATE_SUB(now(), INTERVAL " + days + " DAY)" + scopeSql, Integer.class));
        res.put("daysSum", jdbc.queryForObject("select coalesce(sum(l.days),0) from leave_application l where l.deleted=0 "
                + "and l.create_time >= DATE_SUB(now(), INTERVAL " + days + " DAY)" + scopeSql, BigDecimal.class));
        res.put("onLeave", jdbc.queryForObject("select count(*) from leave_application l where l.deleted=0 and l.status='ON_LEAVE'" + scopeSql, Integer.class));
        res.put("pending", jdbc.queryForObject("select count(*) from leave_application l where l.deleted=0 "
                + "and l.status in ('COUNSELOR_PENDING','DEPT_PENDING')" + scopeSql, Integer.class));
        res.put("overdue", jdbc.queryForObject("select count(*) from leave_application l where l.deleted=0 and l.overdue_flag=1" + scopeSql, Integer.class));
        res.put("lateCount", jdbc.queryForObject("select count(*) from late_return where return_time >= DATE_SUB(now(), INTERVAL " + days + " DAY)", Integer.class));
        res.put("openCase", jdbc.queryForObject("select count(*) from absence_case where status <> 'CLOSED'", Integer.class));
        res.put("closedCase", jdbc.queryForObject("select count(*) from absence_case where status = 'CLOSED'", Integer.class));
        res.put("avgHours", jdbc.queryForObject("select coalesce(round(avg(timestampdiff(minute, l.create_time, a.create_time))/60,1),0) "
                + "from leave_application l join leave_approval a on a.leave_id=l.id and a.action='APPROVE' "
                + "where l.create_time >= DATE_SUB(now(), INTERVAL " + days + " DAY)" + scopeSql, BigDecimal.class));

        // 图表：类型分布 / 状态分布 / 趋势 / 院系排行 / 晚归时段 / 风险分布
        res.put("typeDist", jdbc.queryForList("select l.leave_type as name, count(*) as value from leave_application l "
                + "where l.deleted=0 and l.create_time >= DATE_SUB(now(), INTERVAL " + days + " DAY)" + scopeSql
                + " group by l.leave_type order by value desc"));
        res.put("statusDist", jdbc.queryForList("select l.status as name, count(*) as value from leave_application l "
                + "where l.deleted=0" + scopeSql + " group by l.status"));
        res.put("trend", jdbc.queryForList("select date_format(l.create_time,'%m-%d') as name, count(*) as value "
                + "from leave_application l where l.deleted=0 and l.create_time >= DATE_SUB(now(), INTERVAL 30 DAY)" + scopeSql
                + " group by date_format(l.create_time,'%m-%d') order by name"));
        res.put("deptRank", jdbc.queryForList("select l.dept_name as name, count(*) as value from leave_application l "
                + "where l.deleted=0 and l.overdue_flag=1" + scopeSql + " group by l.dept_name order by value desc limit 5"));
        res.put("lateHours", jdbc.queryForList("select concat(hour(return_time),':00') as name, count(*) as value "
                + "from late_return where return_time >= DATE_SUB(now(), INTERVAL " + days + " DAY) group by concat(hour(return_time),':00') order by name"));
        res.put("riskDist", jdbc.queryForList("select coalesce(adjust_level, level) as name, count(*) as value "
                + "from risk_score group by coalesce(adjust_level, level)"));
        res.put("adoptRate", jdbc.queryForObject("select round(sum(adjust_level is null)/count(*)*100,1) from risk_score", BigDecimal.class));
        res.put("focusStudents", jdbc.queryForList("select s.student_name as name, s.class_name as className, s.total_score as score, "
                + "s.level, s.suggest from risk_score s where s.calc_time >= DATE_SUB(now(), INTERVAL 30 DAY) "
                + "and coalesce(s.adjust_level, s.level) in ('HIGH','MID') order by s.total_score desc limit 8"));
        return res;
    }

    // ---------------- 工具 ----------------

    private void requireOwner(LeaveApplication leave, SysUser user) {
        if (!leave.getStudentId().equals(user.getId()) && !"ADMIN".equals(user.getRoleCode())) {
            throw new BizException("该操作仅限本人办理");
        }
    }

    private void requireApprover(LeaveApplication leave, SysUser user) {
        boolean ok = "ADMIN".equals(user.getRoleCode())
                || Objects.equals(leave.getCurrentApproverId(), user.getId())
                || ("DEPT_HEAD".equals(user.getRoleCode()) && Objects.equals(leave.getDeptId(), user.getDeptId()) && DEPT_PENDING.equals(leave.getStatus()));
        if (!ok) {
            throw new BizException("您不是当前节点的审批人");
        }
    }

    private void writeApproval(LeaveApplication leave, String node, SysUser user, String action, String opinion) {
        LeaveApproval a = new LeaveApproval();
        a.setLeaveId(leave.getId());
        a.setNode(node);
        a.setApproverId(user.getId());
        a.setApproverName(user.getRealName());
        a.setAction(action);
        a.setOpinion(opinion);
        approvalMapper.insert(a);
    }

    private void writeLog(SysUser user, String module, String action, String bizNo, String before, String after, String reason) {
        SysLog log = new SysLog();
        log.setUserId(user.getId());
        log.setUserName(user.getRealName());
        log.setModule(module);
        log.setAction(action);
        log.setBizNo(bizNo);
        log.setBeforeStatus(before);
        log.setAfterStatus(after);
        log.setReason(reason);
        log.setIp("127.0.0.1");
        logMapper.insert(log);
    }

    private void pushMessage(Long receiverId, String title, String content, String type, LeaveApplication leave) {
        if (receiverId == null) {
            return;
        }
        SysMessage m = new SysMessage();
        m.setTitle(title);
        m.setContent(content);
        m.setType(type);
        m.setBizNo(leave.getApplyNo());
        m.setBizId(leave.getId());
        m.setReceiverId(receiverId);
        m.setIsRead(0);
        messageMapper.insert(m);
    }

    private String nextApplyNo() {
        String day = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        Integer cnt = jdbc.queryForObject("select count(*) from leave_application where apply_no like ?",
                Integer.class, "QJ" + day + "%");
        return "QJ" + day + String.format("%04d", (cnt == null ? 0 : cnt) + 1);
    }

    public static String statusText(String status) {
        return switch (status == null ? "" : status) {
            case DRAFT -> "草稿";
            case COUNSELOR_PENDING -> "待辅导员审批";
            case DEPT_PENDING -> "待院系审批";
            case ON_LEAVE -> "请假中";
            case RETURN_PENDING -> "待销假";
            case COMPLETED -> "已销假";
            case REJECTED -> "已驳回";
            case CANCELLED -> "已取消";
            default -> status;
        };
    }

    private static int intOf(String v, int def) {
        try {
            return Integer.parseInt(v);
        } catch (Exception e) {
            return def;
        }
    }

    public static boolean hasText(String s) {
        return s != null && !s.isBlank();
    }

    private static String firstText(String a, String b) {
        String v = hasText(a) ? a : b;
        return v == null ? "" : v.trim();
    }

    public static List<String> splitClasses(String className) {
        if (className == null || className.isBlank()) {
            return List.of();
        }
        return Arrays.stream(className.split(",")).map(String::trim).filter(s -> !s.isEmpty()).collect(Collectors.toList());
    }

    private static String quoteList(List<String> list) {
        if (list.isEmpty()) {
            return "''";
        }
        return list.stream().map(s -> "'" + s.replace("'", "") + "'").collect(Collectors.joining(","));
    }
}
