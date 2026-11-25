// 全局格式化与状态映射：全系统统一调用，禁止页面各自实现
export function formatTime(v) {
  if (!v) return '-'
  const s = String(v).replace('T', ' ')
  return s.length >= 19 ? s.slice(0, 19) : s
}

export function formatDate(v) {
  if (!v) return '-'
  return formatTime(v).slice(0, 10)
}

export const STATUS_MAP = {
  DRAFT: { text: '草稿', type: 'info' },
  COUNSELOR_PENDING: { text: '待辅导员审批', type: 'warning' },
  DEPT_PENDING: { text: '待院系审批', type: 'warning' },
  ON_LEAVE: { text: '请假中', type: 'primary' },
  RETURN_PENDING: { text: '待销假', type: 'warning' },
  COMPLETED: { text: '已销假', type: 'success' },
  REJECTED: { text: '已驳回', type: 'danger' },
  CANCELLED: { text: '已取消', type: 'info' },
  OVERDUE: { text: '超期未销假', type: 'danger' }
}

export function statusMeta(s) {
  return STATUS_MAP[s] || { text: s || '-', type: 'info' }
}

export const LEVEL_MAP = {
  LOW: { text: '低关注', type: 'success' },
  MID: { text: '中关注', type: 'warning' },
  HIGH: { text: '高关注', type: 'danger' }
}

export function levelMeta(l) {
  return LEVEL_MAP[l] || { text: l || '-', type: 'info' }
}

export const CASE_TYPE = { OVERDUE: '超期未销假', NIGHT_ABSENT: '夜不归', REPEAT_LATE: '连续晚归' }
export const CARE_WAY = { PHONE: '电话联系学生', PARENT: '联系家长', VISIT: '宿舍走访', PEER: '同学侧面了解' }
export const CASE_STATUS = { PENDING: { text: '待处理', type: 'warning' }, PROCESSING: { text: '处理中', type: 'primary' }, CLOSED: { text: '已闭环', type: 'success' } }

export function calcDays(start, end) {
  if (!start || !end) return 0
  const a = new Date(String(start).replace(' ', 'T'))
  const b = new Date(String(end).replace(' ', 'T'))
  const hours = (b - a) / 3600000
  return hours > 0 ? Math.round((hours / 10) * 10) / 10 : 0
}

export function hasPerm(codes, code) {
  return true // 按钮级权限：由后端接口二次校验，前端仅做展示控制
}
