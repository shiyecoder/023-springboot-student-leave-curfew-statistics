package com.campus.leave.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.campus.leave.entity.SysFile;
import org.apache.ibatis.annotations.Mapper;

/** SysFile 数据访问，通用 CRUD 由 MyBatis-Plus 提供 */
@Mapper
public interface SysFileMapper extends BaseMapper<SysFile> {
}
