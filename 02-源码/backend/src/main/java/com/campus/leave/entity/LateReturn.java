package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** LateReturn 实体，对应表 late_return */
@Data
@TableName("late_return")
public class LateReturn {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long studentId;
    private String studentName;
    private Long deptId;
    private String deptName;
    private String className;
    private String dorm;
    private LocalDateTime returnTime;
    private String reason;
    private Integer hasLeave;
    private Long leaveId;
    private Integer isViolation;
    private String remark;
    private String imagePath;
    private Long recorderId;
    private String recorderName;
    private LocalDateTime recordTime;
    private LocalDateTime createTime;
}
