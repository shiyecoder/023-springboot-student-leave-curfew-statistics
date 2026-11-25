package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** LeaveRule 实体，对应表 leave_rule */
@Data
@TableName("leave_rule")
public class LeaveRule {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String leaveType;
    private BigDecimal dayThreshold;
    private String outScope;
    private String requiredMaterial;
    private String approvalLevel;
    private Integer enabled;
    private String version;
    private LocalDateTime effectiveTime;
    private String remark;
}
