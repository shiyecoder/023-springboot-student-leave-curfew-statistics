package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** SysMenu 实体，对应表 sys_menu */
@Data
@TableName("sys_menu")
public class SysMenu {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long parentId;
    private String name;
    private String path;
    private String component;
    private String icon;
    private String perm;
    private String type;
    private Integer sort;
    private Integer visible;
}
