package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** ReturnRecord 实体，对应表 return_record */
@Data
@TableName("return_record")
public class ReturnRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long leaveId;
    private String applyNo;
    private Long studentId;
    private String studentName;
    private String returnCode;
    private LocalDateTime codeExpire;
    private String verifyType;
    private Long verifierId;
    private String verifierName;
    private LocalDateTime verifyTime;
    private String status;
    private String remark;
    private LocalDateTime createTime;
}
