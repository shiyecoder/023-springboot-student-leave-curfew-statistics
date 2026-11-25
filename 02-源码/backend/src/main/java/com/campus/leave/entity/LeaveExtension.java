package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** LeaveExtension 实体，对应表 leave_extension */
@Data
@TableName("leave_extension")
public class LeaveExtension {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long leaveId;
    private LocalDateTime oldEndTime;
    private LocalDateTime newEndTime;
    private BigDecimal addDays;
    private String reason;
    private String status;
    private Long approverId;
    private String approverName;
    private LocalDateTime applyTime;
    private LocalDateTime approveTime;
    private String opinion;
}
