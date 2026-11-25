<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>未归核查</h1>
        <p>超期未销假、夜不归、连续晚归自动生成工单，核查须留痕并闭环</p>
      </div>
      <div class="head-actions">
        <el-select v-model="q.caseType" placeholder="异常类型" clearable style="width:180px" @change="search">
          <el-option v-for="(v, k) in CASE_TYPE" :key="k" :label="v" :value="k" />
        </el-select>
        <el-select v-model="q.status" placeholder="处理状态" clearable style="width:150px" @change="search">
          <el-option label="待处理" value="PENDING" /><el-option label="处理中" value="PROCESSING" /><el-option label="已闭环" value="CLOSED" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
      </div>
    </div>

    <div class="card" style="padding:0">
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="caseNo" label="工单编号" min-width="150">
          <template #default="{ row }"><span class="num" style="color:#2F6B8A">{{ row.caseNo }}</span></template>
        </el-table-column>
        <el-table-column prop="studentName" label="学生" width="90" />
        <el-table-column prop="className" label="班级" min-width="130" />
        <el-table-column label="异常类型" width="120">
          <template #default="{ row }">{{ CASE_TYPE[row.caseType] || row.caseType }}</template>
        </el-table-column>
        <el-table-column label="等级" width="90">
          <template #default="{ row }"><el-tag size="small" :type="levelMeta(row.level).type">{{ levelMeta(row.level).text }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="triggerDesc" label="触发依据" min-width="240" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="(CASE_STATUS[row.status] || {}).type">{{ (CASE_STATUS[row.status] || {}).text || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ownerName" label="负责人" width="90" />
        <el-table-column label="截止时间" min-width="150">
          <template #default="{ row }">{{ formatTime(row.deadline) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push({ path: '/safety/care', query: { caseId: row.id } })">关怀</el-button>
            <el-button v-if="row.status !== 'CLOSED'" link type="primary" @click="close(row)">关闭</el-button>
          </template>
        </el-table-column>
        <template #empty><div class="hint" style="padding:24px 0">当前筛选条件下无异常工单</div></template>
      </el-table>
      <div style="display:flex;justify-content:space-between;padding:12px 16px">
        <span class="hint">共 {{ total }} 条</span>
        <el-pagination v-model:current-page="q.page" :page-size="q.size" :total="total" layout="prev, pager, next" @current-change="load" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { CASE_STATUS, CASE_TYPE, formatTime, levelMeta } from '../utils'

const q = ref({ page: 1, size: 10, caseType: '', status: '' })
const rows = ref([])
const total = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const page = await api.casePage(q.value)
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
async function close(row) {
  const { value } = await ElMessageBox.prompt('请填写核查结论（不少于 5 个字）', '关闭工单', {
    inputPattern: /^.{5,}$/, inputErrorMessage: '不少于 5 个字'
  })
  await api.caseClose(row.id, value)
  ElMessage.success('工单已闭环，关怀记录已同步')
  load()
}
onMounted(load)
</script>
