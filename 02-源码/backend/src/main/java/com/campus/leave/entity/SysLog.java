package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** SysLog 实体，对应表 sys_log */
@Data
@TableName("sys_log")
public class SysLog {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String userName;
    private String module;
    private String action;
    private String bizNo;
    private String beforeStatus;
    private String afterStatus;
    private String reason;
    private String ip;
    private LocalDateTime createTime;
}
