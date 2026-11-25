#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""依据表结构生成 MyBatis-Plus 实体与 Mapper（19 张表，避免手写 38 个文件）"""
import pathlib

BASE = pathlib.Path(__file__).parent / "src/main/java/com/campus/leave"
(BASE / "entity").mkdir(parents=True, exist_ok=True)
(BASE / "mapper").mkdir(parents=True, exist_ok=True)

L, S, I, D, T = "Long", "String", "Integer", "BigDecimal", "LocalDateTime"

TABLES = {
    "SysDept": ("sys_dept", [("id", L), ("name", S), ("code", S), ("sort", I), ("createTime", T)]),
    "SysUser": ("sys_user", [("id", L), ("username", S), ("password", S), ("realName", S), ("userNo", S),
                             ("roleCode", S), ("deptId", L), ("deptName", S), ("className", S),
                             ("dormBuilding", S), ("dormRoom", S), ("phone", S), ("guardianName", S),
                             ("guardianPhone", S), ("avatar", S), ("status", I), ("lastLogin", T),
                             ("createTime", T), ("updateTime", T), ("deleted", I)]),
    "SysRole": ("sys_role", [("id", L), ("code", S), ("name", S), ("dataScope", S), ("remark", S), ("createTime", T)]),
    "SysMenu": ("sys_menu", [("id", L), ("parentId", L), ("name", S), ("path", S), ("component", S), ("icon", S),
                             ("perm", S), ("type", S), ("sort", I), ("visible", I)]),
    "SysRoleMenu": ("sys_role_menu", [("id", L), ("roleId", L), ("menuId", L)]),
    "SysMessage": ("sys_message", [("id", L), ("title", S), ("content", S), ("type", S), ("bizNo", S),
                                   ("bizId", L), ("receiverId", L), ("isRead", I), ("createTime", T)]),
    "SysLog": ("sys_log", [("id", L), ("userId", L), ("userName", S), ("module", S), ("action", S), ("bizNo", S),
                           ("beforeStatus", S), ("afterStatus", S), ("reason", S), ("ip", S), ("createTime", T)]),
    "SysFile": ("sys_file", [("id", L), ("fileName", S), ("path", S), ("size", L), ("contentType", S),
                             ("bizType", S), ("uploaderId", L), ("createTime", T)]),
    "SysDict": ("sys_dict", [("id", L), ("dictType", S), ("label", S), ("value", S), ("sort", I)]),
    "LeaveRule": ("leave_rule", [("id", L), ("leaveType", S), ("dayThreshold", D), ("outScope", S),
                                 ("requiredMaterial", S), ("approvalLevel", S), ("enabled", I), ("version", S),
                                 ("effectiveTime", T), ("remark", S)]),
    "LeaveApplication": ("leave_application", [
        ("id", L), ("applyNo", S), ("studentId", L), ("studentName", S), ("deptId", L), ("deptName", S),
        ("className", S), ("leaveType", S), ("startTime", T), ("endTime", T), ("days", D), ("destination", S),
        ("contactName", S), ("contactPhone", S), ("transport", S), ("reason", S), ("attachmentPath", S),
        ("status", S), ("currentApproverId", L), ("currentApproverName", S), ("approvalLevel", S),
        ("needDept", I), ("overdueFlag", I), ("returnDeadline", T), ("riskScore", D), ("riskLevel", S),
        ("cancelReason", S), ("createTime", T), ("updateTime", T), ("deleted", I), ("version", I)]),
    "LeaveApproval": ("leave_approval", [("id", L), ("leaveId", L), ("node", S), ("approverId", L),
                                         ("approverName", S), ("action", S), ("opinion", S), ("createTime", T)]),
    "LeaveExtension": ("leave_extension", [("id", L), ("leaveId", L), ("oldEndTime", T), ("newEndTime", T),
                                           ("addDays", D), ("reason", S), ("status", S), ("approverId", L),
                                           ("approverName", S), ("applyTime", T), ("approveTime", T), ("opinion", S)]),
    "ReturnRecord": ("return_record", [("id", L), ("leaveId", L), ("applyNo", S), ("studentId", L),
                                       ("studentName", S), ("returnCode", S), ("codeExpire", T), ("verifyType", S),
                                       ("verifierId", L), ("verifierName", S), ("verifyTime", T), ("status", S),
                                       ("remark", S), ("createTime", T)]),
    "LateReturn": ("late_return", [("id", L), ("studentId", L), ("studentName", S), ("deptId", L), ("deptName", S),
                                   ("className", S), ("dorm", S), ("returnTime", T), ("reason", S), ("hasLeave", I),
                                   ("leaveId", L), ("isViolation", I), ("remark", S), ("imagePath", S),
                                   ("recorderId", L), ("recorderName", S), ("recordTime", T), ("createTime", T)]),
    "AbsenceCase": ("absence_case", [("id", L), ("caseNo", S), ("studentId", L), ("studentName", S), ("deptId", L),
                                     ("deptName", S), ("className", S), ("caseType", S), ("level", S),
                                     ("triggerDesc", S), ("status", S), ("ownerId", L), ("ownerName", S),
                                     ("deadline", T), ("closeTime", T), ("createTime", T), ("updateTime", T)]),
    "CareRecord": ("care_record", [("id", L), ("caseId", L), ("studentId", L), ("studentName", S), ("careWay", S),
                                    ("content", S), ("result", S), ("recorderId", L), ("recorderName", S),
                                    ("recordTime", T), ("createTime", T)]),
    "RiskRule": ("risk_rule", [("id", L), ("name", S), ("version", S), ("wFreq", D), ("wDays", D), ("wLate", D),
                               ("wOverdue", D), ("wType", D), ("wReject", D), ("lowThreshold", D),
                               ("highThreshold", D), ("enabled", I), ("effectiveTime", T), ("createBy", S),
                               ("createTime", T)]),
    "RiskScore": ("risk_score", [("id", L), ("studentId", L), ("studentName", S), ("className", S),
                                 ("ruleVersion", S), ("snapshot", S), ("detailJson", S), ("totalScore", D),
                                 ("level", S), ("suggest", S), ("adjustLevel", S), ("adjustReason", S),
                                 ("adjustBy", S), ("adjustTime", T), ("calcTime", T)]),
}

for cls, (table, fields) in TABLES.items():
    imports = ["import com.baomidou.mybatisplus.annotation.*;", "import lombok.Data;",
               "import java.time.LocalDateTime;", "import java.math.BigDecimal;"]
    body = []
    for name, typ in fields:
        ann = ""
        if name == "id":
            ann = '    @TableId(type = IdType.AUTO)\n'
        if name == "deleted":
            ann = '    @TableLogic\n'
        if name == "version" and cls == "LeaveApplication":
            ann = '    @Version\n'
        body.append(f"{ann}    private {typ} {name};")
    java = f"""package com.campus.leave.entity;

{chr(10).join(imports)}

/** {cls} 实体，对应表 {table} */
@Data
@TableName("{table}")
public class {cls} {{
{chr(10).join(body)}
}}
"""
    (BASE / "entity" / f"{cls}.java").write_text(java)

    mapper = f"""package com.campus.leave.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.campus.leave.entity.{cls};
import org.apache.ibatis.annotations.Mapper;

/** {cls} 数据访问，通用 CRUD 由 MyBatis-Plus 提供 */
@Mapper
public interface {cls}Mapper extends BaseMapper<{cls}> {{
}}
"""
    (BASE / "mapper" / f"{cls}Mapper.java").write_text(mapper)

print("entities:", len(TABLES))
