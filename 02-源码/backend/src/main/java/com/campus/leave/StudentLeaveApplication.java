package com.campus.leave;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 学生请销假与晚归统计管理系统 启动类
 * 端口 8084（通道 5），数据库 new_023
 */
@SpringBootApplication
@MapperScan("com.campus.leave.mapper")
public class StudentLeaveApplication {
    public static void main(String[] args) {
        SpringApplication.run(StudentLeaveApplication.class, args);
    }
}
