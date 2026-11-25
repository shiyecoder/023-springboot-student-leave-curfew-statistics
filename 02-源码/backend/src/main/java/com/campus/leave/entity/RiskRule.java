package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** RiskRule 实体，对应表 risk_rule */
@Data
@TableName("risk_rule")
public class RiskRule {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String version;
    private BigDecimal wFreq;
    private BigDecimal wDays;
    private BigDecimal wLate;
    private BigDecimal wOverdue;
    private BigDecimal wType;
    private BigDecimal wReject;
    private BigDecimal lowThreshold;
    private BigDecimal highThreshold;
    private Integer enabled;
    private LocalDateTime effectiveTime;
    private String createBy;
    private LocalDateTime createTime;
}
