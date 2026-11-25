package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** SysMessage 实体，对应表 sys_message */
@Data
@TableName("sys_message")
public class SysMessage {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String title;
    private String content;
    private String type;
    private String bizNo;
    private Long bizId;
    private Long receiverId;
    private Integer isRead;
    private LocalDateTime createTime;
}
