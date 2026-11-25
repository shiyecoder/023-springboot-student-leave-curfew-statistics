package com.campus.leave.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/** 请假申请提交参数 */
@Data
public class LeaveCreateDTO {
    private Long id;
    private String leaveType;
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private BigDecimal days;
    private String destination;
    private String contactName;
    private String contactPhone;
    private String transport;
    private String reason;
    private String attachmentPath;
    /** true 仅存草稿，false 直接提交审批 */
    private Boolean draft;
    /** 乐观锁版本号，编辑时必带 */
    private Integer version;
}
