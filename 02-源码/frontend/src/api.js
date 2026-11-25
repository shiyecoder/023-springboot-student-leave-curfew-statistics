import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api', timeout: 20000 })

http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = 'Bearer ' + token
  return cfg
})

http.interceptors.response.use(
  (res) => {
    if (res.config.responseType === 'blob') return res
    const body = res.data
    if (body && body.code === 200) return body.data
    if (body && body.code === 401) {
      localStorage.removeItem('token')
      location.href = '/login'
      return Promise.reject(new Error(body.msg))
    }
    ElMessage.error(body?.msg || '请求失败')
    return Promise.reject(new Error(body?.msg || '请求失败'))
  },
  (err) => {
    const status = err.response?.status
    if (status === 401) {
      localStorage.removeItem('token')
      location.href = '/login'
    } else {
      ElMessage.error(err.response?.data?.msg || err.message || '网络异常')
    }
    return Promise.reject(err)
  }
)

export default http
export const api = {
  login: (d) => http.post('/auth/login', d),
  me: () => http.get('/auth/me'),
  updateProfile: (d) => http.put('/auth/profile', d),
  changePassword: (d) => http.post('/auth/password', d),
  menus: () => http.get('/auth/menus'),

  leavePage: (p) => http.get('/student-leave/page', { params: p }),
  leaveDetail: (id) => http.get('/student-leave/' + id),
  leaveCreate: (d) => http.post('/student-leave', d),
  leaveUpdate: (id, d) => http.put('/student-leave/' + id, d),
  leaveTransition: (id, d) => http.post(`/student-leave/${id}/transition`, d),
  leaveExtend: (id, d) => http.post(`/student-leave/${id}/extension`, d),
  approveExtension: (id, d) => http.post(`/student-leave/extension/${id}/approve`, d),
  leaveEvaluate: (id) => http.post(`/student-leave/${id}/evaluate`),
  leaveOptions: () => http.get('/student-leave/options'),
  dashboard: (range) => http.get('/student-leave/dashboard', { params: { range } }),

  latePage: (p) => http.get('/late/page', { params: p }),
  lateAdd: (d) => http.post('/late', d),
  returnPage: (p) => http.get('/return/page', { params: p }),
  returnVerify: (code) => http.post('/return/verify', { code }),
  returnManual: (id, remark) => http.post(`/return/${id}/manual`, { remark }),
  casePage: (p) => http.get('/case/page', { params: p }),
  caseClose: (id, remark) => http.post(`/case/${id}/close`, { remark }),
  caseCreate: (d) => http.post('/case', d),
  carePage: (p) => http.get('/care/page', { params: p }),
  careAdd: (d) => http.post('/care', d),
  studentOptions: (keyword) => http.get('/student/options', { params: { keyword } }),

  ruleList: () => http.get('/rule/list'),
  ruleSave: (d) => http.post('/rule', d),
  riskRules: () => http.get('/risk/rule/list'),
  riskRuleCurrent: () => http.get('/risk/rule/current'),
  riskRulePublish: (d) => http.post('/risk/rule', d),
  riskScorePage: (p) => http.get('/risk/score/page', { params: p }),
  riskScoreDetail: (id) => http.get('/risk/score/' + id),
  riskEvaluate: (studentId) => http.post(`/risk/score/${studentId}/evaluate`),
  riskAdjust: (id, d) => http.post(`/risk/score/${id}/adjust`, d),

  userPage: (p) => http.get('/user/page', { params: p }),
  userSave: (d) => (d.id ? http.put('/user/' + d.id, d) : http.post('/user', d)),
  userReset: (id) => http.post(`/user/${id}/reset`),
  userDelete: (id) => http.delete('/user/' + id),
  roleList: () => http.get('/role/list'),
  roleMenus: (id) => http.get(`/role/${id}/menus`),
  roleAssign: (id, ids) => http.post(`/role/${id}/menus`, ids),
  menuTree: () => http.get('/menu/tree'),
  menuSave: (d) => http.post('/menu', d),
  dict: (t) => http.get('/dict/' + t),
  messages: (p) => http.get('/message/page', { params: p }),
  messageRead: (id) => http.post(`/message/${id}/read`),
  uploadUrl: '/api/upload'
}
