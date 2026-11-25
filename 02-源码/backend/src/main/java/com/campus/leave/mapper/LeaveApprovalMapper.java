package com.campus.leave.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.campus.leave.entity.LeaveApproval;
import org.apache.ibatis.annotations.Mapper;

/** LeaveApproval 数据访问，通用 CRUD 由 MyBatis-Plus 提供 */
@Mapper
public interface LeaveApprovalMapper extends BaseMapper<LeaveApproval> {
}
