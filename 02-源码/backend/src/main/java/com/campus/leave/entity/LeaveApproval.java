package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** LeaveApproval 实体，对应表 leave_approval */
@Data
@TableName("leave_approval")
public class LeaveApproval {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long leaveId;
    private String node;
    private Long approverId;
    private String approverName;
    private String action;
    private String opinion;
    private LocalDateTime createTime;
}
