package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** SysRole 实体，对应表 sys_role */
@Data
@TableName("sys_role")
public class SysRole {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String code;
    private String name;
    private String dataScope;
    private String remark;
    private LocalDateTime createTime;
}
