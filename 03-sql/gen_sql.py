#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NEW-023 数据库脚本生成器：建库/建表/索引/测试数据（跨 6 个月时间分布）"""
import random, pathlib, datetime as dt

random.seed(23)
OUT = pathlib.Path(__file__).parent / "init.sql"
L = []


def w(s=""):
    L.append(s)


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def ts(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")


w("-- NEW-023 学生请销假与晚归统计管理系统 · MySQL 8 初始化脚本")
w("-- 生成时间：2026-10-31 · 库名 new_023 · 字符集 utf8mb4")
w("SET NAMES utf8mb4;")
w("SET FOREIGN_KEY_CHECKS = 0;")
w("DROP DATABASE IF EXISTS new_023;")
w("CREATE DATABASE new_023 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
w("USE new_023;")
w()

DDL = """
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
) COMMENT '风险计算结果表（保留输入快照与规则版本）';
"""

for stmt in DDL.strip().split(";\n\n"):
    w(stmt.strip() + ";")
    w()

# ---------------- 基础数据 ----------------
w("-- ========== 基础数据 ==========")
w("INSERT INTO sys_dept (id,name,code,sort,create_time) VALUES "
  "(1,'计算机学院','CS',1,'2026-01-05 09:00:00'),"
  "(2,'电子信息学院','EE',2,'2026-01-05 09:00:00'),"
  "(3,'外国语学院','FL',3,'2026-01-05 09:00:00'),"
  "(4,'机械工程学院','ME',4,'2026-01-05 09:00:00'),"
  "(5,'学生工作处','SW',5,'2026-01-05 09:00:00');")
w()

roles = [("STUDENT", "学生", "SELF"), ("COUNSELOR", "辅导员 / 班主任", "CLASS"),
         ("DEPT_HEAD", "院系学工负责人", "DEPT"), ("DORM", "宿管值班员", "DEPT"), ("ADMIN", "系统管理员", "ALL")]
w("INSERT INTO sys_role (id,code,name,data_scope,remark,create_time) VALUES")
vals = []
for i, (c, n, s) in enumerate(roles, 1):
    remark = {"SELF": "仅本人数据", "CLASS": "所带班级", "DEPT": "本院系/本楼栋", "ALL": "全校"}[s]
    vals.append(f"({i},{q(c)},{q(n)},{q(s)},{q(remark)},'2026-01-05 09:10:00')")
w(",\n".join(vals) + ";")
w()

# 菜单
MENUS = [
    (1, 0, "工作台", "/dashboard", "Dashboard", "i-dashboard", "dashboard:view", "MENU", 1, 1),
    (2, 0, "请假管理", "/leave", "Layout", "i-list", "leave:view", "DIR", 2, 1),
    (3, 2, "我的请假", "/leave/list", "leave/LeaveList", "i-list", "leave:list", "MENU", 1, 1),
    (4, 2, "发起请假", "/leave/create", "leave/LeaveForm", "i-plus", "leave:add", "MENU", 2, 1),
    (5, 2, "返校销假", "/leave/return", "leave/ReturnVerify", "i-check", "leave:return", "MENU", 3, 1),
    (6, 0, "审批中心", "/approval", "Layout", "i-shield", "approval:view", "DIR", 3, 1),
    (7, 6, "审批工作台", "/approval/desk", "approval/ApprovalDesk", "i-shield", "approval:desk", "MENU", 1, 1),
    (8, 6, "批量审批", "/approval/batch", "", "i-check", "approval:batch", "BUTTON", 2, 0),
    (9, 6, "院系审批", "/approval/dept", "approval/DeptApprove", "i-shield", "approval:dept", "MENU", 3, 1),
    (10, 0, "安全管理", "/safety", "Layout", "i-alert", "safety:view", "DIR", 4, 1),
    (11, 10, "晚归登记", "/safety/late", "safety/LateRegister", "i-clock", "late:list", "MENU", 1, 1),
    (12, 10, "未归核查", "/safety/cases", "safety/CaseList", "i-alert", "case:list", "MENU", 2, 1),
    (13, 10, "关怀记录", "/safety/care", "safety/CareList", "i-note", "care:list", "MENU", 3, 1),
    (14, 0, "统计分析", "/stats", "Stats", "i-chart", "stats:view", "MENU", 5, 1),
    (15, 0, "小学工", "/", "", "i-users", "", "DIR", 9, 0),
    (16, 0, "规则配置", "/admin/rules", "admin/RuleConfig", "i-settings", "rule:config", "MENU", 6, 1),
    (17, 0, "用户管理", "/admin/users", "admin/UserList", "i-users", "user:list", "MENU", 7, 1),
    (18, 0, "角色管理", "/admin/roles", "admin/RoleList", "i-shield", "role:list", "MENU", 8, 1),
    (19, 0, "菜单管理", "/admin/menus", "admin/MenuList", "i-list", "menu:list", "MENU", 9, 1),
    (20, 0, "个人中心", "/profile", "Profile", "i-avatar", "profile:view", "MENU", 10, 0),
    (21, 12, "关闭工单", "/", "", "i-check", "case:close", "BUTTON", 1, 0),
    (22, 11, "新增晚归", "/", "", "i-plus", "late:add", "BUTTON", 1, 0),
]
w("INSERT INTO sys_menu (id,parent_id,name,path,component,icon,perm,type,sort,visible) VALUES")
w(",\n".join(f"({a},{b},{q(c)},{q(d)},{q(e)},{q(f)},{q(g)},{q(h)},{i},{j})" for a, b, c, d, e, f, g, h, i, j in MENUS) + ";")
w()

ROLE_MENUS = {
    1: [1, 2, 3, 4, 5, 20],                                    # STUDENT
    2: [1, 2, 3, 6, 7, 8, 10, 12, 13, 14, 20, 21],             # COUNSELOR
    3: [1, 2, 3, 6, 7, 9, 10, 12, 13, 14, 20],                 # DEPT_HEAD
    4: [1, 5, 10, 11, 12, 13, 20, 22],                            # DORM
    5: [1, 2, 3, 6, 7, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 8, 21, 22],  # ADMIN
}
rm = []
rid = 0
for role_id, mids in ROLE_MENUS.items():
    for m in mids:
        rid += 1
        rm.append(f"({rid},{role_id},{m})")
w("INSERT INTO sys_role_menu (id,role_id,menu_id) VALUES " + ",".join(rm) + ";")
w()

DICTS = {"leave_type": ["病假", "事假", "公假", "实习", "跨省外出"],
         "leave_status": ["草稿", "待辅导员审批", "待院系审批", "请假中", "待销假", "已销假", "已驳回", "已取消", "超期未销假"],
         "transport": ["地铁", "公交", "高铁", "飞机", "私家车", "步行"],
         "late_reason": ["实习加班", "交通延误", "就医", "其他"],
         "case_type": ["超期未销假", "夜不归", "连续晚归"]}
w("INSERT INTO sys_dict (dict_type,label,value,sort) VALUES")
dv = []
for k, arr in DICTS.items():
    for i, v in enumerate(arr, 1):
        dv.append(f"({q(k)},{q(v)},{q(str(i))},{i})")
w(",\n".join(dv) + ";")
w()

# ---------------- 用户 ----------------
BCRYPT = "$2b$10$PlNwJBWik1xzE8VHIc0FH.oPzBKiJ.pGCO/Umlo6kgeXXLCAYTQoi"  # 123456
w("-- 密码统一为 123456（BCrypt），管理员 admin/admin123 单独一条")
names = ["张若曦", "李昊然", "周文琪", "赵一鸣", "孙可", "陈思远", "王梓萱", "刘子豪",
         "吴桐", "郑雨桐", "林知远", "徐若彤", "何嘉树", "曹雨晴", "谢明轩", "韩思彤",
         "朱一诺", "沈亦辰", "唐婉清", "冯子墨", "邓佳怡", "许诺", "蒋文博", "黄雅静"]
classes = ["软件工程 2201", "软件工程 2202", "软件工程 2203", "计算机科学 2201"]
dept_of = {"软件工程 2201": (1, "计算机学院"), "软件工程 2202": (1, "计算机学院"),
           "软件工程 2203": (1, "计算机学院"), "计算机科学 2201": (1, "计算机学院")}
students = []
for i, n in enumerate(names):
    cls = classes[i % 4]
    students.append({"id": 100 + i, "name": n, "no": f"s2022{i + 1:03d}", "cls": cls,
                     "dept": dept_of[cls], "avatar": f"/uploads/seed/avatar/{(i % 8) + 1:02d}.jpg",
                     "dorm": f"6-{400 + i}"})

users = []
users.append((1, "admin", "$2b$10$1YWyXmTdMpFRTGvnSZKXp.zMkHkkpV48rF9az6tRunrhrCNU5uTUy", "系统管理员", "A0001", "ADMIN", 5, "学生工作处", "-", "-", "-", "13800000001", "-", "-", "/uploads/seed/avatar/03.jpg", 1, "2026-10-31 19:02:00"))
staff = [
    (2, "t1001", "陈立", "T1001", "COUNSELOR", 1, "计算机学院", "软件工程 2201,软件工程 2202", "13900002201", "/uploads/seed/avatar/05.jpg"),
    (3, "t1002", "赵敏", "T1002", "COUNSELOR", 1, "计算机学院", "软件工程 2203,计算机科学 2201", "13900002202", "/uploads/seed/avatar/07.jpg"),
    (4, "t2001", "王志远", "T2001", "DEPT_HEAD", 1, "计算机学院", "-", "13900003302", "/uploads/seed/avatar/03.jpg"),
    (5, "d3001", "刘梅", "D3001", "DORM", 5, "学生工作处", "6 栋", "13700008801", "/uploads/seed/avatar/04.jpg"),
]
for sid, un, rn, no, rc, did, dn, cls, ph, av in staff:
    users.append((sid, un, BCRYPT, rn, no, rc, did, dn, cls, "6 栋" if rc == "DORM" else "-",
                  "101" if rc == "DORM" else "-", ph, "-", "-", av, 1, "2026-10-31 18:20:00"))
for s in students:
    users.append((s["id"], s["no"], BCRYPT, s["name"], s["no"].upper(), "STUDENT", s["dept"][0], s["dept"][1],
                  s["cls"], "6 栋", s["dorm"], "1" + str(3800000000 + s["id"])[:9], "家长", "139****" + f"{s['id']:04d}"[-4:],
                  s["avatar"], 1, "2026-10-30 21:10:00"))

w("INSERT INTO sys_user (id,username,password,real_name,user_no,role_code,dept_id,dept_name,class_name,dorm_building,dorm_room,phone,guardian_name,guardian_phone,avatar,status,last_login) VALUES")
rows = []
for u in users:
    rows.append("(" + ",".join(q(x) for x in u) + ")")
w(",\n".join(rows) + ";")
w()

# ---------------- 请假规则 ----------------
RULES = [
    ("病假", 2.0, "CITY", "诊断证明", "COUNSELOR", "病假 2 天以内仅辅导员审批"),
    ("病假", 2.0, "CITY", "诊断证明 + 病历", "COUNSELOR,DEPT", "病假超过 2 天需追加院系审批"),
    ("事假", 1.0, "CITY", "无", "COUNSELOR", "事假 1 天以内辅导员审批"),
    ("事假", 1.0, "CITY", "家长确认", "COUNSELOR,DEPT", "事假超过 1 天需院系审批"),
    ("公假", 0.0, "PROVINCE", "活动通知", "COUNSELOR,DEPT", "公假一律院系审批"),
    ("跨省外出", 0.0, "CROSS_PROVINCE", "家长确认 + 行程单", "COUNSELOR,DEPT", "跨省外出必须院系审批"),
    ("实习", 7.0, "CITY", "实习协议", "COUNSELOR,DEPT", "实习超过 7 天院系审批"),
]
w("INSERT INTO leave_rule (id,leave_type,day_threshold,out_scope,required_material,approval_level,enabled,version,effective_time,remark) VALUES")
rv = []
for i, r in enumerate(RULES, 1):
    rv.append(f"({i},{q(r[0])},{r[1]},{q(r[2])},{q(r[3])},{q(r[4])},1,'v3','2026-09-01 00:00:00',{q(r[5])})")
w(",\n".join(rv) + ";")
w()

# ---------------- 请假申请 ----------------
TYPES = ["病假", "事假", "公假", "实习", "跨省外出"]
DEST = {"病假": ["市第一人民医院 · 城东院区", "市口腔医院", "校医院转诊 · 市中心医院", "省人民医院"],
        "事假": ["校本部 · 市区", "邻市 · 家中", "市区 · 办证中心", "家中（本市）"],
        "公假": ["省体育中心", "省大学生运动会", "市会展中心", "校团委组织活动"],
        "实习": ["滨江区 · 校企合作基地", "市高新区 · 实习单位", "上海 · 实习企业"],
        "跨省外出": ["江苏省南京市", "上海浦东新区", "安徽省合肥市", "山东省济南市"]}
TRANSPORT = ["地铁", "高铁", "私家车", "公交", "飞机"]
REASONS = {"病假": "身体不适需就医复查，医生建议休息。", "事假": "家中有事需回处理，已与家长沟通。",
           "公假": "代表学院参加比赛/活动，附活动通知。", "实习": "参加校企合作实习，需连续在岗。",
           "跨省外出": "家在外省，需返乡处理家庭事务。"}
REJECT_REASON = ["证明材料不完整，请补充医院诊断证明。", "请假事由说明过于简单，请补充具体行程。",
                 "临近期末考试，非必要不建议请假。"]

base = dt.datetime(2026, 10, 31, 19, 0, 0)
apps = []
# 状态分布：覆盖全部阶段
status_plan = (["COMPLETED"] * 12 + ["ON_LEAVE"] * 4 + ["RETURN_PENDING"] * 4 + ["COUNSELOR_PENDING"] * 4 +
               ["DEPT_PENDING"] * 3 + ["REJECTED"] * 2 + ["CANCELLED"] * 1 + ["OVERDUE"] * 2 + ["DRAFT"] * 1)
random.shuffle(status_plan)
for i, st in enumerate(status_plan):
    s = students[i % len(students)]
    # 待审批单据集中到辅导员所带班级（软件 2201/2202），保证审批台有待办
    if st in ("COUNSELOR_PENDING", "DEPT_PENDING"):
        s = students[i % 4]
    lt = TYPES[i % 5] if i % 7 else "病假"
    # 时间：分散在 2026-05 ~ 2026-10
    month = 5 + (i % 6)
    day = 3 + (i * 3) % 25
    span_days = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 8.0][i % 8]
    # 让在途单据落在“当前时间”附近，历史单据分散在近 6 个月，便于看板展示
    if st in ("ON_LEAVE", "OVERDUE"):
        end = base + dt.timedelta(days=1 + i % 3)
        start = end - dt.timedelta(hours=int(span_days * 10))
    elif st == "RETURN_PENDING":
        end = base - dt.timedelta(minutes=30)
        start = end - dt.timedelta(hours=int(span_days * 10))
    elif st in ("COUNSELOR_PENDING", "DEPT_PENDING"):
        start = base + dt.timedelta(days=1, hours=(i % 6))
        end = start + dt.timedelta(hours=int(span_days * 10))
    else:
        start = dt.datetime(2026, month, day, 8 if i % 2 == 0 else 13, 0, 0)
        end = start + dt.timedelta(hours=int(span_days * 10))
    days = round((end - start).total_seconds() / 3600 / 10, 1)
    need_dept = 1 if (days > 2 or lt in ("公假", "跨省外出", "实习")) else 0
    status = st
    if status == "OVERDUE":
        status = "ON_LEAVE"
        overdue = 1
    else:
        overdue = 0
    approver = {"COUNSELOR_PENDING": (2, "陈立"), "DEPT_PENDING": (4, "王志远"),
                "ON_LEAVE": (2, "陈立"), "RETURN_PENDING": (2, "陈立"),
                "COMPLETED": (2, "陈立"), "OVERDUE": (2, "陈立"),
                "REJECTED": (2, "陈立"), "CANCELLED": (2, "陈立"), "DRAFT": (None, None)}[st]
    apps.append({
        "id": i + 1, "no": f"QJ2026{month:02d}{day:02d}{i + 1:04d}", "student": s, "type": lt,
        "start": start, "end": end, "days": days,
        "dest": DEST[lt][i % len(DEST[lt])], "transport": TRANSPORT[i % len(TRANSPORT)],
        "reason": REASONS[lt], "attach": f"/uploads/seed/proof/{(i % 6) + 1:02d}.jpg",
        "status": status, "need_dept": need_dept, "overdue": overdue,
        "approver": approver, "create": start - dt.timedelta(hours=6 + i % 12),
        "level": "COUNSELOR,DEPT" if need_dept else "COUNSELOR",
        "deadline": end + dt.timedelta(hours=2),
        "risk": round(min(96, 22 + days * 6 + (i % 5) * 7), 1),
    })

w("INSERT INTO leave_application (id,apply_no,student_id,student_name,dept_id,dept_name,class_name,leave_type,start_time,end_time,days,destination,contact_name,contact_phone,transport,reason,attachment_path,status,current_approver_id,current_approver_name,approval_level,need_dept,overdue_flag,return_deadline,risk_score,risk_level,create_time,update_time,deleted,version) VALUES")
rows = []
for a in apps:
    s = a["student"]
    risk = a["risk"]
    lvl = "HIGH" if risk >= 70 else ("MID" if risk >= 40 else "LOW")
    rows.append("(" + ",".join(q(x) for x in [
        a["id"], a["no"], s["id"], s["name"], s["dept"][0], s["dept"][1], s["cls"], a["type"],
        ts(a["start"]), ts(a["end"]), a["days"], a["dest"], "家长 / 辅导员", "138****" + f"{a['id']:04d}",
        a["transport"], a["reason"], a["attach"], a["status"], a["approver"][0], a["approver"][1] or "",
        a["level"], a["need_dept"], a["overdue"], ts(a["deadline"]), risk, lvl,
        ts(a["create"]), ts(a["create"] + dt.timedelta(hours=5 + a["id"] % 20)), 0, a["id"] % 3]) + ")")
w(",\n".join(rows) + ";")
w()

# 审批记录
w("INSERT INTO leave_approval (leave_id,node,approver_id,approver_name,action,opinion,create_time) VALUES")
av = []
for a in apps:
    if a["status"] in ("DRAFT", "CANCELLED"):
        continue
    t1 = a["create"] + dt.timedelta(hours=2 + a["id"] % 6)
    if a["status"] == "REJECTED":
        av.append(f"({a['id']},'COUNSELOR',2,'陈立','REJECT',{q(REJECT_REASON[a['id'] % 3])},{q(ts(t1))})")
        continue
    av.append(f"({a['id']},'COUNSELOR',2,'陈立','APPROVE',{q('情况属实，同意请假。')},{q(ts(t1))})")
    if a["need_dept"] and a["status"] in ("DEPT_PENDING", "ON_LEAVE", "RETURN_PENDING", "COMPLETED"):
        if a["status"] == "DEPT_PENDING":
            pass
        else:
            t2 = t1 + dt.timedelta(hours=4 + a["id"] % 12)
            av.append(f"({a['id']},'DEPT',4,'王志远','APPROVE',{q('已核家长，同意。')},{q(ts(t2))})")
w(",\n".join(av) + ";")
w()

# 延期
w("INSERT INTO leave_extension (leave_id,old_end_time,new_end_time,add_days,reason,status,approver_id,approver_name,apply_time,approve_time,opinion) VALUES")
ev = []
ext_apps = [a for a in apps if a["status"] in ("ON_LEAVE", "COMPLETED", "RETURN_PENDING")][:6]
for i, a in enumerate(ext_apps):
    st = ["APPROVED", "PENDING", "REJECTED"][i % 3]
    nr = a["end"] + dt.timedelta(days=1 + i % 2)
    ev.append(f"({a['id']},{q(ts(a['end']))},{q(ts(nr))},1.5,{q('治疗未结束，需延长休假。')},{q(st)},2,'陈立',{q(ts(a['end'] - dt.timedelta(hours=3)))},{q(ts(a['end'] - dt.timedelta(hours=1))) if st != 'PENDING' else 'NULL'},{q('同意延期，注意按时销假。') if st != 'PENDING' else 'NULL'})")
w(",\n".join(ev) + ";")
w()

# 销假记录
w("INSERT INTO return_record (leave_id,apply_no,student_id,student_name,return_code,code_expire,verify_type,verifier_id,verifier_name,verify_time,status,remark,create_time) VALUES")
rv = []
done_apps = [a for a in apps if a["status"] == "COMPLETED"]
for i, a in enumerate(done_apps):
    vt = a["end"] + dt.timedelta(minutes=30 + i * 7)
    code = f"{420000 + i * 137}"
    rv.append(f"({a['id']},{q(a['no'])},{a['student']['id']},{q(a['student']['name'])},{q(code)},{q(ts(vt + dt.timedelta(minutes=10)))},'CODE',5,'刘梅',{q(ts(vt))},'VERIFIED',{q('扫码核验通过，未超期。')},{q(ts(vt - dt.timedelta(minutes=14)))})")
# 未核销的待销假
for i, a in enumerate([x for x in apps if x["status"] == "RETURN_PENDING"]):
    code = f"{510000 + i * 211}"
    rv.append(f"({a['id']},{q(a['no'])},{a['student']['id']},{q(a['student']['name'])},{q(code)},{q(ts(a['end'] + dt.timedelta(minutes=10)))},NULL,NULL,NULL,NULL,'PENDING',{q('已生成返校码，等待宿管核验。')},{q(ts(a['end'] - dt.timedelta(minutes=5)))})")
w(",\n".join(rv) + ";")
w()

# 晚归
w("INSERT INTO late_return (student_id,student_name,dept_id,dept_name,class_name,dorm,return_time,reason,has_leave,leave_id,is_violation,remark,image_path,recorder_id,recorder_name,record_time,create_time) VALUES")
lv = []
late_reasons = ["实习加班", "交通延误", "就医", "其他"]
for i in range(34):
    s = students[(i * 3) % 24]
    day = 5 + (i * 2) % 26
    month = 7 + (i % 4)
    rt = dt.datetime(2026, month, day, 21 + (i % 3), (i * 7) % 60, 0)
    has_leave = 1 if i % 3 == 0 else 0
    lid = apps[i % len(apps)]["id"] if has_leave else None
    lv.append("(" + ",".join(q(x) for x in [
        s["id"], s["name"], s["dept"][0], s["dept"][1], s["cls"], "6 栋 " + s["dorm"],
        ts(rt), late_reasons[i % 4], has_leave, lid, 0 if has_leave else 1,
        "已出示请假单，口头提醒按时返寝。" if has_leave else "未说明具体原因，已记录并通知辅导员。",
        f"/uploads/seed/proof/{(i % 6) + 1:02d}.jpg", 5, "刘梅", ts(rt + dt.timedelta(minutes=4)),
        ts(rt + dt.timedelta(minutes=4))]) + ")")
w(",\n".join(lv) + ";")
w()

# 未归核查工单
w("INSERT INTO absence_case (case_no,student_id,student_name,dept_id,dept_name,class_name,case_type,level,trigger_desc,status,owner_id,owner_name,deadline,close_time,create_time,update_time) VALUES")
cv = []
case_defs = [("OVERDUE", "超期未销假", "HIGH", "请假结束 24 小时未提交销假"),
             ("NIGHT_ABSENT", "夜不归", "HIGH", "23:30 未返寝且无有效请假"),
             ("REPEAT_LATE", "连续晚归", "MID", "近 14 天晚归 3 次")]
for i in range(12):
    ct, cn, lvl, desc = case_defs[i % 3]
    s = students[(i * 5) % 24]
    st = ["PENDING", "PROCESSING", "CLOSED"][i % 3]
    create = dt.datetime(2026, 10, 2 + i * 2, 20, 0, 0)
    cv.append("(" + ",".join(q(x) for x in [
        f"YC2026{10:02d}{i + 1:04d}", s["id"], s["name"], s["dept"][0], s["dept"][1], s["cls"],
        ct, lvl, desc, st, 2, "陈立", ts(create + dt.timedelta(days=2)),
        ts(create + dt.timedelta(days=1, hours=3)) if st == "CLOSED" else None,
        ts(create), ts(create + dt.timedelta(hours=6))]) + ")")
w(",\n".join(cv) + ";")
w()

# 关怀记录
w("INSERT INTO care_record (case_id,student_id,student_name,care_way,content,result,recorder_id,recorder_name,record_time,create_time) VALUES")
crv = []
ways = ["PHONE", "PARENT", "VISIT", "PEER"]
for i in range(14):
    s = students[(i * 4) % 24]
    t = dt.datetime(2026, 10, 3 + i * 2, 19, 30, 0)
    crv.append("(" + ",".join(q(x) for x in [
        (i % 12) + 1, s["id"], s["name"], ways[i % 4],
        "学生称在返程途中，情绪平稳，已提醒注意安全。" if i % 2 == 0 else "家长确认学生已离校返乡，明日返校。",
        "要求 22:00 前到楼并生成返校码，次日上午补交凭证。" if i % 2 == 0 else "已登记家长联系方式，纳入重点关注名单。",
        2, "陈立", ts(t), ts(t)]) + ")")
w(",\n".join(crv) + ";")
w()

# ---------------- 创新点规则与结果 ----------------
w("INSERT INTO risk_rule (name,version,w_freq,w_days,w_late,w_overdue,w_type,w_reject,low_threshold,high_threshold,enabled,effective_time,create_by,create_time) VALUES")
w("('请假行为风险分层规则','v1',25.00,25.00,20.00,20.00,5.00,5.00,40.0,70.0,0,'2026-03-01 00:00:00','admin','2026-03-01 09:00:00'),")
w("('请假行为风险分层规则','v2',25.00,20.00,20.00,25.00,5.00,5.00,40.0,70.0,0,'2026-06-15 00:00:00','admin','2026-06-15 09:00:00'),")
w("('请假行为风险分层规则','v3',20.00,20.00,20.00,25.00,10.00,5.00,40.0,70.0,1,'2026-09-01 00:00:00','admin','2026-09-01 09:00:00');")
w()

w("INSERT INTO risk_score (student_id,student_name,class_name,rule_version,snapshot,detail_json,total_score,level,suggest,adjust_level,adjust_reason,adjust_by,adjust_time,calc_time) VALUES")
sv = []
for i, s in enumerate(students):
    freq = 1 + (i * 3) % 6
    dys = round(2 + (i * 7) % 22 + 0.5, 1)
    late = (i * 2) % 5
    over = i % 4
    reject = i % 3
    # 简化同算法：归一化后乘权重
    f_n = min(freq / 8, 1); d_n = min(dys / 30, 1); l_n = min(late / 6, 1)
    o_n = min(over / 4, 1); t_n = 0.6 if i % 5 == 4 else 0.2; r_n = min(reject / 3, 1)
    total = round(f_n * 20 + d_n * 20 + l_n * 20 + o_n * 25 + t_n * 10 + r_n * 5, 1)
    lvl = "HIGH" if total >= 70 else ("MID" if total >= 40 else "LOW")
    snap = '{"freq":%d,"days":%.1f,"late":%d,"overdue":%d,"type":"%s","reject":%d}' % (freq, dys, late, over, apps[i]["type"], reject)
    detail = '{"freq":%.1f,"days":%.1f,"late":%.1f,"overdue":%.1f,"type":%.1f,"reject":%.1f}' % (
        f_n * 20, d_n * 20, l_n * 20, o_n * 25, t_n * 10, r_n * 5)
    sug = ("建议纳入重点关注，安排一次当面访谈并联系家长。" if lvl == "HIGH" else
           ("建议关注其请假规律，提醒按时销假。" if lvl == "MID" else "当前行为平稳，保持常规关注即可。"))
    adj = "MID" if lvl == "HIGH" and i % 7 == 0 else None
    sv.append("(" + ",".join(q(x) for x in [
        s["id"], s["name"], s["cls"], "v3", snap, detail, total, lvl, sug, adj,
        "学生已说明家庭原因，人工下调一级。" if adj else None, "陈立" if adj else None,
        ts(dt.datetime(2026, 10, 30, 9, 0, 0)) if adj else None,
        ts(dt.datetime(2026, 10, 30, 8, 0, 0))]) + ")")
w(",\n".join(sv) + ";")
w()

# 消息 & 日志
w("INSERT INTO sys_message (title,content,type,biz_no,biz_id,receiver_id,is_read,create_time) VALUES")
mv = []
for i, a in enumerate(apps[:12]):
    mv.append(f"({q('新的请假申请待审批')},{q(a['no'] + ' 由 ' + a['student']['name'] + ' 提交，请及时处理。')},'APPROVAL',{q(a['no'])},{a['id']},2,{i % 2},{q(ts(a['create'] + dt.timedelta(minutes=1)))})")
for i in range(4):
    mv.append(f"({q('超期未销假预警')},{q('有 2 条请假已超过应销假时间，请核查。')},'OVERDUE','-',NULL,2,0,{q(ts(dt.datetime(2026, 10, 30, 9, 0, 0)))})")
mv.append(f"({q('返校码核验成功')},{q('张若曦的返校码已由宿管核验，销假完成。')},'SYSTEM','QJ202610280012',1,101,1,{q(ts(dt.datetime(2026, 10, 30, 19, 12, 0)))})")
w(",\n".join(mv) + ";")
w()

w("INSERT INTO sys_log (user_id,user_name,module,action,biz_no,before_status,after_status,reason,ip,create_time) VALUES")
lgv = []
for a in apps[:16]:
    lgv.append(f"(2,'陈立','请假审批','APPROVE',{q(a['no'])},'COUNSELOR_PENDING','{a['status']}',{q('情况属实，同意请假。')},'192.168.1.22',{q(ts(a['create'] + dt.timedelta(hours=3)))})")
lgv.append("(1,'admin','规则配置','PUBLISH','RISK-v3','v2','v3','调整逾期销假权重至 25%','192.168.1.10','2026-09-01 09:00:00')")
w(",\n".join(lgv) + ";")
w()

w("INSERT INTO sys_file (file_name,path,size,content_type,biz_type,uploader_id,create_time) VALUES")
fv = []
for i in range(6):
    fv.append(f"({q('诊断证明-%02d.jpg' % (i + 1))},{q('/uploads/seed/proof/%02d.jpg' % (i + 1))},{120000 + i * 9000},'image/jpeg','PROOF',101,{q(ts(dt.datetime(2026, 10, 20 + i, 10, 0, 0)))})")
for i in range(8):
    fv.append(f"({q('avatar-%02d.jpg' % (i + 1))},{q('/uploads/seed/avatar/%02d.jpg' % (i + 1))},130000,'image/jpeg','AVATAR',101,{q(ts(dt.datetime(2026, 10, 1, 9, 0, 0)))})")
w(",\n".join(fv) + ";")
w()
w("SET FOREIGN_KEY_CHECKS = 1;")

OUT.write_text("\n".join(L))
print("init.sql", OUT.stat().st_size // 1024, "KB", len(L), "lines", "apps", len(apps))
