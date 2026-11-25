package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** AbsenceCase 实体，对应表 absence_case */
@Data
@TableName("absence_case")
public class AbsenceCase {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String caseNo;
    private Long studentId;
    private String studentName;
    private Long deptId;
    private String deptName;
    private String className;
    private String caseType;
    private String level;
    private String triggerDesc;
    private String status;
    private Long ownerId;
    private String ownerName;
    private LocalDateTime deadline;
    private LocalDateTime closeTime;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
