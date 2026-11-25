import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('./views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('./layout/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: () => import('./views/Dashboard.vue'), meta: { title: '工作台' } },
      { path: 'leave/list', component: () => import('./views/LeaveList.vue'), meta: { title: '请假记录' } },
      { path: 'leave/create', component: () => import('./views/LeaveForm.vue'), meta: { title: '发起请假' } },
      { path: 'leave/edit/:id', component: () => import('./views/LeaveForm.vue'), meta: { title: '编辑请假' } },
      { path: 'leave/detail/:id', component: () => import('./views/LeaveDetail.vue'), meta: { title: '请假详情' } },
      { path: 'leave/return', component: () => import('./views/ReturnVerify.vue'), meta: { title: '返校销假' } },
      { path: 'approval/desk', component: () => import('./views/ApprovalDesk.vue'), meta: { title: '审批工作台' } },
      { path: 'approval/dept', component: () => import('./views/ApprovalDesk.vue'), meta: { title: '院系审批' } },
      { path: 'safety/late', component: () => import('./views/LateRegister.vue'), meta: { title: '晚归登记' } },
      { path: 'safety/cases', component: () => import('./views/CaseList.vue'), meta: { title: '未归核查' } },
      { path: 'safety/care', component: () => import('./views/CareList.vue'), meta: { title: '关怀记录' } },
      { path: 'stats', component: () => import('./views/Stats.vue'), meta: { title: '统计分析' } },
      { path: 'risk/center', component: () => import('./views/RiskCenter.vue'), meta: { title: '风险分层' } },
      { path: 'admin/rules', component: () => import('./views/RuleConfig.vue'), meta: { title: '规则配置' } },
      { path: 'admin/users', component: () => import('./views/UserList.vue'), meta: { title: '用户管理' } },
      { path: 'admin/roles', component: () => import('./views/RoleList.vue'), meta: { title: '角色管理' } },
      { path: 'admin/menus', component: () => import('./views/MenuList.vue'), meta: { title: '菜单管理' } },
      { path: 'profile', component: () => import('./views/Profile.vue'), meta: { title: '个人中心' } }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) return '/login'
  if (to.path === '/login' && token) return '/dashboard'
  return true
})

export default router
