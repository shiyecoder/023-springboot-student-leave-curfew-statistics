<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>{{ pageTitle }}</h1>
        <p>共 {{ total }} 条记录 · 服务端分页 · 全系统时间统一 yyyy-MM-dd HH:mm:ss</p>
      </div>
      <div class="head-actions">
        <el-button @click="exportCsv">导出当前筛选</el-button>
        <el-button v-if="isStudent" type="primary" @click="$router.push('/leave/create')">发起请假</el-button>
      </div>
    </div>

    <div class="card">
      <div class="filters">
        <el-input v-model="q.keyword" placeholder="申请编号 / 学生姓名" clearable @keyup.enter="search" />
        <el-select v-model="q.leaveType" placeholder="请假类型" clearable>
          <el-option v-for="t in ['病假','事假','公假','实习','跨省外出']" :key="t" :label="t" :value="t" />
        </el-select>
        <el-select v-model="q.status" placeholder="审批状态" clearable>
          <el-option v-for="(v, k) in STATUS_MAP" :key="k" :label="v.text" :value="k" />
        </el-select>
        <el-select v-if="!isStudent" v-model="q.className" placeholder="班级" clearable>
          <el-option v-for="c in classOptions" :key="c" :label="c" :value="c" />
        </el-select>
        <el-date-picker v-model="dates" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期"
          value-format="YYYY-MM-DD" style="width:250px" />
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>
    </div>

    <div class="card mt" style="padding:0">
      <el-table :data="rows" v-loading="loading" style="width:100%">
        <el-table-column prop="applyNo" label="申请编号" min-width="150">
          <template #default="{ row }"><span class="num" style="color:#2F6B8A;font-weight:500">{{ row.applyNo }}</span></template>
        </el-table-column>
        <el-table-column v-if="!isStudent" prop="studentName" label="学生" min-width="90" />
        <el-table-column v-if="!isStudent" prop="className" label="班级" min-width="120" />
        <el-table-column prop="leaveType" label="类型" min-width="80" />
        <el-table-column label="开始时间" min-width="150"><template #default="{ row }">{{ formatTime(row.startTime) }}</template></el-table-column>
        <el-table-column label="结束时间" min-width="150"><template #default="{ row }">{{ formatTime(row.endTime) }}</template></el-table-column>
        <el-table-column prop="days" label="天数" min-width="70" align="right">
          <template #default="{ row }"><span class="num">{{ row.days }}</span></template>
        </el-table-column>
        <el-table-column prop="destination" label="外出地点" min-width="160" show-overflow-tooltip />
        <el-table-column label="证明" min-width="70">
          <template #default="{ row }">
            <el-image v-if="row.attachmentPath" :src="row.attachmentPath" :preview-src-list="[row.attachmentPath]"
              fit="cover" style="width:44px;height:32px;border-radius:3px" preview-teleported />
            <span v-else class="hint">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="110">
          <template #default="{ row }">
            <el-tag :type="statusMeta(row.status).type" size="small">{{ statusMeta(row.status).text }}</el-tag>
            <el-tag v-if="row.overdueFlag === 1" type="danger" size="small" style="margin-left:4px">超期</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="currentApproverName" label="当前审批人" min-width="100" />
        <el-table-column label="最近更新" min-width="150"><template #default="{ row }">{{ formatTime(row.updateTime) }}</template></el-table-column>
        <el-table-column label="操作" min-width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push('/leave/detail/' + row.id)">查看</el-button>
            <el-button v-if="isStudent && row.status === 'RETURN_PENDING'" link type="primary"
              @click="$router.push('/leave/return')">销假</el-button>
            <el-button v-if="canApprove(row)" link type="primary" @click="openApprove(row)">审批</el-button>
            <el-button v-if="isStudent && (row.status === 'DRAFT' || row.status === 'REJECTED')" link
              @click="$router.push('/leave/edit/' + row.id)">编辑</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <div style="padding:26px 0">
            <div class="hint">当前筛选条件下无记录</div>
            <el-button v-if="isStudent" type="primary" size="small" class="mt8" @click="$router.push('/leave/create')">发起请假</el-button>
          </div>
        </template>
      </el-table>
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px">
        <span class="hint">共 {{ total }} 条</span>
        <el-pagination v-model:current-page="q.page" v-model:page-size="q.size" :page-sizes="[10, 20, 50]"
          :total="total" layout="sizes, prev, pager, next" @size-change="search" @current-change="load" />
      </div>
    </div>

    <el-drawer v-model="drawer" title="审批" size="460px">
      <div v-if="cur">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="申请编号">{{ cur.applyNo }}</el-descriptions-item>
          <el-descriptions-item label="学生">{{ cur.studentName }} · {{ cur.className }}</el-descriptions-item>
          <el-descriptions-item label="请假">{{ cur.leaveType }} · {{ cur.days }} 天</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(cur.startTime) }} → {{ formatTime(cur.endTime) }}</el-descriptions-item>
          <el-descriptions-item label="事由">{{ cur.reason }}</el-descriptions-item>
          <el-descriptions-item label="风险分层">
            <el-tag :type="levelMeta(cur.riskLevel).type" size="small">{{ levelMeta(cur.riskLevel).text }}</el-tag>
            <span class="num" style="margin-left:6px">{{ cur.riskScore }}</span>
          </el-descriptions-item>
        </el-descriptions>
        <div class="hint mt">审批意见（驳回时必填，不少于 5 字）</div>
        <el-input v-model="opinion" type="textarea" :rows="3" class="mt8" placeholder="请填写审批意见" />
        <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:18px">
          <el-button @click="drawer = false">取消</el-button>
          <el-button type="danger" plain @click="doTransition('REJECT')">驳回</el-button>
          <el-button type="primary" @click="doTransition('APPROVE')">通过</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { store } from '../store'
import { STATUS_MAP, formatTime, levelMeta, statusMeta } from '../utils'

const q = ref({ page: 1, size: 10, keyword: '', leaveType: '', status: '', className: '' })
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const dates = ref([])
const drawer = ref(false)
const cur = ref(null)
const opinion = ref('')

const isStudent = computed(() => store.user?.roleCode === 'STUDENT')
const isDept = computed(() => store.user?.roleCode === 'DEPT_HEAD')
const pageTitle = computed(() => isStudent.value ? '我的请假' : isDept.value ? '本院系请假记录' : '请假记录')
const classOptions = ['软件工程 2201', '软件工程 2202', '软件工程 2203', '计算机科学 2201']

const canApprove = (row) => !isStudent.value && ['COUNSELOR_PENDING', 'DEPT_PENDING'].includes(row.status)

async function load() {
  loading.value = true
  try {
    const params = { ...q.value }
    if (dates.value && dates.value.length === 2) {
      params.startDate = dates.value[0]
      params.endDate = dates.value[1]
    }
    const page = await api.leavePage(params)
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
function reset() {
  q.value = { page: 1, size: 10, keyword: '', leaveType: '', status: '', className: '' }
  dates.value = []
  load()
}
function openApprove(row) {
  cur.value = row
  opinion.value = ''
  drawer.value = true
}
async function doTransition(action) {
  if (action === 'REJECT' && opinion.value.trim().length < 5) {
    return ElMessage.warning('驳回必须填写不少于 5 个字的原因')
  }
  await api.leaveTransition(cur.value.id, { action, opinion: opinion.value, version: cur.value.version })
  ElMessage.success(action === 'APPROVE' ? '已通过' : '已驳回')
  drawer.value = false
  load()
}
function exportCsv() {
  const token = localStorage.getItem('token')
  const params = new URLSearchParams({ ...q.value, page: 1, size: 200 })
  fetch('/api/student-leave/export?' + params, { headers: { Authorization: 'Bearer ' + token } })
    .then((r) => r.blob())
    .then((b) => {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(b)
      a.download = '请假记录.csv'
      a.click()
    })
}
onMounted(load)
</script>
