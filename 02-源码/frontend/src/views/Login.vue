<template>
  <div class="login">
    <div class="left">
      <div class="bg"></div>
      <div class="brandline">
        <span class="dot">勤</span>
        <span>学生安全请假平台</span>
      </div>
      <div class="slogan">
        <h2>请假有据<br />返校有码<br />安全有数</h2>
        <p>从请假申请、分级审批、限时返校码，到晚归核查与关怀记录，形成学生外出安全管理的完整闭环。</p>
        <div class="badges">
          <span>分级审批</span><span>限时返校码</span><span>晚归核查</span><span>行为风险分层</span>
        </div>
      </div>
      <div class="duty">
        <div>技术支持：信息中心 · 值班电话 0571-8888 0000</div>
        <div class="hint" style="color:#8FA0B2">建议使用 Chrome / Edge 浏览器，移动端支持请假与审批</div>
      </div>
    </div>

    <div class="right">
      <div class="box">
        <div class="tabs">
          <span class="on">账号登录</span>
          <span class="off">扫码登录（移动端）</span>
        </div>
        <h3>欢迎回来</h3>
        <p class="sub">请使用学号 / 工号登录，连续 5 次失败将锁定 10 分钟</p>
        <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent>
          <el-form-item prop="username">
            <el-input v-model="form.username" size="large" placeholder="学号 / 工号" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" size="large" type="password" show-password placeholder="登录密码"
              :prefix-icon="Lock" @keyup.enter="submit" />
          </el-form-item>
          <div class="rows">
            <el-checkbox v-model="remember">记住账号</el-checkbox>
            <a @click="tip">忘记密码</a>
          </div>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="submit">登 录</el-button>
        </el-form>
        <div class="quick">
          <div class="hint">一键填充测试账号</div>
          <div class="chips">
            <span v-for="a in accounts" :key="a.username" @click="fill(a)">{{ a.label }}</span>
          </div>
        </div>
        <div class="foot hint">登录即表示同意《学生外出安全管理规定》· 数据仅用于校内安全管理</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { api } from '../api'
import { loadUser } from '../store'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const remember = ref(true)
const form = ref({ username: 's2022001', password: '123456' })

const accounts = [
  { label: '学生', username: 's2022001', password: '123456' },
  { label: '辅导员', username: 't1001', password: '123456' },
  { label: '院系负责人', username: 't2001', password: '123456' },
  { label: '宿管', username: 'd3001', password: '123456' },
  { label: '管理员', username: 'admin', password: 'admin123' }
]

const rules = {
  username: [{ required: true, message: '请输入学号或工号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const fill = (a) => {
  form.value = { username: a.username, password: a.password }
}
const tip = () => ElMessage.info('请联系辅导员或信息中心重置密码')

async function submit() {
  await formRef.value.validate()
  loading.value = true
  try {
    const data = await api.login(form.value)
    localStorage.setItem('token', data.token)
    await loadUser(true)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login { min-height: 100vh; display: grid; grid-template-columns: 1.05fr .95fr; background: #fff; }
.left { position: relative; background: #16202C; color: #fff; padding: 56px 64px; display: flex;
  flex-direction: column; justify-content: space-between; overflow: hidden; }
.bg { position: absolute; inset: 0; background: url('/login-bg.jpg') center/cover no-repeat; opacity: .32;
  filter: saturate(.85); }
.left > * { position: relative; }
.brandline { display: flex; align-items: center; gap: 10px; font-weight: 600; letter-spacing: .5px; }
.brandline .dot { width: 26px; height: 26px; border-radius: 5px; background: #2F6B8A; display: grid; place-items: center; font-size: 13px; }
.slogan h2 { font-size: 34px; line-height: 1.32; letter-spacing: 2px; margin: 0; font-weight: 600; }
.slogan p { color: #A9B7C6; margin: 16px 0 0; max-width: 430px; line-height: 1.9; font-size: 13px; }
.badges { display: flex; gap: 10px; margin-top: 26px; flex-wrap: wrap; }
.badges span { border: 1px solid #ffffff26; border-radius: 20px; padding: 5px 14px; font-size: 12px; color: #C9D2DC; }
.duty { border-top: 1px solid #ffffff1a; padding-top: 18px; font-size: 12px; color: #9BA9B8; display: grid; gap: 6px; }
.right { display: grid; place-items: center; padding: 40px; }
.box { width: 356px; }
.tabs { display: flex; gap: 22px; border-bottom: 1px solid #E3E8EF; margin-bottom: 22px; font-size: 13px; }
.tabs span { padding-bottom: 9px; }
.tabs .on { color: #1F2937; font-weight: 600; border-bottom: 2px solid #1F2937; }
.tabs .off { color: #9AA8B6; }
h3 { font-size: 21px; margin: 0 0 6px; }
.sub { color: #6B7785; font-size: 12px; margin: 0 0 22px; }
.rows { display: flex; justify-content: space-between; align-items: center; font-size: 12px; margin: -4px 0 16px; color: #6B7785; }
.quick { margin-top: 22px; border-top: 1px dashed #E3E8EF; padding-top: 14px; }
.chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.chips span { border: 1px solid #E3E8EF; border-radius: 14px; padding: 4px 12px; font-size: 12px; cursor: pointer; color: #3B4A5A; background: #FBFCFE; }
.chips span:hover { border-color: #2F6B8A; color: #2F6B8A; }
.foot { margin-top: 18px; text-align: center; }
</style>
