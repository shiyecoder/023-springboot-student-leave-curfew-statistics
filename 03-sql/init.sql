-- NEW-023 学生请销假与晚归统计管理系统 · MySQL 8 初始化脚本
-- 生成时间：2026-10-31 · 库名 new_023 · 字符集 utf8mb4
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
DROP DATABASE IF EXISTS new_023;
CREATE DATABASE new_023 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE new_023;

-- ---------- 组织与权限 ----------
CREATE TABLE sys_dept (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  name VARCHAR(64) NOT NULL COMMENT '院系名称',
  code VARCHAR(32) NOT NULL COMMENT '院系编码',
  sort INT DEFAULT 0 COMMENT '排序',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) COMMENT '院系表';

CREATE TABLE sys_user (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  username VARCHAR(50) NOT NULL COMMENT '登录账号（学号/工号）',
  password VARCHAR(100) NOT NULL COMMENT 'BCrypt 密码',
  real_name VARCHAR(50) NOT NULL COMMENT '姓名',
  user_no VARCHAR(50) DEFAULT NULL COMMENT '学号/工号',
  role_code VARCHAR(32) NOT NULL COMMENT '角色编码 STUDENT/COUNSELOR/DEPT_HEAD/DORM/ADMIN',
  dept_id BIGINT DEFAULT NULL COMMENT '院系ID',
  dept_name VARCHAR(64) DEFAULT NULL COMMENT '院系名称（冗余便于列表展示）',
  class_name VARCHAR(64) DEFAULT NULL COMMENT '班级',
  dorm_building VARCHAR(32) DEFAULT NULL COMMENT '宿舍楼',
  dorm_room VARCHAR(32) DEFAULT NULL COMMENT '宿舍号',
  phone VARCHAR(20) DEFAULT NULL COMMENT '联系电话',
  guardian_name VARCHAR(50) DEFAULT NULL COMMENT '紧急联系人',
  guardian_phone VARCHAR(20) DEFAULT NULL COMMENT '紧急联系人电话',
  avatar VARCHAR(200) DEFAULT NULL COMMENT '头像相对路径',
  status TINYINT DEFAULT 1 COMMENT '1启用 0停用',
  last_login DATETIME DEFAULT NULL COMMENT '最近登录',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  deleted TINYINT DEFAULT 0 COMMENT '逻辑删除 0正常 1删除',
  UNIQUE KEY uk_username (username),
  KEY idx_role (role_code),
  KEY idx_class (class_name)
) COMMENT '用户表';

CREATE TABLE sys_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(32) NOT NULL COMMENT '角色编码',
  name VARCHAR(64) NOT NULL COMMENT '角色名称',
  data_scope VARCHAR(32) DEFAULT 'SELF' COMMENT '数据范围 SELF/CLASS/DEPT/ALL',
  remark VARCHAR(200) DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_code (code)
) COMMENT '角色表';

CREATE TABLE sys_menu (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  parent_id BIGINT DEFAULT 0 COMMENT '父级ID，0为根',
  name VARCHAR(64) NOT NULL COMMENT '菜单名称',
  path VARCHAR(120) DEFAULT NULL COMMENT '路由地址',
  component VARCHAR(120) DEFAULT NULL COMMENT '前端组件',
  icon VARCHAR(64) DEFAULT NULL COMMENT '图标',
  perm VARCHAR(100) DEFAULT NULL COMMENT '权限标识',
  type VARCHAR(16) DEFAULT 'MENU' COMMENT 'DIR/MENU/BUTTON',
  sort INT DEFAULT 0,
  visible TINYINT DEFAULT 1 COMMENT '1显示 0隐藏'
) COMMENT '菜单表';

CREATE TABLE sys_role_menu (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  role_id BIGINT NOT NULL,
  menu_id BIGINT NOT NULL,
  UNIQUE KEY uk_role_menu (role_id, menu_id)
) COMMENT '角色菜单关联表';

CREATE TABLE sys_message (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(120) NOT NULL,
  content VARCHAR(500) DEFAULT NULL,
  type VARCHAR(32) DEFAULT 'SYSTEM' COMMENT 'APPROVAL/OVERDUE/CASE/SYSTEM',
  biz_no VARCHAR(50) DEFAULT NULL COMMENT '业务编号',
  biz_id BIGINT DEFAULT NULL COMMENT '业务ID',
  receiver_id BIGINT NOT NULL COMMENT '接收人',
  is_read TINYINT DEFAULT 0,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_receiver (receiver_id, is_read)
) COMMENT '站内消息表';

CREATE TABLE sys_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT DEFAULT NULL,
  user_name VARCHAR(50) DEFAULT NULL,
  module VARCHAR(50) DEFAULT NULL COMMENT '模块',
  action VARCHAR(50) DEFAULT NULL COMMENT '动作',
  biz_no VARCHAR(50) DEFAULT NULL COMMENT '业务编号',
  before_status VARCHAR(32) DEFAULT NULL,
  after_status VARCHAR(32) DEFAULT NULL,
  reason VARCHAR(300) DEFAULT NULL,
  ip VARCHAR(64) DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_biz (biz_no)
) COMMENT '操作日志表';

CREATE TABLE sys_file (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  file_name VARCHAR(200) NOT NULL COMMENT '原始文件名',
  path VARCHAR(300) NOT NULL COMMENT '相对路径 /uploads/xxx',
  size BIGINT DEFAULT 0 COMMENT '字节',
  content_type VARCHAR(100) DEFAULT NULL,
  biz_type VARCHAR(50) DEFAULT NULL COMMENT 'PROOF/AVATAR/LATE',
  uploader_id BIGINT DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) COMMENT '文件表';

CREATE TABLE sys_dict (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  dict_type VARCHAR(50) NOT NULL,
  label VARCHAR(64) NOT NULL,
  value VARCHAR(64) NOT NULL,
  sort INT DEFAULT 0,
  KEY idx_type (dict_type)
) COMMENT '字典表';

-- ---------- 业务主表 ----------
CREATE TABLE leave_rule (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  leave_type VARCHAR(32) NOT NULL COMMENT '请假类型',
  day_threshold DECIMAL(4,1) NOT NULL COMMENT '天数阈值（>= 时升级审批）',
  out_scope VARCHAR(32) DEFAULT 'CITY' COMMENT '外出范围 CITY/PROVINCE/CROSS_PROVINCE',
  required_material VARCHAR(200) DEFAULT NULL COMMENT '必需材料说明',
  approval_level VARCHAR(64) NOT NULL COMMENT '审批层级 COUNSELOR / COUNSELOR,DEPT',
  enabled TINYINT DEFAULT 1,
  version VARCHAR(16) DEFAULT 'v3',
  effective_time DATETIME DEFAULT NULL,
  remark VARCHAR(200) DEFAULT NULL
) COMMENT '请假审批规则表';

CREATE TABLE leave_application (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  apply_no VARCHAR(50) NOT NULL COMMENT '申请编号，后端生成',
  student_id BIGINT NOT NULL COMMENT '学生ID',
  student_name VARCHAR(50) NOT NULL COMMENT '学生姓名',
  dept_id BIGINT DEFAULT NULL,
  dept_name VARCHAR(64) DEFAULT NULL,
  class_name VARCHAR(64) DEFAULT NULL,
  leave_type VARCHAR(32) NOT NULL COMMENT '病假/事假/公假/实习/跨省外出',
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  days DECIMAL(5,1) NOT NULL COMMENT '请假天数（后端按小时折算）',
  destination VARCHAR(100) DEFAULT NULL COMMENT '外出地点',
  contact_name VARCHAR(100) DEFAULT NULL COMMENT '紧急联系人',
  contact_phone VARCHAR(20) DEFAULT NULL,
  transport VARCHAR(32) DEFAULT NULL COMMENT '交通方式',
  reason VARCHAR(500) DEFAULT NULL COMMENT '请假事由',
  attachment_path VARCHAR(300) DEFAULT NULL COMMENT '证明附件相对路径',
  status VARCHAR(32) NOT NULL DEFAULT 'DRAFT' COMMENT 'DRAFT/COUNSELOR_PENDING/DEPT_PENDING/ON_LEAVE/RETURN_PENDING/COMPLETED/REJECTED/CANCELLED/OVERDUE',
  current_approver_id BIGINT DEFAULT NULL,
  current_approver_name VARCHAR(50) DEFAULT NULL,
  approval_level VARCHAR(64) DEFAULT NULL COMMENT '命中的审批层级',
  need_dept TINYINT DEFAULT 0,
  overdue_flag TINYINT DEFAULT 0 COMMENT '1 已超期未销假',
  return_deadline DATETIME DEFAULT NULL COMMENT '应销假截止时间',
  risk_score DECIMAL(5,1) DEFAULT NULL COMMENT '风险总分快照',
  risk_level VARCHAR(16) DEFAULT NULL COMMENT 'LOW/MID/HIGH',
  cancel_reason VARCHAR(300) DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted TINYINT DEFAULT 0,
  version INT DEFAULT 0 COMMENT '乐观锁版本号',
  UNIQUE KEY uk_apply_no (apply_no),
  KEY idx_student (student_id),
  KEY idx_status (status),
  KEY idx_create (create_time)
) COMMENT '学生请假申请主表';

CREATE TABLE leave_approval (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  leave_id BIGINT NOT NULL,
  node VARCHAR(32) NOT NULL COMMENT 'COUNSELOR/DEPT',
  approver_id BIGINT DEFAULT NULL,
  approver_name VARCHAR(50) DEFAULT NULL,
  action VARCHAR(16) NOT NULL COMMENT 'APPROVE/REJECT/RETURN',
  opinion VARCHAR(300) DEFAULT NULL COMMENT '审批意见，驳回必填',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_leave (leave_id)
) COMMENT '审批记录表';

CREATE TABLE leave_extension (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  leave_id BIGINT NOT NULL,
  old_end_time DATETIME NOT NULL,
  new_end_time DATETIME NOT NULL,
  add_days DECIMAL(5,1) NOT NULL,
  reason VARCHAR(300) NOT NULL,
  status VARCHAR(32) DEFAULT 'PENDING' COMMENT 'PENDING/APPROVED/REJECTED',
  approver_id BIGINT DEFAULT NULL,
  approver_name VARCHAR(50) DEFAULT NULL,
  apply_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  approve_time DATETIME DEFAULT NULL,
  opinion VARCHAR(300) DEFAULT NULL,
  KEY idx_leave (leave_id)
) COMMENT '延期申请表';

CREATE TABLE return_record (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  leave_id BIGINT NOT NULL,
  apply_no VARCHAR(50) DEFAULT NULL,
  student_id BIGINT DEFAULT NULL,
  student_name VARCHAR(50) DEFAULT NULL,
  return_code VARCHAR(16) DEFAULT NULL COMMENT '6位限时返校码',
  code_expire DATETIME DEFAULT NULL COMMENT '码过期时间',
  verify_type VARCHAR(16) DEFAULT NULL COMMENT 'CODE/MANUAL',
  verifier_id BIGINT DEFAULT NULL,
  verifier_name VARCHAR(50) DEFAULT NULL,
  verify_time DATETIME DEFAULT NULL,
  status VARCHAR(32) DEFAULT 'PENDING' COMMENT 'PENDING/VERIFIED/EXPIRED',
  remark VARCHAR(300) DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_leave (leave_id),
  KEY idx_code (return_code)
) COMMENT '返校销假记录表';

CREATE TABLE late_return (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  student_id BIGINT NOT NULL,
  student_name VARCHAR(50) NOT NULL,
  dept_id BIGINT DEFAULT NULL,
  dept_name VARCHAR(64) DEFAULT NULL,
  class_name VARCHAR(64) DEFAULT NULL,
  dorm VARCHAR(50) DEFAULT NULL COMMENT '宿舍 楼栋-房间',
  return_time DATETIME NOT NULL COMMENT '返寝时间',
  reason VARCHAR(100) DEFAULT NULL,
  has_leave TINYINT DEFAULT 0 COMMENT '1 有有效请假',
  leave_id BIGINT DEFAULT NULL,
  is_violation TINYINT DEFAULT 1 COMMENT '1 违规晚归',
  remark VARCHAR(300) DEFAULT NULL COMMENT '现场说明',
  image_path VARCHAR(300) DEFAULT NULL COMMENT '现场照片',
  recorder_id BIGINT DEFAULT NULL,
  recorder_name VARCHAR(50) DEFAULT NULL,
  record_time DATETIME DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_student (student_id),
  KEY idx_time (return_time)
) COMMENT '晚归登记表';

CREATE TABLE absence_case (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  case_no VARCHAR(50) NOT NULL COMMENT '工单编号',
  student_id BIGINT NOT NULL,
  student_name VARCHAR(50) NOT NULL,
  dept_id BIGINT DEFAULT NULL,
  dept_name VARCHAR(64) DEFAULT NULL,
  class_name VARCHAR(64) DEFAULT NULL,
  case_type VARCHAR(32) NOT NULL COMMENT 'OVERDUE/NIGHT_ABSENT/REPEAT_LATE',
  level VARCHAR(16) DEFAULT 'MID' COMMENT 'LOW/MID/HIGH',
  trigger_desc VARCHAR(300) DEFAULT NULL COMMENT '触发依据',
  status VARCHAR(32) DEFAULT 'PENDING' COMMENT 'PENDING/PROCESSING/CLOSED',
  owner_id BIGINT DEFAULT NULL,
  owner_name VARCHAR(50) DEFAULT NULL,
  deadline DATETIME DEFAULT NULL,
  close_time DATETIME DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_case_no (case_no),
  KEY idx_status (status)
) COMMENT '未归核查工单表';

CREATE TABLE care_record (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  case_id BIGINT DEFAULT NULL,
  student_id BIGINT DEFAULT NULL,
  student_name VARCHAR(50) DEFAULT NULL,
  care_way VARCHAR(32) DEFAULT NULL COMMENT 'PHONE/PARENT/VISIT/PEER',
  content VARCHAR(500) DEFAULT NULL COMMENT '学生情况',
  result VARCHAR(500) DEFAULT NULL COMMENT '后续处置',
  recorder_id BIGINT DEFAULT NULL,
  recorder_name VARCHAR(50) DEFAULT NULL,
  record_time DATETIME DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_case (case_id)
) COMMENT '关怀记录表';

-- ---------- 创新点：请假行为风险分层 ----------
CREATE TABLE risk_rule (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(64) DEFAULT '请假行为风险分层规则',
  version VARCHAR(16) NOT NULL,
  w_freq DECIMAL(5,2) NOT NULL COMMENT '近30天请假次数权重(%)',
  w_days DECIMAL(5,2) NOT NULL COMMENT '累计天数权重(%)',
  w_late DECIMAL(5,2) NOT NULL COMMENT '晚归次数权重(%)',
  w_overdue DECIMAL(5,2) NOT NULL COMMENT '逾期销假次数权重(%)',
  w_type DECIMAL(5,2) NOT NULL COMMENT '请假类型权重(%)',
  w_reject DECIMAL(5,2) NOT NULL COMMENT '审批驳回次数权重(%)',
  low_threshold DECIMAL(5,1) DEFAULT 40 COMMENT '低关注上限',
  high_threshold DECIMAL(5,1) DEFAULT 70 COMMENT '中关注上限',
  enabled TINYINT DEFAULT 1,
  effective_time DATETIME DEFAULT NULL,
  create_by VARCHAR(50) DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_version (version)
) COMMENT '风险分层规则表（权重合计必须=100）';

CREATE TABLE risk_score (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  student_id BIGINT NOT NULL,
  student_name VARCHAR(50) DEFAULT NULL,
  class_name VARCHAR(64) DEFAULT NULL,
  rule_version VARCHAR(16) DEFAULT NULL,
  snapshot VARCHAR(1000) DEFAULT NULL COMMENT '输入快照 JSON',
  detail_json VARCHAR(2000) DEFAULT NULL COMMENT '各项得分 JSON',
  total_score DECIMAL(5,1) DEFAULT NULL,
  level VARCHAR(16) DEFAULT NULL COMMENT 'LOW/MID/HIGH',
  suggest VARCHAR(500) DEFAULT NULL COMMENT '结果解释与改进建议',
  adjust_level VARCHAR(16) DEFAULT NULL COMMENT '人工调整后等级',
  adjust_reason VARCHAR(300) DEFAULT NULL,
  adjust_by VARCHAR(50) DEFAULT NULL,
  adjust_time DATETIME DEFAULT NULL,
  calc_time DATETIME DEFAULT NULL,
  KEY idx_student (student_id)
) COMMENT '风险计算结果表（保留输入快照与规则版本）';;

-- ========== 基础数据 ==========
INSERT INTO sys_dept (id,name,code,sort,create_time) VALUES (1,'计算机学院','CS',1,'2026-01-05 09:00:00'),(2,'电子信息学院','EE',2,'2026-01-05 09:00:00'),(3,'外国语学院','FL',3,'2026-01-05 09:00:00'),(4,'机械工程学院','ME',4,'2026-01-05 09:00:00'),(5,'学生工作处','SW',5,'2026-01-05 09:00:00');

INSERT INTO sys_role (id,code,name,data_scope,remark,create_time) VALUES
(1,'STUDENT','学生','SELF','仅本人数据','2026-01-05 09:10:00'),
(2,'COUNSELOR','辅导员 / 班主任','CLASS','所带班级','2026-01-05 09:10:00'),
(3,'DEPT_HEAD','院系学工负责人','DEPT','本院系/本楼栋','2026-01-05 09:10:00'),
(4,'DORM','宿管值班员','DEPT','本院系/本楼栋','2026-01-05 09:10:00'),
(5,'ADMIN','系统管理员','ALL','全校','2026-01-05 09:10:00');

INSERT INTO sys_menu (id,parent_id,name,path,component,icon,perm,type,sort,visible) VALUES
(1,0,'工作台','/dashboard','Dashboard','i-dashboard','dashboard:view','MENU',1,1),
(2,0,'请假管理','/leave','Layout','i-list','leave:view','DIR',2,1),
(3,2,'我的请假','/leave/list','leave/LeaveList','i-list','leave:list','MENU',1,1),
(4,2,'发起请假','/leave/create','leave/LeaveForm','i-plus','leave:add','MENU',2,1),
(5,2,'返校销假','/leave/return','leave/ReturnVerify','i-check','leave:return','MENU',3,1),
(6,0,'审批中心','/approval','Layout','i-shield','approval:view','DIR',3,1),
(7,6,'审批工作台','/approval/desk','approval/ApprovalDesk','i-shield','approval:desk','MENU',1,1),
(8,6,'批量审批','/approval/batch','','i-check','approval:batch','BUTTON',2,0),
(9,6,'院系审批','/approval/dept','approval/DeptApprove','i-shield','approval:dept','MENU',3,1),
(10,0,'安全管理','/safety','Layout','i-alert','safety:view','DIR',4,1),
(11,10,'晚归登记','/safety/late','safety/LateRegister','i-clock','late:list','MENU',1,1),
(12,10,'未归核查','/safety/cases','safety/CaseList','i-alert','case:list','MENU',2,1),
(13,10,'关怀记录','/safety/care','safety/CareList','i-note','care:list','MENU',3,1),
(14,0,'统计分析','/stats','Stats','i-chart','stats:view','MENU',5,1),
(15,0,'小学工','/','','i-users','','DIR',9,0),
(16,0,'规则配置','/admin/rules','admin/RuleConfig','i-settings','rule:config','MENU',6,1),
(17,0,'用户管理','/admin/users','admin/UserList','i-users','user:list','MENU',7,1),
(18,0,'角色管理','/admin/roles','admin/RoleList','i-shield','role:list','MENU',8,1),
(19,0,'菜单管理','/admin/menus','admin/MenuList','i-list','menu:list','MENU',9,1),
(20,0,'个人中心','/profile','Profile','i-avatar','profile:view','MENU',10,0),
(21,12,'关闭工单','/','','i-check','case:close','BUTTON',1,0),
(22,11,'新增晚归','/','','i-plus','late:add','BUTTON',1,0);

INSERT INTO sys_role_menu (id,role_id,menu_id) VALUES (1,1,1),(2,1,2),(3,1,3),(4,1,4),(5,1,5),(6,1,20),(7,2,1),(8,2,2),(9,2,3),(10,2,6),(11,2,7),(12,2,8),(13,2,10),(14,2,12),(15,2,13),(16,2,14),(17,2,20),(18,2,21),(19,3,1),(20,3,2),(21,3,3),(22,3,6),(23,3,7),(24,3,9),(25,3,10),(26,3,12),(27,3,13),(28,3,14),(29,3,20),(30,4,1),(31,4,5),(32,4,10),(33,4,11),(34,4,12),(35,4,13),(36,4,20),(37,4,22),(38,5,1),(39,5,2),(40,5,3),(41,5,6),(42,5,7),(43,5,9),(44,5,10),(45,5,11),(46,5,12),(47,5,13),(48,5,14),(49,5,16),(50,5,17),(51,5,18),(52,5,19),(53,5,20),(54,5,8),(55,5,21),(56,5,22);

INSERT INTO sys_dict (dict_type,label,value,sort) VALUES
('leave_type','病假','1',1),
('leave_type','事假','2',2),
('leave_type','公假','3',3),
('leave_type','实习','4',4),
('leave_type','跨省外出','5',5),
('leave_status','草稿','1',1),
('leave_status','待辅导员审批','2',2),
('leave_status','待院系审批','3',3),
('leave_status','请假中','4',4),
('leave_status','待销假','5',5),
('leave_status','已销假','6',6),
('leave_status','已驳回','7',7),
('leave_status','已取消','8',8),
('leave_status','超期未销假','9',9),
('transport','地铁','1',1),
('transport','公交','2',2),
('transport','高铁','3',3),
('transport','飞机','4',4),
('transport','私家车','5',5),
('transport','步行','6',6),
('late_reason','实习加班','1',1),
('late_reason','交通延误','2',2),
('late_reason','就医','3',3),
('late_reason','其他','4',4),
('case_type','超期未销假','1',1),
('case_type','夜不归','2',2),
('case_type','连续晚归','3',3);

-- 密码统一为 123456（BCrypt），管理员 admin/admin123 单独一条
INSERT INTO sys_user (id,username,password,real_name,user_no,role_code,dept_id,dept_name,class_name,dorm_building,dorm_room,phone,guardian_name,guardian_phone,avatar,status,last_login) VALUES
(1,'admin','$2b$10$1YWyXmTdMpFRTGvnSZKXp.zMkHkkpV48rF9az6tRunrhrCNU5uTUy','系统管理员','A0001','ADMIN',5,'学生工作处','-','-','-','13800000001','-','-','/uploads/seed/avatar/03.jpg',1,'2026-10-31 19:02:00'),
(2,'t1001','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','陈立','T1001','COUNSELOR',1,'计算机学院','软件工程 2201,软件工程 2202','-','-','13900002201','-','-','/uploads/seed/avatar/05.jpg',1,'2026-10-31 18:20:00'),
(3,'t1002','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','赵敏','T1002','COUNSELOR',1,'计算机学院','软件工程 2203,计算机科学 2201','-','-','13900002202','-','-','/uploads/seed/avatar/07.jpg',1,'2026-10-31 18:20:00'),
(4,'t2001','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','王志远','T2001','DEPT_HEAD',1,'计算机学院','-','-','-','13900003302','-','-','/uploads/seed/avatar/03.jpg',1,'2026-10-31 18:20:00'),
(5,'d3001','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','刘梅','D3001','DORM',5,'学生工作处','6 栋','6 栋','101','13700008801','-','-','/uploads/seed/avatar/04.jpg',1,'2026-10-31 18:20:00'),
(100,'s2022001','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','张若曦','S2022001','STUDENT',1,'计算机学院','软件工程 2201','6 栋','6-400','1380000010','家长','139****0100','/uploads/seed/avatar/01.jpg',1,'2026-10-30 21:10:00'),
(101,'s2022002','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','李昊然','S2022002','STUDENT',1,'计算机学院','软件工程 2202','6 栋','6-401','1380000010','家长','139****0101','/uploads/seed/avatar/02.jpg',1,'2026-10-30 21:10:00'),
(102,'s2022003','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','周文琪','S2022003','STUDENT',1,'计算机学院','软件工程 2203','6 栋','6-402','1380000010','家长','139****0102','/uploads/seed/avatar/03.jpg',1,'2026-10-30 21:10:00'),
(103,'s2022004','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','赵一鸣','S2022004','STUDENT',1,'计算机学院','计算机科学 2201','6 栋','6-403','1380000010','家长','139****0103','/uploads/seed/avatar/04.jpg',1,'2026-10-30 21:10:00'),
(104,'s2022005','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','孙可','S2022005','STUDENT',1,'计算机学院','软件工程 2201','6 栋','6-404','1380000010','家长','139****0104','/uploads/seed/avatar/05.jpg',1,'2026-10-30 21:10:00'),
(105,'s2022006','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','陈思远','S2022006','STUDENT',1,'计算机学院','软件工程 2202','6 栋','6-405','1380000010','家长','139****0105','/uploads/seed/avatar/06.jpg',1,'2026-10-30 21:10:00'),
(106,'s2022007','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','王梓萱','S2022007','STUDENT',1,'计算机学院','软件工程 2203','6 栋','6-406','1380000010','家长','139****0106','/uploads/seed/avatar/07.jpg',1,'2026-10-30 21:10:00'),
(107,'s2022008','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','刘子豪','S2022008','STUDENT',1,'计算机学院','计算机科学 2201','6 栋','6-407','1380000010','家长','139****0107','/uploads/seed/avatar/08.jpg',1,'2026-10-30 21:10:00'),
(108,'s2022009','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','吴桐','S2022009','STUDENT',1,'计算机学院','软件工程 2201','6 栋','6-408','1380000010','家长','139****0108','/uploads/seed/avatar/01.jpg',1,'2026-10-30 21:10:00'),
(109,'s2022010','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','郑雨桐','S2022010','STUDENT',1,'计算机学院','软件工程 2202','6 栋','6-409','1380000010','家长','139****0109','/uploads/seed/avatar/02.jpg',1,'2026-10-30 21:10:00'),
(110,'s2022011','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','林知远','S2022011','STUDENT',1,'计算机学院','软件工程 2203','6 栋','6-410','1380000011','家长','139****0110','/uploads/seed/avatar/03.jpg',1,'2026-10-30 21:10:00'),
(111,'s2022012','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','徐若彤','S2022012','STUDENT',1,'计算机学院','计算机科学 2201','6 栋','6-411','1380000011','家长','139****0111','/uploads/seed/avatar/04.jpg',1,'2026-10-30 21:10:00'),
(112,'s2022013','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','何嘉树','S2022013','STUDENT',1,'计算机学院','软件工程 2201','6 栋','6-412','1380000011','家长','139****0112','/uploads/seed/avatar/05.jpg',1,'2026-10-30 21:10:00'),
(113,'s2022014','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','曹雨晴','S2022014','STUDENT',1,'计算机学院','软件工程 2202','6 栋','6-413','1380000011','家长','139****0113','/uploads/seed/avatar/06.jpg',1,'2026-10-30 21:10:00'),
(114,'s2022015','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','谢明轩','S2022015','STUDENT',1,'计算机学院','软件工程 2203','6 栋','6-414','1380000011','家长','139****0114','/uploads/seed/avatar/07.jpg',1,'2026-10-30 21:10:00'),
(115,'s2022016','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','韩思彤','S2022016','STUDENT',1,'计算机学院','计算机科学 2201','6 栋','6-415','1380000011','家长','139****0115','/uploads/seed/avatar/08.jpg',1,'2026-10-30 21:10:00'),
(116,'s2022017','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','朱一诺','S2022017','STUDENT',1,'计算机学院','软件工程 2201','6 栋','6-416','1380000011','家长','139****0116','/uploads/seed/avatar/01.jpg',1,'2026-10-30 21:10:00'),
(117,'s2022018','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','沈亦辰','S2022018','STUDENT',1,'计算机学院','软件工程 2202','6 栋','6-417','1380000011','家长','139****0117','/uploads/seed/avatar/02.jpg',1,'2026-10-30 21:10:00'),
(118,'s2022019','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','唐婉清','S2022019','STUDENT',1,'计算机学院','软件工程 2203','6 栋','6-418','1380000011','家长','139****0118','/uploads/seed/avatar/03.jpg',1,'2026-10-30 21:10:00'),
(119,'s2022020','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','冯子墨','S2022020','STUDENT',1,'计算机学院','计算机科学 2201','6 栋','6-419','1380000011','家长','139****0119','/uploads/seed/avatar/04.jpg',1,'2026-10-30 21:10:00'),
(120,'s2022021','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','邓佳怡','S2022021','STUDENT',1,'计算机学院','软件工程 2201','6 栋','6-420','1380000012','家长','139****0120','/uploads/seed/avatar/05.jpg',1,'2026-10-30 21:10:00'),
(121,'s2022022','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','许诺','S2022022','STUDENT',1,'计算机学院','软件工程 2202','6 栋','6-421','1380000012','家长','139****0121','/uploads/seed/avatar/06.jpg',1,'2026-10-30 21:10:00'),
(122,'s2022023','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','蒋文博','S2022023','STUDENT',1,'计算机学院','软件工程 2203','6 栋','6-422','1380000012','家长','139****0122','/uploads/seed/avatar/07.jpg',1,'2026-10-30 21:10:00'),
(123,'s2022024','$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi','黄雅静','S2022024','STUDENT',1,'计算机学院','计算机科学 2201','6 栋','6-423','1380000012','家长','139****0123','/uploads/seed/avatar/08.jpg',1,'2026-10-30 21:10:00');

INSERT INTO leave_rule (id,leave_type,day_threshold,out_scope,required_material,approval_level,enabled,version,effective_time,remark) VALUES
(1,'病假',2.0,'CITY','诊断证明','COUNSELOR',1,'v3','2026-09-01 00:00:00','病假 2 天以内仅辅导员审批'),
(2,'病假',2.0,'CITY','诊断证明 + 病历','COUNSELOR,DEPT',1,'v3','2026-09-01 00:00:00','病假超过 2 天需追加院系审批'),
(3,'事假',1.0,'CITY','无','COUNSELOR',1,'v3','2026-09-01 00:00:00','事假 1 天以内辅导员审批'),
(4,'事假',1.0,'CITY','家长确认','COUNSELOR,DEPT',1,'v3','2026-09-01 00:00:00','事假超过 1 天需院系审批'),
(5,'公假',0.0,'PROVINCE','活动通知','COUNSELOR,DEPT',1,'v3','2026-09-01 00:00:00','公假一律院系审批'),
(6,'跨省外出',0.0,'CROSS_PROVINCE','家长确认 + 行程单','COUNSELOR,DEPT',1,'v3','2026-09-01 00:00:00','跨省外出必须院系审批'),
(7,'实习',7.0,'CITY','实习协议','COUNSELOR,DEPT',1,'v3','2026-09-01 00:00:00','实习超过 7 天院系审批');

INSERT INTO leave_application (id,apply_no,student_id,student_name,dept_id,dept_name,class_name,leave_type,start_time,end_time,days,destination,contact_name,contact_phone,transport,reason,attachment_path,status,current_approver_id,current_approver_name,approval_level,need_dept,overdue_flag,return_deadline,risk_score,risk_level,create_time,update_time,deleted,version) VALUES
(1,'QJ202605030001',100,'张若曦',1,'计算机学院','软件工程 2201','病假','2026-11-01 14:00:00','2026-11-01 19:00:00',0.5,'市第一人民医院 · 城东院区','家长 / 辅导员','138****0001','地铁','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/01.jpg','ON_LEAVE',2,'陈立','COUNSELOR',0,0,'2026-11-01 21:00:00',25.0,'LOW','2026-11-01 08:00:00','2026-11-01 14:00:00',0,1),
(2,'QJ202606060002',101,'李昊然',1,'计算机学院','软件工程 2202','事假','2026-11-01 20:00:00','2026-11-02 06:00:00',1.0,'邻市 · 家中','家长 / 辅导员','138****0002','高铁','家中有事需回处理，已与家长沟通。','/uploads/seed/proof/02.jpg','COUNSELOR_PENDING',2,'陈立','COUNSELOR',0,0,'2026-11-02 08:00:00',35.0,'LOW','2026-11-01 13:00:00','2026-11-01 20:00:00',0,2),
(3,'QJ202607090003',102,'周文琪',1,'计算机学院','软件工程 2203','公假','2026-07-09 08:00:00','2026-07-09 23:00:00',1.5,'市会展中心','家长 / 辅导员','138****0003','私家车','代表学院参加比赛/活动，附活动通知。','/uploads/seed/proof/03.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-07-10 01:00:00',45.0,'MID','2026-07-09 00:00:00','2026-07-09 08:00:00',0,0),
(4,'QJ202608120004',103,'赵一鸣',1,'计算机学院','计算机科学 2201','实习','2026-11-01 22:00:00','2026-11-02 18:00:00',2.0,'滨江区 · 校企合作基地','家长 / 辅导员','138****0004','公交','参加校企合作实习，需连续在岗。','/uploads/seed/proof/04.jpg','DEPT_PENDING',4,'王志远','COUNSELOR,DEPT',1,0,'2026-11-02 20:00:00',55.0,'MID','2026-11-01 13:00:00','2026-11-01 22:00:00',0,1),
(5,'QJ202609150005',104,'孙可',1,'计算机学院','软件工程 2201','跨省外出','2026-10-30 12:30:00','2026-10-31 18:30:00',3.0,'江苏省南京市','家长 / 辅导员','138****0005','飞机','家在外省，需返乡处理家庭事务。','/uploads/seed/proof/05.jpg','RETURN_PENDING',2,'陈立','COUNSELOR,DEPT',1,0,'2026-10-31 20:30:00',68.0,'MID','2026-10-30 02:30:00','2026-10-30 12:30:00',0,2),
(6,'QJ202610180006',105,'陈思远',1,'计算机学院','软件工程 2202','病假','2026-10-18 13:00:00','2026-10-20 05:00:00',4.0,'市口腔医院','家长 / 辅导员','138****0006','地铁','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/06.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-10-20 07:00:00',46.0,'MID','2026-10-18 02:00:00','2026-10-18 13:00:00',0,0),
(7,'QJ202605210007',106,'王梓萱',1,'计算机学院','软件工程 2203','事假','2026-05-21 08:00:00','2026-05-23 10:00:00',5.0,'市区 · 办证中心','家长 / 辅导员','138****0007','高铁','家中有事需回处理，已与家长沟通。','/uploads/seed/proof/01.jpg','REJECTED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-05-23 12:00:00',59.0,'MID','2026-05-20 20:00:00','2026-05-21 08:00:00',0,1),
(8,'QJ202606240008',107,'刘子豪',1,'计算机学院','计算机科学 2201','病假','2026-10-30 11:00:00','2026-11-02 19:00:00',8.0,'省人民医院','家长 / 辅导员','138****0008','私家车','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/02.jpg','ON_LEAVE',2,'陈立','COUNSELOR,DEPT',1,1,'2026-11-02 21:00:00',84.0,'HIGH','2026-10-29 22:00:00','2026-10-30 11:00:00',0,2),
(9,'QJ202607270009',108,'吴桐',1,'计算机学院','软件工程 2201','实习','2026-07-27 08:00:00','2026-07-27 13:00:00',0.5,'上海 · 实习企业','家长 / 辅导员','138****0009','公交','参加校企合作实习，需连续在岗。','/uploads/seed/proof/03.jpg','REJECTED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-07-27 15:00:00',46.0,'MID','2026-07-26 18:00:00','2026-07-27 08:00:00',0,0),
(10,'QJ202608050010',101,'李昊然',1,'计算机学院','软件工程 2202','跨省外出','2026-11-01 22:00:00','2026-11-02 08:00:00',1.0,'上海浦东新区','家长 / 辅导员','138****0010','飞机','家在外省，需返乡处理家庭事务。','/uploads/seed/proof/04.jpg','COUNSELOR_PENDING',2,'陈立','COUNSELOR,DEPT',1,0,'2026-11-02 10:00:00',56.0,'MID','2026-11-01 07:00:00','2026-11-01 22:00:00',0,1),
(11,'QJ202609080011',102,'周文琪',1,'计算机学院','软件工程 2203','病假','2026-11-01 23:00:00','2026-11-02 14:00:00',1.5,'校医院转诊 · 市中心医院','家长 / 辅导员','138****0011','地铁','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/05.jpg','DEPT_PENDING',4,'王志远','COUNSELOR',0,0,'2026-11-02 16:00:00',31.0,'LOW','2026-11-01 07:00:00','2026-11-01 23:00:00',0,2),
(12,'QJ202610110012',103,'赵一鸣',1,'计算机学院','计算机科学 2201','事假','2026-11-02 00:00:00','2026-11-02 20:00:00',2.0,'家中（本市）','家长 / 辅导员','138****0012','高铁','家中有事需回处理，已与家长沟通。','/uploads/seed/proof/06.jpg','COUNSELOR_PENDING',2,'陈立','COUNSELOR',0,0,'2026-11-02 22:00:00',41.0,'MID','2026-11-01 07:00:00','2026-11-02 00:00:00',0,0),
(13,'QJ202605140013',112,'何嘉树',1,'计算机学院','软件工程 2201','公假','2026-05-14 08:00:00','2026-05-15 14:00:00',3.0,'省体育中心','家长 / 辅导员','138****0013','私家车','代表学院参加比赛/活动，附活动通知。','/uploads/seed/proof/01.jpg','CANCELLED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-05-15 16:00:00',54.0,'MID','2026-05-14 02:00:00','2026-05-14 20:00:00',0,1),
(14,'QJ202606170014',101,'李昊然',1,'计算机学院','软件工程 2202','实习','2026-11-01 20:00:00','2026-11-03 12:00:00',4.0,'市高新区 · 实习单位','家长 / 辅导员','138****0014','公交','参加校企合作实习，需连续在岗。','/uploads/seed/proof/02.jpg','DEPT_PENDING',4,'王志远','COUNSELOR,DEPT',1,0,'2026-11-03 14:00:00',67.0,'MID','2026-11-01 13:00:00','2026-11-02 08:00:00',0,2),
(15,'QJ202607200015',114,'谢明轩',1,'计算机学院','软件工程 2203','病假','2026-07-20 08:00:00','2026-07-22 10:00:00',5.0,'校医院转诊 · 市中心医院','家长 / 辅导员','138****0015','飞机','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/03.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-07-22 12:00:00',80.0,'HIGH','2026-07-20 00:00:00','2026-07-20 20:00:00',0,0),
(16,'QJ202608230016',115,'韩思彤',1,'计算机学院','计算机科学 2201','病假','2026-08-23 13:00:00','2026-08-26 21:00:00',8.0,'省人民医院','家长 / 辅导员','138****0016','地铁','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/04.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-08-26 23:00:00',70.0,'HIGH','2026-08-23 04:00:00','2026-08-24 01:00:00',0,1),
(17,'QJ202609260017',116,'朱一诺',1,'计算机学院','软件工程 2201','事假','2026-10-31 13:30:00','2026-10-31 18:30:00',0.5,'校本部 · 市区','家长 / 辅导员','138****0017','高铁','家中有事需回处理，已与家长沟通。','/uploads/seed/proof/05.jpg','RETURN_PENDING',2,'陈立','COUNSELOR',0,0,'2026-10-31 20:30:00',32.0,'LOW','2026-10-31 03:30:00','2026-11-01 01:30:00',0,2),
(18,'QJ202610040018',101,'李昊然',1,'计算机学院','软件工程 2202','公假','2026-11-02 00:00:00','2026-11-02 10:00:00',1.0,'省大学生运动会','家长 / 辅导员','138****0018','私家车','代表学院参加比赛/活动，附活动通知。','/uploads/seed/proof/06.jpg','COUNSELOR_PENDING',2,'陈立','COUNSELOR,DEPT',1,0,'2026-11-02 12:00:00',42.0,'MID','2026-11-01 13:00:00','2026-11-02 12:00:00',0,0),
(19,'QJ202605070019',118,'唐婉清',1,'计算机学院','软件工程 2203','实习','2026-05-07 08:00:00','2026-05-07 23:00:00',1.5,'滨江区 · 校企合作基地','家长 / 辅导员','138****0019','公交','参加校企合作实习，需连续在岗。','/uploads/seed/proof/01.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-05-08 01:00:00',52.0,'MID','2026-05-06 20:00:00','2026-05-07 20:00:00',0,1),
(20,'QJ202606100020',119,'冯子墨',1,'计算机学院','计算机科学 2201','跨省外出','2026-11-01 23:00:00','2026-11-02 19:00:00',2.0,'山东省济南市','家长 / 辅导员','138****0020','飞机','家在外省，需返乡处理家庭事务。','/uploads/seed/proof/02.jpg','ON_LEAVE',2,'陈立','COUNSELOR,DEPT',1,1,'2026-11-02 21:00:00',62.0,'MID','2026-11-01 10:00:00','2026-11-01 15:00:00',0,2),
(21,'QJ202607130021',120,'邓佳怡',1,'计算机学院','软件工程 2201','病假','2026-11-02 13:00:00','2026-11-03 19:00:00',3.0,'市第一人民医院 · 城东院区','家长 / 辅导员','138****0021','地铁','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/03.jpg','ON_LEAVE',2,'陈立','COUNSELOR,DEPT',1,0,'2026-11-03 21:00:00',40.0,'MID','2026-11-01 23:00:00','2026-11-02 05:00:00',0,0),
(22,'QJ202608160022',121,'许诺',1,'计算机学院','软件工程 2202','病假','2026-08-16 13:00:00','2026-08-18 05:00:00',4.0,'市口腔医院','家长 / 辅导员','138****0022','高铁','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/04.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-08-18 07:00:00',53.0,'MID','2026-08-15 22:00:00','2026-08-16 05:00:00',0,1),
(23,'QJ202609190023',122,'蒋文博',1,'计算机学院','软件工程 2203','公假','2026-09-19 08:00:00','2026-09-21 10:00:00',5.0,'市会展中心','家长 / 辅导员','138****0023','私家车','代表学院参加比赛/活动，附活动通知。','/uploads/seed/proof/05.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-09-21 12:00:00',66.0,'MID','2026-09-18 16:00:00','2026-09-19 00:00:00',0,2),
(24,'QJ202610220024',123,'黄雅静',1,'计算机学院','计算机科学 2201','实习','2026-10-22 13:00:00','2026-10-25 21:00:00',8.0,'上海 · 实习企业','家长 / 辅导员','138****0024','公交','参加校企合作实习，需连续在岗。','/uploads/seed/proof/06.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-10-25 23:00:00',91.0,'HIGH','2026-10-21 20:00:00','2026-10-22 05:00:00',0,0),
(25,'QJ202605250025',100,'张若曦',1,'计算机学院','软件工程 2201','跨省外出','2026-05-25 08:00:00','2026-05-25 13:00:00',0.5,'江苏省南京市','家长 / 辅导员','138****0025','飞机','家在外省，需返乡处理家庭事务。','/uploads/seed/proof/01.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-05-25 15:00:00',53.0,'MID','2026-05-25 02:00:00','2026-05-25 12:00:00',0,1),
(26,'QJ202606030026',101,'李昊然',1,'计算机学院','软件工程 2202','病假','2026-10-31 08:30:00','2026-10-31 18:30:00',1.0,'市口腔医院','家长 / 辅导员','138****0026','地铁','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/02.jpg','RETURN_PENDING',2,'陈立','COUNSELOR',0,0,'2026-10-31 20:30:00',28.0,'LOW','2026-10-31 01:30:00','2026-10-31 12:30:00',0,2),
(27,'QJ202607060027',102,'周文琪',1,'计算机学院','软件工程 2203','事假','2026-11-03 04:00:00','2026-11-03 19:00:00',1.5,'市区 · 办证中心','家长 / 辅导员','138****0027','高铁','家中有事需回处理，已与家长沟通。','/uploads/seed/proof/03.jpg','ON_LEAVE',2,'陈立','COUNSELOR',0,0,'2026-11-03 21:00:00',38.0,'LOW','2026-11-02 20:00:00','2026-11-03 08:00:00',0,0),
(28,'QJ202608090028',103,'赵一鸣',1,'计算机学院','计算机科学 2201','公假','2026-10-31 23:00:00','2026-11-01 19:00:00',2.0,'校团委组织活动','家长 / 辅导员','138****0028','私家车','代表学院参加比赛/活动，附活动通知。','/uploads/seed/proof/04.jpg','ON_LEAVE',2,'陈立','COUNSELOR,DEPT',1,0,'2026-11-01 21:00:00',48.0,'MID','2026-10-31 14:00:00','2026-11-01 03:00:00',0,1),
(29,'QJ202609120029',104,'孙可',1,'计算机学院','软件工程 2201','病假','2026-09-12 08:00:00','2026-09-13 14:00:00',3.0,'市第一人民医院 · 城东院区','家长 / 辅导员','138****0029','公交','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/05.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-09-13 16:00:00',61.0,'MID','2026-09-11 22:00:00','2026-09-12 12:00:00',0,2),
(30,'QJ202610150030',105,'陈思远',1,'计算机学院','软件工程 2202','跨省外出','2026-10-15 13:00:00','2026-10-17 05:00:00',4.0,'上海浦东新区','家长 / 辅导员','138****0030','飞机','家在外省，需返乡处理家庭事务。','/uploads/seed/proof/06.jpg','DRAFT',NULL,'','COUNSELOR,DEPT',1,0,'2026-10-17 07:00:00',74.0,'HIGH','2026-10-15 02:00:00','2026-10-15 17:00:00',0,0),
(31,'QJ202605180031',106,'王梓萱',1,'计算机学院','软件工程 2203','病假','2026-05-18 08:00:00','2026-05-20 10:00:00',5.0,'校医院转诊 · 市中心医院','家长 / 辅导员','138****0031','地铁','身体不适需就医复查，医生建议休息。','/uploads/seed/proof/01.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-05-20 12:00:00',52.0,'MID','2026-05-17 20:00:00','2026-05-18 12:00:00',0,1),
(32,'QJ202606210032',107,'刘子豪',1,'计算机学院','计算机科学 2201','事假','2026-06-21 13:00:00','2026-06-24 21:00:00',8.0,'家中（本市）','家长 / 辅导员','138****0032','高铁','家中有事需回处理，已与家长沟通。','/uploads/seed/proof/02.jpg','COMPLETED',2,'陈立','COUNSELOR,DEPT',1,0,'2026-06-24 23:00:00',77.0,'HIGH','2026-06-21 00:00:00','2026-06-21 17:00:00',0,2),
(33,'QJ202607240033',108,'吴桐',1,'计算机学院','软件工程 2201','公假','2026-10-31 13:30:00','2026-10-31 18:30:00',0.5,'省体育中心','家长 / 辅导员','138****0033','私家车','代表学院参加比赛/活动，附活动通知。','/uploads/seed/proof/03.jpg','RETURN_PENDING',2,'陈立','COUNSELOR,DEPT',1,0,'2026-10-31 20:30:00',39.0,'LOW','2026-10-30 23:30:00','2026-10-31 17:30:00',0,0);

INSERT INTO leave_approval (leave_id,node,approver_id,approver_name,action,opinion,create_time) VALUES
(1,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-01 11:00:00'),
(2,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-01 17:00:00'),
(3,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-07-09 05:00:00'),
(3,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-07-09 12:00:00'),
(4,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-01 19:00:00'),
(5,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-10-30 09:30:00'),
(5,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-10-30 18:30:00'),
(6,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-10-18 04:00:00'),
(6,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-10-18 14:00:00'),
(7,'COUNSELOR',2,'陈立','REJECT','请假事由说明过于简单，请补充具体行程。','2026-05-20 23:00:00'),
(8,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-10-30 02:00:00'),
(8,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-10-30 14:00:00'),
(9,'COUNSELOR',2,'陈立','REJECT','证明材料不完整，请补充医院诊断证明。','2026-07-26 23:00:00'),
(10,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-01 13:00:00'),
(11,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-01 14:00:00'),
(12,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-01 09:00:00'),
(14,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-01 17:00:00'),
(15,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-07-20 05:00:00'),
(15,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-07-20 12:00:00'),
(16,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-08-23 10:00:00'),
(16,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-08-23 18:00:00'),
(17,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-10-31 10:30:00'),
(18,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-01 15:00:00'),
(19,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-05-06 23:00:00'),
(19,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-05-07 10:00:00'),
(20,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-01 14:00:00'),
(20,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-11-02 02:00:00'),
(21,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-02 04:00:00'),
(21,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-11-02 17:00:00'),
(22,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-08-16 04:00:00'),
(22,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-08-16 18:00:00'),
(23,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-09-18 23:00:00'),
(23,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-09-19 14:00:00'),
(24,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-10-21 22:00:00'),
(24,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-10-22 02:00:00'),
(25,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-05-25 05:00:00'),
(25,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-05-25 10:00:00'),
(26,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-10-31 05:30:00'),
(27,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-11-03 01:00:00'),
(28,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-10-31 20:00:00'),
(28,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-11-01 04:00:00'),
(29,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-09-12 05:00:00'),
(29,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-09-12 14:00:00'),
(31,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-05-17 23:00:00'),
(31,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-05-18 10:00:00'),
(32,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-06-21 04:00:00'),
(32,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-06-21 16:00:00'),
(33,'COUNSELOR',2,'陈立','APPROVE','情况属实，同意请假。','2026-10-31 04:30:00'),
(33,'DEPT',4,'王志远','APPROVE','已核家长，同意。','2026-10-31 17:30:00');

INSERT INTO leave_extension (leave_id,old_end_time,new_end_time,add_days,reason,status,approver_id,approver_name,apply_time,approve_time,opinion) VALUES
(1,'2026-11-01 19:00:00','2026-11-02 19:00:00',1.5,'治疗未结束，需延长休假。','APPROVED',2,'陈立','2026-11-01 16:00:00','2026-11-01 18:00:00','同意延期，注意按时销假。'),
(3,'2026-07-09 23:00:00','2026-07-11 23:00:00',1.5,'治疗未结束，需延长休假。','PENDING',2,'陈立','2026-07-09 20:00:00',NULL,NULL),
(5,'2026-10-31 18:30:00','2026-11-01 18:30:00',1.5,'治疗未结束，需延长休假。','REJECTED',2,'陈立','2026-10-31 15:30:00','2026-10-31 17:30:00','同意延期，注意按时销假。'),
(6,'2026-10-20 05:00:00','2026-10-22 05:00:00',1.5,'治疗未结束，需延长休假。','APPROVED',2,'陈立','2026-10-20 02:00:00','2026-10-20 04:00:00','同意延期，注意按时销假。'),
(8,'2026-11-02 19:00:00','2026-11-03 19:00:00',1.5,'治疗未结束，需延长休假。','PENDING',2,'陈立','2026-11-02 16:00:00',NULL,NULL),
(15,'2026-07-22 10:00:00','2026-07-24 10:00:00',1.5,'治疗未结束，需延长休假。','REJECTED',2,'陈立','2026-07-22 07:00:00','2026-07-22 09:00:00','同意延期，注意按时销假。');

INSERT INTO return_record (leave_id,apply_no,student_id,student_name,return_code,code_expire,verify_type,verifier_id,verifier_name,verify_time,status,remark,create_time) VALUES
(3,'QJ202607090003',102,'周文琪','420000','2026-07-09 23:40:00','CODE',5,'刘梅','2026-07-09 23:30:00','VERIFIED','扫码核验通过，未超期。','2026-07-09 23:16:00'),
(6,'QJ202610180006',105,'陈思远','420137','2026-10-20 05:47:00','CODE',5,'刘梅','2026-10-20 05:37:00','VERIFIED','扫码核验通过，未超期。','2026-10-20 05:23:00'),
(15,'QJ202607200015',114,'谢明轩','420274','2026-07-22 10:54:00','CODE',5,'刘梅','2026-07-22 10:44:00','VERIFIED','扫码核验通过，未超期。','2026-07-22 10:30:00'),
(16,'QJ202608230016',115,'韩思彤','420411','2026-08-26 22:01:00','CODE',5,'刘梅','2026-08-26 21:51:00','VERIFIED','扫码核验通过，未超期。','2026-08-26 21:37:00'),
(19,'QJ202605070019',118,'唐婉清','420548','2026-05-08 00:08:00','CODE',5,'刘梅','2026-05-07 23:58:00','VERIFIED','扫码核验通过，未超期。','2026-05-07 23:44:00'),
(22,'QJ202608160022',121,'许诺','420685','2026-08-18 06:15:00','CODE',5,'刘梅','2026-08-18 06:05:00','VERIFIED','扫码核验通过，未超期。','2026-08-18 05:51:00'),
(23,'QJ202609190023',122,'蒋文博','420822','2026-09-21 11:22:00','CODE',5,'刘梅','2026-09-21 11:12:00','VERIFIED','扫码核验通过，未超期。','2026-09-21 10:58:00'),
(24,'QJ202610220024',123,'黄雅静','420959','2026-10-25 22:29:00','CODE',5,'刘梅','2026-10-25 22:19:00','VERIFIED','扫码核验通过，未超期。','2026-10-25 22:05:00'),
(25,'QJ202605250025',100,'张若曦','421096','2026-05-25 14:36:00','CODE',5,'刘梅','2026-05-25 14:26:00','VERIFIED','扫码核验通过，未超期。','2026-05-25 14:12:00'),
(29,'QJ202609120029',104,'孙可','421233','2026-09-13 15:43:00','CODE',5,'刘梅','2026-09-13 15:33:00','VERIFIED','扫码核验通过，未超期。','2026-09-13 15:19:00'),
(31,'QJ202605180031',106,'王梓萱','421370','2026-05-20 11:50:00','CODE',5,'刘梅','2026-05-20 11:40:00','VERIFIED','扫码核验通过，未超期。','2026-05-20 11:26:00'),
(32,'QJ202606210032',107,'刘子豪','421507','2026-06-24 22:57:00','CODE',5,'刘梅','2026-06-24 22:47:00','VERIFIED','扫码核验通过，未超期。','2026-06-24 22:33:00'),
(5,'QJ202609150005',104,'孙可','510000','2026-10-31 18:40:00',NULL,NULL,NULL,NULL,'PENDING','已生成返校码，等待宿管核验。','2026-10-31 18:25:00'),
(17,'QJ202609260017',116,'朱一诺','510211','2026-10-31 18:40:00',NULL,NULL,NULL,NULL,'PENDING','已生成返校码，等待宿管核验。','2026-10-31 18:25:00'),
(26,'QJ202606030026',101,'李昊然','510422','2026-10-31 18:40:00',NULL,NULL,NULL,NULL,'PENDING','已生成返校码，等待宿管核验。','2026-10-31 18:25:00'),
(33,'QJ202607240033',108,'吴桐','510633','2026-10-31 18:40:00',NULL,NULL,NULL,NULL,'PENDING','已生成返校码，等待宿管核验。','2026-10-31 18:25:00');

INSERT INTO late_return (student_id,student_name,dept_id,dept_name,class_name,dorm,return_time,reason,has_leave,leave_id,is_violation,remark,image_path,recorder_id,recorder_name,record_time,create_time) VALUES
(100,'张若曦',1,'计算机学院','软件工程 2201','6 栋 6-400','2026-07-05 21:00:00','实习加班',1,1,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/01.jpg',5,'刘梅','2026-07-05 21:04:00','2026-07-05 21:04:00'),
(103,'赵一鸣',1,'计算机学院','计算机科学 2201','6 栋 6-403','2026-08-07 22:07:00','交通延误',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/02.jpg',5,'刘梅','2026-08-07 22:11:00','2026-08-07 22:11:00'),
(106,'王梓萱',1,'计算机学院','软件工程 2203','6 栋 6-406','2026-09-09 23:14:00','就医',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/03.jpg',5,'刘梅','2026-09-09 23:18:00','2026-09-09 23:18:00'),
(109,'郑雨桐',1,'计算机学院','软件工程 2202','6 栋 6-409','2026-10-11 21:21:00','其他',1,4,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/04.jpg',5,'刘梅','2026-10-11 21:25:00','2026-10-11 21:25:00'),
(112,'何嘉树',1,'计算机学院','软件工程 2201','6 栋 6-412','2026-07-13 22:28:00','实习加班',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/05.jpg',5,'刘梅','2026-07-13 22:32:00','2026-07-13 22:32:00'),
(115,'韩思彤',1,'计算机学院','计算机科学 2201','6 栋 6-415','2026-08-15 23:35:00','交通延误',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/06.jpg',5,'刘梅','2026-08-15 23:39:00','2026-08-15 23:39:00'),
(118,'唐婉清',1,'计算机学院','软件工程 2203','6 栋 6-418','2026-09-17 21:42:00','就医',1,7,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/01.jpg',5,'刘梅','2026-09-17 21:46:00','2026-09-17 21:46:00'),
(121,'许诺',1,'计算机学院','软件工程 2202','6 栋 6-421','2026-10-19 22:49:00','其他',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/02.jpg',5,'刘梅','2026-10-19 22:53:00','2026-10-19 22:53:00'),
(100,'张若曦',1,'计算机学院','软件工程 2201','6 栋 6-400','2026-07-21 23:56:00','实习加班',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/03.jpg',5,'刘梅','2026-07-22 00:00:00','2026-07-22 00:00:00'),
(103,'赵一鸣',1,'计算机学院','计算机科学 2201','6 栋 6-403','2026-08-23 21:03:00','交通延误',1,10,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/04.jpg',5,'刘梅','2026-08-23 21:07:00','2026-08-23 21:07:00'),
(106,'王梓萱',1,'计算机学院','软件工程 2203','6 栋 6-406','2026-09-25 22:10:00','就医',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/05.jpg',5,'刘梅','2026-09-25 22:14:00','2026-09-25 22:14:00'),
(109,'郑雨桐',1,'计算机学院','软件工程 2202','6 栋 6-409','2026-10-27 23:17:00','其他',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/06.jpg',5,'刘梅','2026-10-27 23:21:00','2026-10-27 23:21:00'),
(112,'何嘉树',1,'计算机学院','软件工程 2201','6 栋 6-412','2026-07-29 21:24:00','实习加班',1,13,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/01.jpg',5,'刘梅','2026-07-29 21:28:00','2026-07-29 21:28:00'),
(115,'韩思彤',1,'计算机学院','计算机科学 2201','6 栋 6-415','2026-08-05 22:31:00','交通延误',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/02.jpg',5,'刘梅','2026-08-05 22:35:00','2026-08-05 22:35:00'),
(118,'唐婉清',1,'计算机学院','软件工程 2203','6 栋 6-418','2026-09-07 23:38:00','就医',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/03.jpg',5,'刘梅','2026-09-07 23:42:00','2026-09-07 23:42:00'),
(121,'许诺',1,'计算机学院','软件工程 2202','6 栋 6-421','2026-10-09 21:45:00','其他',1,16,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/04.jpg',5,'刘梅','2026-10-09 21:49:00','2026-10-09 21:49:00'),
(100,'张若曦',1,'计算机学院','软件工程 2201','6 栋 6-400','2026-07-11 22:52:00','实习加班',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/05.jpg',5,'刘梅','2026-07-11 22:56:00','2026-07-11 22:56:00'),
(103,'赵一鸣',1,'计算机学院','计算机科学 2201','6 栋 6-403','2026-08-13 23:59:00','交通延误',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/06.jpg',5,'刘梅','2026-08-14 00:03:00','2026-08-14 00:03:00'),
(106,'王梓萱',1,'计算机学院','软件工程 2203','6 栋 6-406','2026-09-15 21:06:00','就医',1,19,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/01.jpg',5,'刘梅','2026-09-15 21:10:00','2026-09-15 21:10:00'),
(109,'郑雨桐',1,'计算机学院','软件工程 2202','6 栋 6-409','2026-10-17 22:13:00','其他',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/02.jpg',5,'刘梅','2026-10-17 22:17:00','2026-10-17 22:17:00'),
(112,'何嘉树',1,'计算机学院','软件工程 2201','6 栋 6-412','2026-07-19 23:20:00','实习加班',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/03.jpg',5,'刘梅','2026-07-19 23:24:00','2026-07-19 23:24:00'),
(115,'韩思彤',1,'计算机学院','计算机科学 2201','6 栋 6-415','2026-08-21 21:27:00','交通延误',1,22,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/04.jpg',5,'刘梅','2026-08-21 21:31:00','2026-08-21 21:31:00'),
(118,'唐婉清',1,'计算机学院','软件工程 2203','6 栋 6-418','2026-09-23 22:34:00','就医',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/05.jpg',5,'刘梅','2026-09-23 22:38:00','2026-09-23 22:38:00'),
(121,'许诺',1,'计算机学院','软件工程 2202','6 栋 6-421','2026-10-25 23:41:00','其他',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/06.jpg',5,'刘梅','2026-10-25 23:45:00','2026-10-25 23:45:00'),
(100,'张若曦',1,'计算机学院','软件工程 2201','6 栋 6-400','2026-07-27 21:48:00','实习加班',1,25,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/01.jpg',5,'刘梅','2026-07-27 21:52:00','2026-07-27 21:52:00'),
(103,'赵一鸣',1,'计算机学院','计算机科学 2201','6 栋 6-403','2026-08-29 22:55:00','交通延误',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/02.jpg',5,'刘梅','2026-08-29 22:59:00','2026-08-29 22:59:00'),
(106,'王梓萱',1,'计算机学院','软件工程 2203','6 栋 6-406','2026-09-05 23:02:00','就医',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/03.jpg',5,'刘梅','2026-09-05 23:06:00','2026-09-05 23:06:00'),
(109,'郑雨桐',1,'计算机学院','软件工程 2202','6 栋 6-409','2026-10-07 21:09:00','其他',1,28,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/04.jpg',5,'刘梅','2026-10-07 21:13:00','2026-10-07 21:13:00'),
(112,'何嘉树',1,'计算机学院','软件工程 2201','6 栋 6-412','2026-07-09 22:16:00','实习加班',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/05.jpg',5,'刘梅','2026-07-09 22:20:00','2026-07-09 22:20:00'),
(115,'韩思彤',1,'计算机学院','计算机科学 2201','6 栋 6-415','2026-08-11 23:23:00','交通延误',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/06.jpg',5,'刘梅','2026-08-11 23:27:00','2026-08-11 23:27:00'),
(118,'唐婉清',1,'计算机学院','软件工程 2203','6 栋 6-418','2026-09-13 21:30:00','就医',1,31,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/01.jpg',5,'刘梅','2026-09-13 21:34:00','2026-09-13 21:34:00'),
(121,'许诺',1,'计算机学院','软件工程 2202','6 栋 6-421','2026-10-15 22:37:00','其他',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/02.jpg',5,'刘梅','2026-10-15 22:41:00','2026-10-15 22:41:00'),
(100,'张若曦',1,'计算机学院','软件工程 2201','6 栋 6-400','2026-07-17 23:44:00','实习加班',0,NULL,1,'未说明具体原因，已记录并通知辅导员。','/uploads/seed/proof/03.jpg',5,'刘梅','2026-07-17 23:48:00','2026-07-17 23:48:00'),
(103,'赵一鸣',1,'计算机学院','计算机科学 2201','6 栋 6-403','2026-08-19 21:51:00','交通延误',1,1,0,'已出示请假单，口头提醒按时返寝。','/uploads/seed/proof/04.jpg',5,'刘梅','2026-08-19 21:55:00','2026-08-19 21:55:00');

INSERT INTO absence_case (case_no,student_id,student_name,dept_id,dept_name,class_name,case_type,level,trigger_desc,status,owner_id,owner_name,deadline,close_time,create_time,update_time) VALUES
('YC2026100001',100,'张若曦',1,'计算机学院','软件工程 2201','OVERDUE','HIGH','请假结束 24 小时未提交销假','PENDING',2,'陈立','2026-10-04 20:00:00',NULL,'2026-10-02 20:00:00','2026-10-03 02:00:00'),
('YC2026100002',105,'陈思远',1,'计算机学院','软件工程 2202','NIGHT_ABSENT','HIGH','23:30 未返寝且无有效请假','PROCESSING',2,'陈立','2026-10-06 20:00:00',NULL,'2026-10-04 20:00:00','2026-10-05 02:00:00'),
('YC2026100003',110,'林知远',1,'计算机学院','软件工程 2203','REPEAT_LATE','MID','近 14 天晚归 3 次','CLOSED',2,'陈立','2026-10-08 20:00:00','2026-10-07 23:00:00','2026-10-06 20:00:00','2026-10-07 02:00:00'),
('YC2026100004',115,'韩思彤',1,'计算机学院','计算机科学 2201','OVERDUE','HIGH','请假结束 24 小时未提交销假','PENDING',2,'陈立','2026-10-10 20:00:00',NULL,'2026-10-08 20:00:00','2026-10-09 02:00:00'),
('YC2026100005',120,'邓佳怡',1,'计算机学院','软件工程 2201','NIGHT_ABSENT','HIGH','23:30 未返寝且无有效请假','PROCESSING',2,'陈立','2026-10-12 20:00:00',NULL,'2026-10-10 20:00:00','2026-10-11 02:00:00'),
('YC2026100006',101,'李昊然',1,'计算机学院','软件工程 2202','REPEAT_LATE','MID','近 14 天晚归 3 次','CLOSED',2,'陈立','2026-10-14 20:00:00','2026-10-13 23:00:00','2026-10-12 20:00:00','2026-10-13 02:00:00'),
('YC2026100007',106,'王梓萱',1,'计算机学院','软件工程 2203','OVERDUE','HIGH','请假结束 24 小时未提交销假','PENDING',2,'陈立','2026-10-16 20:00:00',NULL,'2026-10-14 20:00:00','2026-10-15 02:00:00'),
('YC2026100008',111,'徐若彤',1,'计算机学院','计算机科学 2201','NIGHT_ABSENT','HIGH','23:30 未返寝且无有效请假','PROCESSING',2,'陈立','2026-10-18 20:00:00',NULL,'2026-10-16 20:00:00','2026-10-17 02:00:00'),
('YC2026100009',116,'朱一诺',1,'计算机学院','软件工程 2201','REPEAT_LATE','MID','近 14 天晚归 3 次','CLOSED',2,'陈立','2026-10-20 20:00:00','2026-10-19 23:00:00','2026-10-18 20:00:00','2026-10-19 02:00:00'),
('YC2026100010',121,'许诺',1,'计算机学院','软件工程 2202','OVERDUE','HIGH','请假结束 24 小时未提交销假','PENDING',2,'陈立','2026-10-22 20:00:00',NULL,'2026-10-20 20:00:00','2026-10-21 02:00:00'),
('YC2026100011',102,'周文琪',1,'计算机学院','软件工程 2203','NIGHT_ABSENT','HIGH','23:30 未返寝且无有效请假','PROCESSING',2,'陈立','2026-10-24 20:00:00',NULL,'2026-10-22 20:00:00','2026-10-23 02:00:00'),
('YC2026100012',107,'刘子豪',1,'计算机学院','计算机科学 2201','REPEAT_LATE','MID','近 14 天晚归 3 次','CLOSED',2,'陈立','2026-10-26 20:00:00','2026-10-25 23:00:00','2026-10-24 20:00:00','2026-10-25 02:00:00');

INSERT INTO care_record (case_id,student_id,student_name,care_way,content,result,recorder_id,recorder_name,record_time,create_time) VALUES
(1,100,'张若曦','PHONE','学生称在返程途中，情绪平稳，已提醒注意安全。','要求 22:00 前到楼并生成返校码，次日上午补交凭证。',2,'陈立','2026-10-03 19:30:00','2026-10-03 19:30:00'),
(2,104,'孙可','PARENT','家长确认学生已离校返乡，明日返校。','已登记家长联系方式，纳入重点关注名单。',2,'陈立','2026-10-05 19:30:00','2026-10-05 19:30:00'),
(3,108,'吴桐','VISIT','学生称在返程途中，情绪平稳，已提醒注意安全。','要求 22:00 前到楼并生成返校码，次日上午补交凭证。',2,'陈立','2026-10-07 19:30:00','2026-10-07 19:30:00'),
(4,112,'何嘉树','PEER','家长确认学生已离校返乡，明日返校。','已登记家长联系方式，纳入重点关注名单。',2,'陈立','2026-10-09 19:30:00','2026-10-09 19:30:00'),
(5,116,'朱一诺','PHONE','学生称在返程途中，情绪平稳，已提醒注意安全。','要求 22:00 前到楼并生成返校码，次日上午补交凭证。',2,'陈立','2026-10-11 19:30:00','2026-10-11 19:30:00'),
(6,120,'邓佳怡','PARENT','家长确认学生已离校返乡，明日返校。','已登记家长联系方式，纳入重点关注名单。',2,'陈立','2026-10-13 19:30:00','2026-10-13 19:30:00'),
(7,100,'张若曦','VISIT','学生称在返程途中，情绪平稳，已提醒注意安全。','要求 22:00 前到楼并生成返校码，次日上午补交凭证。',2,'陈立','2026-10-15 19:30:00','2026-10-15 19:30:00'),
(8,104,'孙可','PEER','家长确认学生已离校返乡，明日返校。','已登记家长联系方式，纳入重点关注名单。',2,'陈立','2026-10-17 19:30:00','2026-10-17 19:30:00'),
(9,108,'吴桐','PHONE','学生称在返程途中，情绪平稳，已提醒注意安全。','要求 22:00 前到楼并生成返校码，次日上午补交凭证。',2,'陈立','2026-10-19 19:30:00','2026-10-19 19:30:00'),
(10,112,'何嘉树','PARENT','家长确认学生已离校返乡，明日返校。','已登记家长联系方式，纳入重点关注名单。',2,'陈立','2026-10-21 19:30:00','2026-10-21 19:30:00'),
(11,116,'朱一诺','VISIT','学生称在返程途中，情绪平稳，已提醒注意安全。','要求 22:00 前到楼并生成返校码，次日上午补交凭证。',2,'陈立','2026-10-23 19:30:00','2026-10-23 19:30:00'),
(12,120,'邓佳怡','PEER','家长确认学生已离校返乡，明日返校。','已登记家长联系方式，纳入重点关注名单。',2,'陈立','2026-10-25 19:30:00','2026-10-25 19:30:00'),
(1,100,'张若曦','PHONE','学生称在返程途中，情绪平稳，已提醒注意安全。','要求 22:00 前到楼并生成返校码，次日上午补交凭证。',2,'陈立','2026-10-27 19:30:00','2026-10-27 19:30:00'),
(2,104,'孙可','PARENT','家长确认学生已离校返乡，明日返校。','已登记家长联系方式，纳入重点关注名单。',2,'陈立','2026-10-29 19:30:00','2026-10-29 19:30:00');

INSERT INTO risk_rule (name,version,w_freq,w_days,w_late,w_overdue,w_type,w_reject,low_threshold,high_threshold,enabled,effective_time,create_by,create_time) VALUES
('请假行为风险分层规则','v1',25.00,25.00,20.00,20.00,5.00,5.00,40.0,70.0,0,'2026-03-01 00:00:00','admin','2026-03-01 09:00:00'),
('请假行为风险分层规则','v2',25.00,20.00,20.00,25.00,5.00,5.00,40.0,70.0,0,'2026-06-15 00:00:00','admin','2026-06-15 09:00:00'),
('请假行为风险分层规则','v3',20.00,20.00,20.00,25.00,10.00,5.00,40.0,70.0,1,'2026-09-01 00:00:00','admin','2026-09-01 09:00:00');

INSERT INTO risk_score (student_id,student_name,class_name,rule_version,snapshot,detail_json,total_score,level,suggest,adjust_level,adjust_reason,adjust_by,adjust_time,calc_time) VALUES
(100,'张若曦','软件工程 2201','v3','{"freq":1,"days":2.5,"late":0,"overdue":0,"type":"病假","reject":0}','{"freq":2.5,"days":1.7,"late":0.0,"overdue":0.0,"type":2.0,"reject":0.0}',6.2,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(101,'李昊然','软件工程 2202','v3','{"freq":4,"days":9.5,"late":2,"overdue":1,"type":"事假","reject":1}','{"freq":10.0,"days":6.3,"late":6.7,"overdue":6.2,"type":2.0,"reject":1.7}',32.9,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(102,'周文琪','软件工程 2203','v3','{"freq":1,"days":16.5,"late":4,"overdue":2,"type":"公假","reject":2}','{"freq":2.5,"days":11.0,"late":13.3,"overdue":12.5,"type":2.0,"reject":3.3}',44.7,'MID','建议关注其请假规律，提醒按时销假。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(103,'赵一鸣','计算机科学 2201','v3','{"freq":4,"days":23.5,"late":1,"overdue":3,"type":"实习","reject":0}','{"freq":10.0,"days":15.7,"late":3.3,"overdue":18.8,"type":2.0,"reject":0.0}',49.8,'MID','建议关注其请假规律，提醒按时销假。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(104,'孙可','软件工程 2201','v3','{"freq":1,"days":8.5,"late":3,"overdue":0,"type":"跨省外出","reject":1}','{"freq":2.5,"days":5.7,"late":10.0,"overdue":0.0,"type":6.0,"reject":1.7}',25.8,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(105,'陈思远','软件工程 2202','v3','{"freq":4,"days":15.5,"late":0,"overdue":1,"type":"病假","reject":2}','{"freq":10.0,"days":10.3,"late":0.0,"overdue":6.2,"type":2.0,"reject":3.3}',31.9,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(106,'王梓萱','软件工程 2203','v3','{"freq":1,"days":22.5,"late":2,"overdue":2,"type":"事假","reject":0}','{"freq":2.5,"days":15.0,"late":6.7,"overdue":12.5,"type":2.0,"reject":0.0}',38.7,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(107,'刘子豪','计算机科学 2201','v3','{"freq":4,"days":7.5,"late":4,"overdue":3,"type":"病假","reject":1}','{"freq":10.0,"days":5.0,"late":13.3,"overdue":18.8,"type":2.0,"reject":1.7}',50.7,'MID','建议关注其请假规律，提醒按时销假。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(108,'吴桐','软件工程 2201','v3','{"freq":1,"days":14.5,"late":1,"overdue":0,"type":"实习","reject":2}','{"freq":2.5,"days":9.7,"late":3.3,"overdue":0.0,"type":2.0,"reject":3.3}',20.8,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(109,'郑雨桐','软件工程 2202','v3','{"freq":4,"days":21.5,"late":3,"overdue":1,"type":"跨省外出","reject":0}','{"freq":10.0,"days":14.3,"late":10.0,"overdue":6.2,"type":6.0,"reject":0.0}',46.6,'MID','建议关注其请假规律，提醒按时销假。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(110,'林知远','软件工程 2203','v3','{"freq":1,"days":6.5,"late":0,"overdue":2,"type":"病假","reject":1}','{"freq":2.5,"days":4.3,"late":0.0,"overdue":12.5,"type":2.0,"reject":1.7}',23.0,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(111,'徐若彤','计算机科学 2201','v3','{"freq":4,"days":13.5,"late":2,"overdue":3,"type":"事假","reject":2}','{"freq":10.0,"days":9.0,"late":6.7,"overdue":18.8,"type":2.0,"reject":3.3}',49.8,'MID','建议关注其请假规律，提醒按时销假。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(112,'何嘉树','软件工程 2201','v3','{"freq":1,"days":20.5,"late":4,"overdue":0,"type":"公假","reject":0}','{"freq":2.5,"days":13.7,"late":13.3,"overdue":0.0,"type":2.0,"reject":0.0}',31.5,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(113,'曹雨晴','软件工程 2202','v3','{"freq":4,"days":5.5,"late":1,"overdue":1,"type":"实习","reject":1}','{"freq":10.0,"days":3.7,"late":3.3,"overdue":6.2,"type":2.0,"reject":1.7}',26.9,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(114,'谢明轩','软件工程 2203','v3','{"freq":1,"days":12.5,"late":3,"overdue":2,"type":"病假","reject":2}','{"freq":2.5,"days":8.3,"late":10.0,"overdue":12.5,"type":6.0,"reject":3.3}',42.7,'MID','建议关注其请假规律，提醒按时销假。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(115,'韩思彤','计算机科学 2201','v3','{"freq":4,"days":19.5,"late":0,"overdue":3,"type":"病假","reject":0}','{"freq":10.0,"days":13.0,"late":0.0,"overdue":18.8,"type":2.0,"reject":0.0}',43.8,'MID','建议关注其请假规律，提醒按时销假。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(116,'朱一诺','软件工程 2201','v3','{"freq":1,"days":4.5,"late":2,"overdue":0,"type":"事假","reject":1}','{"freq":2.5,"days":3.0,"late":6.7,"overdue":0.0,"type":2.0,"reject":1.7}',15.8,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(117,'沈亦辰','软件工程 2202','v3','{"freq":4,"days":11.5,"late":4,"overdue":1,"type":"公假","reject":2}','{"freq":10.0,"days":7.7,"late":13.3,"overdue":6.2,"type":2.0,"reject":3.3}',42.6,'MID','建议关注其请假规律，提醒按时销假。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(118,'唐婉清','软件工程 2203','v3','{"freq":1,"days":18.5,"late":1,"overdue":2,"type":"实习","reject":0}','{"freq":2.5,"days":12.3,"late":3.3,"overdue":12.5,"type":2.0,"reject":0.0}',32.7,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(119,'冯子墨','计算机科学 2201','v3','{"freq":4,"days":3.5,"late":3,"overdue":3,"type":"跨省外出","reject":1}','{"freq":10.0,"days":2.3,"late":10.0,"overdue":18.8,"type":6.0,"reject":1.7}',48.8,'MID','建议关注其请假规律，提醒按时销假。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(120,'邓佳怡','软件工程 2201','v3','{"freq":1,"days":10.5,"late":0,"overdue":0,"type":"病假","reject":2}','{"freq":2.5,"days":7.0,"late":0.0,"overdue":0.0,"type":2.0,"reject":3.3}',14.8,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(121,'许诺','软件工程 2202','v3','{"freq":4,"days":17.5,"late":2,"overdue":1,"type":"病假","reject":0}','{"freq":10.0,"days":11.7,"late":6.7,"overdue":6.2,"type":2.0,"reject":0.0}',36.6,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(122,'蒋文博','软件工程 2203','v3','{"freq":1,"days":2.5,"late":4,"overdue":2,"type":"公假","reject":1}','{"freq":2.5,"days":1.7,"late":13.3,"overdue":12.5,"type":2.0,"reject":1.7}',33.7,'LOW','当前行为平稳，保持常规关注即可。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00'),
(123,'黄雅静','计算机科学 2201','v3','{"freq":4,"days":9.5,"late":1,"overdue":3,"type":"实习","reject":2}','{"freq":10.0,"days":6.3,"late":3.3,"overdue":18.8,"type":2.0,"reject":3.3}',43.8,'MID','建议关注其请假规律，提醒按时销假。',NULL,NULL,NULL,NULL,'2026-10-30 08:00:00');

INSERT INTO sys_message (title,content,type,biz_no,biz_id,receiver_id,is_read,create_time) VALUES
('新的请假申请待审批','QJ202605030001 由 张若曦 提交，请及时处理。','APPROVAL','QJ202605030001',1,2,0,'2026-11-01 08:01:00'),
('新的请假申请待审批','QJ202606060002 由 李昊然 提交，请及时处理。','APPROVAL','QJ202606060002',2,2,1,'2026-11-01 13:01:00'),
('新的请假申请待审批','QJ202607090003 由 周文琪 提交，请及时处理。','APPROVAL','QJ202607090003',3,2,0,'2026-07-09 00:01:00'),
('新的请假申请待审批','QJ202608120004 由 赵一鸣 提交，请及时处理。','APPROVAL','QJ202608120004',4,2,1,'2026-11-01 13:01:00'),
('新的请假申请待审批','QJ202609150005 由 孙可 提交，请及时处理。','APPROVAL','QJ202609150005',5,2,0,'2026-10-30 02:31:00'),
('新的请假申请待审批','QJ202610180006 由 陈思远 提交，请及时处理。','APPROVAL','QJ202610180006',6,2,1,'2026-10-18 02:01:00'),
('新的请假申请待审批','QJ202605210007 由 王梓萱 提交，请及时处理。','APPROVAL','QJ202605210007',7,2,0,'2026-05-20 20:01:00'),
('新的请假申请待审批','QJ202606240008 由 刘子豪 提交，请及时处理。','APPROVAL','QJ202606240008',8,2,1,'2026-10-29 22:01:00'),
('新的请假申请待审批','QJ202607270009 由 吴桐 提交，请及时处理。','APPROVAL','QJ202607270009',9,2,0,'2026-07-26 18:01:00'),
('新的请假申请待审批','QJ202608050010 由 李昊然 提交，请及时处理。','APPROVAL','QJ202608050010',10,2,1,'2026-11-01 07:01:00'),
('新的请假申请待审批','QJ202609080011 由 周文琪 提交，请及时处理。','APPROVAL','QJ202609080011',11,2,0,'2026-11-01 07:01:00'),
('新的请假申请待审批','QJ202610110012 由 赵一鸣 提交，请及时处理。','APPROVAL','QJ202610110012',12,2,1,'2026-11-01 07:01:00'),
('超期未销假预警','有 2 条请假已超过应销假时间，请核查。','OVERDUE','-',NULL,2,0,'2026-10-30 09:00:00'),
('超期未销假预警','有 2 条请假已超过应销假时间，请核查。','OVERDUE','-',NULL,2,0,'2026-10-30 09:00:00'),
('超期未销假预警','有 2 条请假已超过应销假时间，请核查。','OVERDUE','-',NULL,2,0,'2026-10-30 09:00:00'),
('超期未销假预警','有 2 条请假已超过应销假时间，请核查。','OVERDUE','-',NULL,2,0,'2026-10-30 09:00:00'),
('返校码核验成功','张若曦的返校码已由宿管核验，销假完成。','SYSTEM','QJ202610280012',1,101,1,'2026-10-30 19:12:00');

INSERT INTO sys_log (user_id,user_name,module,action,biz_no,before_status,after_status,reason,ip,create_time) VALUES
(2,'陈立','请假审批','APPROVE','QJ202605030001','COUNSELOR_PENDING','ON_LEAVE','情况属实，同意请假。','192.168.1.22','2026-11-01 11:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202606060002','COUNSELOR_PENDING','COUNSELOR_PENDING','情况属实，同意请假。','192.168.1.22','2026-11-01 16:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202607090003','COUNSELOR_PENDING','COMPLETED','情况属实，同意请假。','192.168.1.22','2026-07-09 03:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202608120004','COUNSELOR_PENDING','DEPT_PENDING','情况属实，同意请假。','192.168.1.22','2026-11-01 16:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202609150005','COUNSELOR_PENDING','RETURN_PENDING','情况属实，同意请假。','192.168.1.22','2026-10-30 05:30:00'),
(2,'陈立','请假审批','APPROVE','QJ202610180006','COUNSELOR_PENDING','COMPLETED','情况属实，同意请假。','192.168.1.22','2026-10-18 05:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202605210007','COUNSELOR_PENDING','REJECTED','情况属实，同意请假。','192.168.1.22','2026-05-20 23:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202606240008','COUNSELOR_PENDING','ON_LEAVE','情况属实，同意请假。','192.168.1.22','2026-10-30 01:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202607270009','COUNSELOR_PENDING','REJECTED','情况属实，同意请假。','192.168.1.22','2026-07-26 21:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202608050010','COUNSELOR_PENDING','COUNSELOR_PENDING','情况属实，同意请假。','192.168.1.22','2026-11-01 10:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202609080011','COUNSELOR_PENDING','DEPT_PENDING','情况属实，同意请假。','192.168.1.22','2026-11-01 10:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202610110012','COUNSELOR_PENDING','COUNSELOR_PENDING','情况属实，同意请假。','192.168.1.22','2026-11-01 10:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202605140013','COUNSELOR_PENDING','CANCELLED','情况属实，同意请假。','192.168.1.22','2026-05-14 05:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202606170014','COUNSELOR_PENDING','DEPT_PENDING','情况属实，同意请假。','192.168.1.22','2026-11-01 16:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202607200015','COUNSELOR_PENDING','COMPLETED','情况属实，同意请假。','192.168.1.22','2026-07-20 03:00:00'),
(2,'陈立','请假审批','APPROVE','QJ202608230016','COUNSELOR_PENDING','COMPLETED','情况属实，同意请假。','192.168.1.22','2026-08-23 07:00:00'),
(1,'admin','规则配置','PUBLISH','RISK-v3','v2','v3','调整逾期销假权重至 25%','192.168.1.10','2026-09-01 09:00:00');

INSERT INTO sys_file (file_name,path,size,content_type,biz_type,uploader_id,create_time) VALUES
('诊断证明-01.jpg','/uploads/seed/proof/01.jpg',120000,'image/jpeg','PROOF',101,'2026-10-20 10:00:00'),
('诊断证明-02.jpg','/uploads/seed/proof/02.jpg',129000,'image/jpeg','PROOF',101,'2026-10-21 10:00:00'),
('诊断证明-03.jpg','/uploads/seed/proof/03.jpg',138000,'image/jpeg','PROOF',101,'2026-10-22 10:00:00'),
('诊断证明-04.jpg','/uploads/seed/proof/04.jpg',147000,'image/jpeg','PROOF',101,'2026-10-23 10:00:00'),
('诊断证明-05.jpg','/uploads/seed/proof/05.jpg',156000,'image/jpeg','PROOF',101,'2026-10-24 10:00:00'),
('诊断证明-06.jpg','/uploads/seed/proof/06.jpg',165000,'image/jpeg','PROOF',101,'2026-10-25 10:00:00'),
('avatar-01.jpg','/uploads/seed/avatar/01.jpg',130000,'image/jpeg','AVATAR',101,'2026-10-01 09:00:00'),
('avatar-02.jpg','/uploads/seed/avatar/02.jpg',130000,'image/jpeg','AVATAR',101,'2026-10-01 09:00:00'),
('avatar-03.jpg','/uploads/seed/avatar/03.jpg',130000,'image/jpeg','AVATAR',101,'2026-10-01 09:00:00'),
('avatar-04.jpg','/uploads/seed/avatar/04.jpg',130000,'image/jpeg','AVATAR',101,'2026-10-01 09:00:00'),
('avatar-05.jpg','/uploads/seed/avatar/05.jpg',130000,'image/jpeg','AVATAR',101,'2026-10-01 09:00:00'),
('avatar-06.jpg','/uploads/seed/avatar/06.jpg',130000,'image/jpeg','AVATAR',101,'2026-10-01 09:00:00'),
('avatar-07.jpg','/uploads/seed/avatar/07.jpg',130000,'image/jpeg','AVATAR',101,'2026-10-01 09:00:00'),
('avatar-08.jpg','/uploads/seed/avatar/08.jpg',130000,'image/jpeg','AVATAR',101,'2026-10-01 09:00:00');

SET FOREIGN_KEY_CHECKS = 1;