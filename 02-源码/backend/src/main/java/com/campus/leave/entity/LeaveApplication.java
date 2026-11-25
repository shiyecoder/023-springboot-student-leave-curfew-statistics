package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** LeaveApplication 实体，对应表 leave_application */
@Data
@TableName("leave_application")
public class LeaveApplication {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String applyNo;
    private Long studentId;
    private String studentName;
    private Long deptId;
    private String deptName;
    private String className;
    private String leaveType;
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private BigDecimal days;
    private String destination;
    private String contactName;
    private String contactPhone;
    private String transport;
    private String reason;
    private String attachmentPath;
    private String status;
    private Long currentApproverId;
    private String currentApproverName;
    private String approvalLevel;
    private Integer needDept;
    private Integer overdueFlag;
    private LocalDateTime returnDeadline;
    private BigDecimal riskScore;
    private String riskLevel;
    private String cancelReason;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    @TableLogic
    private Integer deleted;
    @Version
    private Integer version;
}
