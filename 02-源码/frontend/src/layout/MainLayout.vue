<template>
  <div class="layout">
    <aside class="sidebar" :class="{ collapsed: collapsed }">
      <div class="brand">
        <span class="dot">勤</span>
        <span v-if="!collapsed">学生安全请假平台</span>
      </div>
      <el-menu :default-active="route.path" :collapse="collapsed" router unique-opened>
        <template v-for="m in menus" :key="m.id">
          <el-sub-menu v-if="m.children && m.children.length" :index="m.path || String(m.id)">
            <template #title>
              <el-icon><component :is="iconOf(m.name)" /></el-icon>
              <span>{{ m.name }}</span>
            </template>
            <el-menu-item v-for="c in m.children" :key="c.id" :index="c.path">
              <el-icon><component :is="iconOf(c.name)" /></el-icon>
              <span>{{ c.name }}</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="m.path">
            <el-icon><component :is="iconOf(m.name)" /></el-icon>
            <span>{{ m.name }}</span>
          </el-menu-item>
        </template>
      </el-menu>
      <div class="side-foot">
        <span v-if="!collapsed">v1.0 · {{ roleText }}</span>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="row-left">
          <el-icon class="collapse-btn" @click="collapsed = !collapsed"><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
          <span class="crumb">首页 / <b>{{ route.meta.title || '' }}</b></span>
        </div>
        <div class="topright">
          <el-popover placement="bottom-end" width="320" trigger="click" @show="loadMessages">
            <template #reference>
              <span class="bell">
                <el-icon><Bell /></el-icon>
                <i v-if="unread > 0">{{ unread }}</i>
              </span>
            </template>
            <div class="msg-head">站内消息</div>
            <div v-if="messages.length === 0" class="hint" style="padding:10px 0">暂无新消息</div>
            <div v-for="m in messages" :key="m.id" class="msg-item" @click="openMsg(m)">
              <div class="msg-title">{{ m.title }}</div>
              <div class="msg-body">{{ m.content }}</div>
              <div class="hint">{{ formatTime(m.createTime) }}</div>
            </div>
          </el-popover>
          <span class="who" @click="$router.push('/profile')">
            <img class="ava" :src="store.user?.avatar || '/uploads/seed/avatar/01.jpg'" alt="头像" />
            <span>{{ store.user?.realName }} · {{ roleText }}</span>
          </span>
          <el-button link @click="doLogout">退出</el-button>
        </div>
      </header>
      <div class="content">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { loadUser, logout, store } from '../store'
import { formatTime } from '../utils'

const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const messages = ref([])
const unread = ref(0)

const menus = computed(() => store.menus)
const roleText = computed(() => ({
  STUDENT: '学生', COUNSELOR: '辅导员', DEPT_HEAD: '院系负责人', DORM: '宿管值班员', ADMIN: '管理员'
}[store.user?.roleCode] || ''))

const ICONS = {
  工作台: 'Odometer', 请假管理: 'Tickets', 我的请假: 'List', 发起请假: 'CirclePlus', 返校销假: 'CircleCheck',
  审批中心: 'Stamp', 审批工作台: 'Stamp', 批量审批: 'Finished', 院系审批: 'OfficeBuilding',
  安全管理: 'Warning', 晚归登记: 'Clock', 未归核查: 'WarningFilled', 关怀记录: 'ChatLineSquare',
  统计分析: 'DataAnalysis', 规则配置: 'Setting', 用户管理: 'User', 角色管理: 'Avatar', 菜单管理: 'Menu',
  个人中心: 'UserFilled'
}
const iconOf = (name) => ICONS[name] || 'Document'

async function loadMessages() {
  const page = await api.messages({ page: 1, size: 6 })
  messages.value = page.records || []
  unread.value = messages.value.filter((m) => m.isRead === 0).length
}

async function openMsg(m) {
  if (m.isRead === 0) {
    await api.messageRead(m.id)
    m.isRead = 1
    unread.value = Math.max(0, unread.value - 1)
  }
  if (m.bizId) router.push('/leave/detail/' + m.bizId)
}

async function doLogout() {
  await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
  logout()
  ElMessage.success('已退出')
  router.push('/login')
}

onMounted(async () => {
  await loadUser(true)
  loadMessages()
})
</script>

<style scoped>
.row-left { display: flex; align-items: center; gap: 14px; }
.collapse-btn { cursor: pointer; color: #6B7785; font-size: 16px; }
.bell { position: relative; cursor: pointer; display: flex; color: #6B7785; font-size: 16px; }
.bell i { position: absolute; top: -6px; right: -8px; background: #B3261E; color: #fff; font-size: 9px;
  border-radius: 8px; padding: 0 4px; font-style: normal; line-height: 14px; }
.side-foot { padding: 12px 16px; font-size: 11px; color: #7C8798; border-top: 1px solid #ffffff14; white-space: nowrap; }
.msg-head { font-weight: 600; margin-bottom: 6px; }
.msg-item { padding: 8px 0; border-bottom: 1px solid #EEF2F6; cursor: pointer; }
.msg-item:hover { background: #F9FBFD; }
.msg-title { font-size: 13px; font-weight: 500; }
.msg-body { font-size: 12px; color: #6B7785; margin: 2px 0; }
</style>
