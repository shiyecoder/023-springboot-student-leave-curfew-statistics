package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** SysFile 实体，对应表 sys_file */
@Data
@TableName("sys_file")
public class SysFile {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String fileName;
    private String path;
    private Long size;
    private String contentType;
    private String bizType;
    private Long uploaderId;
    private LocalDateTime createTime;
}
