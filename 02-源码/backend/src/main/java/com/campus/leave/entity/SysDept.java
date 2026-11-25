package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** SysDept 实体，对应表 sys_dept */
@Data
@TableName("sys_dept")
public class SysDept {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String code;
    private Integer sort;
    private LocalDateTime createTime;
}
