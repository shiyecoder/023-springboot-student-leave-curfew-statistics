package com.campus.leave.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/** SysUser 实体，对应表 sys_user */
@Data
@TableName("sys_user")
public class SysUser {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String username;
    private String password;
    private String realName;
    private String userNo;
    private String roleCode;
    private Long deptId;
    private String deptName;
    private String className;
    private String dormBuilding;
    private String dormRoom;
    private String phone;
    private String guardianName;
    private String guardianPhone;
    private String avatar;
    private Integer status;
    private LocalDateTime lastLogin;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    @TableLogic
    private Integer deleted;
}
