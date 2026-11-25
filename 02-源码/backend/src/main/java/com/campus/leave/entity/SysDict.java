package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** SysDict 实体，对应表 sys_dict */
@Data
@TableName("sys_dict")
public class SysDict {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String dictType;
    private String label;
    private String value;
    private Integer sort;
}
