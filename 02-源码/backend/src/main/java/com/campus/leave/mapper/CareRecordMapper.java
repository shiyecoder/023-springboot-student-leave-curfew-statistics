package com.campus.leave.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.campus.leave.entity.CareRecord;
import org.apache.ibatis.annotations.Mapper;

/** CareRecord 数据访问，通用 CRUD 由 MyBatis-Plus 提供 */
@Mapper
public interface CareRecordMapper extends BaseMapper<CareRecord> {
}
