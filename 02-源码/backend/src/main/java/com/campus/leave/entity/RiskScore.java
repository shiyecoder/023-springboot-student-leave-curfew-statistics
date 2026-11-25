package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** RiskScore 实体，对应表 risk_score */
@Data
@TableName("risk_score")
public class RiskScore {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long studentId;
    private String studentName;
    private String className;
    private String ruleVersion;
    private String snapshot;
    private String detailJson;
    private BigDecimal totalScore;
    private String level;
    private String suggest;
    private String adjustLevel;
    private String adjustReason;
    private String adjustBy;
    private LocalDateTime adjustTime;
    private LocalDateTime calcTime;
}
