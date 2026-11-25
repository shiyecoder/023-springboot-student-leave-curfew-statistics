package com.campus.leave.config;

import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateTimeDeserializer;
import com.fasterxml.jackson.datatype.jsr310.ser.LocalDateTimeSerializer;
import org.springframework.boot.autoconfigure.jackson.Jackson2ObjectMapperBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 全局时间格式：出入参统一 yyyy-MM-dd HH:mm:ss，
 * 与前端 el-date-picker 的 value-format 保持一致，避免反序列化失败。
 */
@Configuration
public class JacksonConfig {

    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jacksonCustomizer() {
        return builder -> {
            SimpleModule module = new SimpleModule();
            module.addSerializer(LocalDateTime.class, new LocalDateTimeSerializer(FMT));
            module.addDeserializer(LocalDateTime.class, new LocalDateTimeDeserializer(FMT));
            builder.modules(module);
            builder.simpleDateFormat("yyyy-MM-dd HH:mm:ss");
        };
    }
}
