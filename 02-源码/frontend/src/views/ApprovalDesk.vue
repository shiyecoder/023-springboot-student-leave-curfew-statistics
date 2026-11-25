<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>{{ isDept ? '院系审批' : '审批工作台' }}</h1>
        <p>{{ isDept ? '长假 / 跨省 / 特殊类型请假，需追加院系审批' : '待我审批的请假单，行末直接处理，支持批量审批' }}</p>
      </div>
      <div class="head-actions">
        <el-button :disabled="selection.length === 0" type="primary" @click="batchApprove">
          批量通过{{ selection.length ? `（${selection.length}）` : '' }}
        </el-button>
      </div>
    </div>

    <div class="kpis" style="grid-template-columns:repeat(5,1fr)">
      <div class="kpi"><div class="lb">待我审批</div><div class="vl" style="color:#A9761F">{{ total }}</div><div class="dt">超 24h 自动提醒</div></div>
      <div class="kpi"><div class="lb">今日已处理</div><div class="vl">{{ done }}</div><div class="dt">审批留痕可追溯</div></div>
      <div class="kpi"><div class="lb">平均审批时效</div><div class="vl">{{ avgHours }}<span style="font-size:12px"> h</span></div><div class="dt">近 30 天</div></div>
      <div class="kpi"><div class="lb">待销假</div><div class="vl">{{ pendingReturn }}</div><div class="dt">到期未销假自动生成工单</div></div>
      <div class="kpi"><div class="lb">重点关注</div><div class="vl" style="color:#B3261E">{{ highRisk }}</div><div class="dt">风险分层高关注</div></div>
    </div>

    <div class="card mt">
      <div class="filters">
        <el-radio-group v-model="tab" @change="search">
          <el-radio-button label="todo">待我处理</el-radio-button>
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="overdue">超期未销假</el-radio-button>
        </el-radio-group>
        <el-select v-model="q.leaveType" placeholder="请假类型" clearable style="width:180px" @change="search">
          <el-option v-for="t in ['病假','事假','公假','实习','跨省外出']" :key="t" :label="t" :value="t" />
        </el-select>
        <el-input v-model="q.keyword" placeholder="学生 / 编号" clearable style="width:200px" @keyup.enter="search" />
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>
    </div>

    <div class="card mt" style="padding:0">
      <el-table :data="rows" v-loading="loading" @selection-change="(v) => (selection = v)">
        <el-table-column type="selection" width="44" :selectable="(r) => r.status !== 'COMPLETED'" />
        <el-table-column prop="applyNo" label="申请编号" min-width="150">
          <template #default="{ row }"><span class="num" style="color:#2F6B8A">{{ row.applyNo }}</span></template>
        </el-table-column>
        <el-table-column prop="studentName" label="学生" min-width="90" />
        <el-table-column prop="className" label="班级" min-width="120" />
        <el-table-column prop="leaveType" label="类型" min-width="80" />
        <el-table-column label="起止时间" min-width="230">
          <template #default="{ row }"><span class="num">{{ formatTime(row.startTime) }} → {{ formatTime(row.endTime) }}</span></template>
        </el-table-column>
        <el-table-column prop="days" label="天数" min-width="70" align="right" />
        <el-table-column label="风险" min-width="90">
          <template #default="{ row }">
            <el-tag :type="levelMeta(row.riskLevel).type" size="small">{{ levelMeta(row.riskLevel).text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="120">
          <template #default="{ row }">
            <el-tag :type="statusMeta(row.status).type" size="small">{{ statusMeta(row.status).text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push('/leave/detail/' + row.id)">查看</el-button>
            <el-button v-if="['COUNSELOR_PENDING','DEPT_PENDING'].includes(row.status)" link type="primary" @click="open(row)">审批</el-button>
            <el-button v-if="row.status === 'RETURN_PENDING'" link type="primary" @click="remind(row)">催办</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:space-between;padding:12px 16px">
        <span class="hint">共 {{ total }} 条</span>
        <el-pagination v-model:current-page="q.page" v-model:page-size="q.size" :page-sizes="[10, 20, 50]"
          :total="total" layout="sizes, prev, pager, next" @size-change="search" @current-change="load" />
      </div>
    </div>

    <el-drawer v-model="drawer" title="审批单据" size="460px">
      <div v-if="cur">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="编号">{{ cur.applyNo }}</el-descriptions-item>
          <el-descriptions-item label="学生">{{ cur.studentName }} · {{ cur.className }}</el-descriptions-item>
          <el-descriptions-item label="请假">{{ cur.leaveType }} · {{ cur.days }} 天</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(cur.startTime) }} → {{ formatTime(cur.endTime) }}</el-descriptions-item>
          <el-descriptions-item label="事由">{{ cur.reason }}</el-descriptions-item>
          <el-descriptions-item label="风险">{{ levelMeta(cur.riskLevel).text }}（{{ cur.riskScore }} 分）</el-descriptions-item>
        </el-descriptions>
        <div class="hint mt">审批意见（驳回必填，≥5 字）</div>
        <el-input v-model="opinion" type="textarea" :rows="3" class="mt8" placeholder="如：已电话核实本人与家长，同意请假。" />
        <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:18px">
          <el-button @click="drawer = false">取消</el-button>
          <el-button type="danger" plain @click="submit('REJECT')">驳回</el-button>
          <el-button type="primary" @click="submit('APPROVE')">通过</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { formatTime, levelMeta, statusMeta } from '../utils'

const route = useRoute()
const isDept = computed(() => route.path.includes('/approval/dept'))
const tab = ref('todo')
const q = ref({ page: 1, size: 10, keyword: '', leaveType: '' })
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const drawer = ref(false)
const cur = ref(null)
const opinion = ref('')
const selection = ref([])
const stat = ref({ done: 0, avgHours: 0, pendingReturn: 0, highRisk: 0 })

const done = computed(() => stat.value.done || 0)
const avgHours = computed(() => stat.value.avgHours || 0)
const pendingReturn = computed(() => stat.value.pendingReturn || 0)
const highRisk = computed(() => stat.value.highRisk || 0)

async function load() {
  loading.value = true
  try {
    const params = { ...q.value }
    if (tab.value === 'todo') {
      params.todo = '1'
      params.status = isDept.value ? 'DEPT_PENDING' : 'COUNSELOR_PENDING'
    } else if (tab.value === 'overdue') {
      params.overdue = '1'
    } else if (isDept.value) {
      params.status = 'DEPT_PENDING'
    }
    const page = await api.leavePage(params)
    rows.value = page.records
    total.value = page.total
  } finally {
    loading.value = false
  }
}
async function loadStat() {
  const d = await api.dashboard('30')
  stat.value = { done: d.leaveCount, avgHours: d.avgHours, pendingReturn: d.onLeave, highRisk: (d.focusStudents || []).length }
}
function search() {
  q.value.page = 1
  load()
}
function reset() {
  q.value = { page: 1, size: 10, keyword: '', leaveType: '' }
  search()
}
function open(row) {
  cur.value = row
  opinion.value = ''
  drawer.value = true
}
async function submit(action) {
  if (action === 'REJECT' && opinion.value.trim().length < 5) return ElMessage.warning('驳回必须填写不少于 5 个字的原因')
  await api.leaveTransition(cur.value.id, { action, opinion: opinion.value, version: cur.value.version })
  ElMessage.success('审批完成')
  drawer.value = false
  load()
  loadStat()
}
async function batchApprove() {
  await ElMessageBox.confirm(`确认批量通过 ${selection.value.length} 条申请？系统将逐条返回结果。`, '批量审批', { type: 'warning' })
  let ok = 0
  const fails = []
  for (const row of selection.value) {
    try {
      await api.leaveTransition(row.id, { action: 'APPROVE', opinion: '批量审批通过', version: row.version })
      ok++
    } catch (e) {
      fails.push(`${row.applyNo}：${e.message}`)
    }
  }
  ElMessage[fails.length ? 'warning' : 'success'](`成功 ${ok} 条${fails.length ? '，失败 ' + fails.length + ' 条：' + fails.join('；') : ''}`)
  load()
}
function remind(row) {
  ElMessage.success(`已向 ${row.studentName} 推送催办消息（${row.applyNo}）`)
}
onMounted(() => {
  load()
  loadStat()
})
</script>
