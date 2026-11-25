package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** CareRecord 实体，对应表 care_record */
@Data
@TableName("care_record")
public class CareRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long caseId;
    private Long studentId;
    private String studentName;
    private String careWay;
    private String content;
    private String result;
    private Long recorderId;
    private String recorderName;
    private LocalDateTime recordTime;
    private LocalDateTime createTime;
}
