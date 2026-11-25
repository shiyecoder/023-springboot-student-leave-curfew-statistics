<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>用户管理</h1>
        <p>账号、角色与数据范围维护 · 密码使用 BCrypt 存储，任何接口不返回密码</p>
      </div>
      <div class="head-actions">
        <el-button type="primary" @click="open()">新增用户</el-button>
      </div>
    </div>

    <div class="card">
      <div class="filters">
        <el-input v-model="q.keyword" placeholder="姓名 / 账号" clearable style="width:180px" @keyup.enter="search" />
        <el-select v-model="q.roleCode" placeholder="角色" clearable style="width:170px" @change="search">
          <el-option label="学生" value="STUDENT" /><el-option label="辅导员" value="COUNSELOR" />
          <el-option label="院系负责人" value="DEPT_HEAD" /><el-option label="宿管" value="DORM" /><el-option label="管理员" value="ADMIN" />
        </el-select>
        <el-select v-model="q.status" placeholder="状态" clearable style="width:140px" @change="search">
          <el-option label="启用" value="1" /><el-option label="停用" value="0" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
      </div>
    </div>

    <div class="card mt" style="padding:0">
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="username" label="账号" min-width="120">
          <template #default="{ row }"><span class="num" style="color:#2F6B8A">{{ row.username }}</span></template>
        </el-table-column>
        <el-table-column prop="realName" label="姓名" width="100" />
        <el-table-column prop="userNo" label="学号/工号" min-width="120" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">{{ roleText[row.roleCode] || row.roleCode }}</template>
        </el-table-column>
        <el-table-column prop="deptName" label="院系" min-width="130" />
        <el-table-column prop="className" label="班级 / 楼栋" min-width="150" />
        <el-table-column prop="phone" label="联系电话" min-width="120" />
        <el-table-column label="头像" width="70">
          <template #default="{ row }">
            <el-avatar :size="26" :src="row.avatar || '/uploads/seed/avatar/01.jpg'" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }"><el-tag size="small" :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '启用' : '停用' }}</el-tag></template>
        </el-table-column>
        <el-table-column label="最近登录" min-width="150"><template #default="{ row }">{{ formatTime(row.lastLogin) }}</template></el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="open(row)">编辑</el-button>
            <el-button link @click="reset(row)">重置密码</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:space-between;padding:12px 16px">
        <span class="hint">共 {{ total }} 个账号</span>
        <el-pagination v-model:current-page="q.page" v-model:page-size="q.size" :page-sizes="[10,20,50]" :total="total"
          layout="sizes, prev, pager, next" @size-change="search" @current-change="load" />
      </div>
    </div>

    <el-dialog v-model="dialog" :title="form.id ? '编辑用户' : '新增用户'" width="520px">
      <el-form :model="form" label-width="96px">
        <el-form-item label="账号"><el-input v-model="form.username" :disabled="!!form.id" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.realName" /></el-form-item>
        <el-form-item label="学号/工号"><el-input v-model="form.userNo" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.roleCode" style="width:200px">
            <el-option label="学生" value="STUDENT" /><el-option label="辅导员" value="COUNSELOR" />
            <el-option label="院系负责人" value="DEPT_HEAD" /><el-option label="宿管" value="DORM" /><el-option label="管理员" value="ADMIN" />
          </el-select>
        </el-form-item>
        <el-form-item label="院系"><el-input v-model="form.deptName" /></el-form-item>
        <el-form-item label="班级"><el-input v-model="form.className" placeholder="学生填班级，辅导员可用逗号分隔多个" /></el-form-item>
        <el-form-item label="联系电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="初始密码"><el-input v-model="form.password" placeholder="留空默认 123456" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { formatTime } from '../utils'

const roleText = { STUDENT: '学生', COUNSELOR: '辅导员', DEPT_HEAD: '院系负责人', DORM: '宿管', ADMIN: '管理员' }
const q = ref({ page: 1, size: 10, keyword: '', roleCode: '', status: '' })
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const dialog = ref(false)
const form = ref({})

async function load() {
  loading.value = true
  try {
    const page = await api.userPage(q.value)
    rows.value = page.records
    total.value = page.total
  } finally {
    loading.value = false
  }
}
function search() {
  q.value.page = 1
  load()
}
function open(row) {
  form.value = row ? { ...row, password: '' } : { username: '', realName: '', roleCode: 'STUDENT', deptName: '', className: '', phone: '', password: '' }
  dialog.value = true
}
async function save() {
  await api.userSave(form.value)
  ElMessage.success('已保存')
  dialog.value = false
  load()
}
async function reset(row) {
  await ElMessageBox.confirm(`确认重置 ${row.realName} 的密码为 123456？`, '重置密码', { type: 'warning' })
  await api.userReset(row.id)
  ElMessage.success('密码已重置')
}
async function remove(row) {
  await ElMessageBox.confirm(`确认删除账号 ${row.username}？删除后不可恢复。`, '删除用户', { type: 'warning' })
  await api.userDelete(row.id)
  ElMessage.success('已删除')
  load()
}
onMounted(load)
</script>
