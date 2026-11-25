<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>个人中心</h1>
        <p>账号 {{ store.user?.username }} · 最近登录 {{ formatTime(store.user?.lastLogin) }}</p>
      </div>
      <div class="head-actions">
        <el-button type="primary" :loading="saving" @click="save">保存修改</el-button>
      </div>
    </div>

    <div class="grid2">
      <div class="card">
        <div class="card-title">基本资料</div>
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px">
          <el-avatar :size="64" :src="form.avatar || '/uploads/seed/avatar/01.jpg'" />
          <div>
            <el-upload :action="uploadUrl" :headers="headers" name="file" :show-file-list="false" :on-success="onAvatar" accept=".jpg,.jpeg,.png">
              <el-button size="small">更换头像</el-button>
            </el-upload>
            <div class="hint mt8">JPG / PNG ≤ 10MB，上传后右上角同步显示</div>
          </div>
        </div>
        <el-form :model="form" label-width="96px">
          <el-form-item label="姓名"><el-input v-model="form.realName" style="width:280px" /></el-form-item>
          <el-form-item label="学号/工号"><el-input :model-value="store.user?.userNo" disabled style="width:280px" /></el-form-item>
          <el-form-item label="院系班级"><el-input :model-value="`${store.user?.deptName || ''} / ${store.user?.className || ''}`" disabled style="width:340px" /></el-form-item>
          <el-form-item label="联系电话"><el-input v-model="form.phone" style="width:280px" /></el-form-item>
          <el-form-item label="紧急联系人"><el-input v-model="form.guardianName" style="width:280px" /></el-form-item>
          <el-form-item label="联系人电话"><el-input v-model="form.guardianPhone" style="width:280px" /></el-form-item>
        </el-form>
      </div>

      <div>
        <div class="card">
          <div class="card-title">修改密码</div>
          <el-form label-width="96px">
            <el-form-item label="原密码"><el-input v-model="pwd.oldPassword" type="password" show-password style="width:280px" /></el-form-item>
            <el-form-item label="新密码"><el-input v-model="pwd.newPassword" type="password" show-password style="width:280px" /></el-form-item>
            <el-form-item label="确认新密码"><el-input v-model="pwd.confirm" type="password" show-password style="width:280px" /></el-form-item>
            <el-form-item><el-button type="primary" @click="changePwd">修改密码</el-button></el-form-item>
          </el-form>
          <div class="hint">密码使用 BCrypt 存储，任何接口与日志都不会返回密码字段。</div>
        </div>

        <div class="card">
          <div class="card-title">我的角色与数据范围</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="角色">{{ store.user?.roleCode }}</el-descriptions-item>
            <el-descriptions-item label="数据范围">
              {{ { STUDENT: '本人', COUNSELOR: '所带班级', DEPT_HEAD: '本院系', DORM: '本院系 / 楼栋', ADMIN: '全校' }[store.user?.roleCode] }}
            </el-descriptions-item>
            <el-descriptions-item label="宿舍">{{ store.user?.dormBuilding }} {{ store.user?.dormRoom }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { loadUser, setAvatar, store } from '../store'
import { formatTime } from '../utils'

const form = ref({ realName: '', phone: '', guardianName: '', guardianPhone: '', avatar: '' })
const pwd = ref({ oldPassword: '', newPassword: '', confirm: '' })
const saving = ref(false)
const uploadUrl = '/api/upload'
const headers = computed(() => ({ Authorization: 'Bearer ' + localStorage.getItem('token') }))

async function save() {
  saving.value = true
  try {
    await api.updateProfile(form.value)
    await loadUser(true)
    ElMessage.success('资料已保存')
  } finally {
    saving.value = false
  }
}
async function onAvatar(res) {
  if (res.code === 200) {
    form.value.avatar = res.data.path
    await api.updateProfile({ avatar: res.data.path })
    setAvatar(res.data.path)
    await loadUser(true)
    ElMessage.success('头像已更新')
  }
}
async function changePwd() {
  if (pwd.value.newPassword !== pwd.value.confirm) return ElMessage.warning('两次输入的新密码不一致')
  if (pwd.value.newPassword.length < 6) return ElMessage.warning('新密码不少于 6 位')
  await api.changePassword({ oldPassword: pwd.value.oldPassword, newPassword: pwd.value.newPassword })
  ElMessage.success('密码已修改')
  pwd.value = { oldPassword: '', newPassword: '', confirm: '' }
}
onMounted(() => {
  const u = store.user || {}
  form.value = { realName: u.realName, phone: u.phone, guardianName: u.guardianName, guardianPhone: u.guardianPhone, avatar: u.avatar }
})
</script>
