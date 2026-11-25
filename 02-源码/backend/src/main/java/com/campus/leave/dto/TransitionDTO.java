package com.campus.leave.dto;

import lombok.Data;

/** 状态流转参数：action 见 LeaveService.ACTION_*，reason/opinion 用于留痕 */
@Data
public class TransitionDTO {
    private String action;
    private String reason;
    private String opinion;
    /** 乐观锁版本号，前端提交前携带 */
    private Integer version;
}
