<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>关怀记录</h1>
        <p>电话核查、家长联系、宿舍走访与后续处置全过程留痕{{ caseId ? ' · 当前按工单筛选' : '' }}</p>
      </div>
      <div class="head-actions">
        <el-button v-if="caseId" @click="clearFilter">查看全部</el-button>
      </div>
    </div>

    <div class="grid2">
      <div class="card">
        <div class="card-title">新增关怀记录</div>
        <el-form :model="form" label-width="96px">
          <el-form-item label="学生">
            <el-select v-model="form.studentId" filterable remote :remote-method="searchStudent" style="width:260px"
              placeholder="搜索学生" @change="(id) => { const s = students.find(x => x.id === id); form.studentName = s?.realName || '' }">
              <el-option v-for="s in students" :key="s.id" :label="`${s.realName} · ${s.className}`" :value="s.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="核查方式">
            <el-select v-model="form.careWay" style="width:200px">
              <el-option v-for="(v, k) in CARE_WAY" :key="k" :label="v" :value="k" />
            </el-select>
          </el-form-item>
          <el-form-item label="学生情况">
            <el-input v-model="form.content" type="textarea" :rows="3" placeholder="不少于 5 个字" />
          </el-form-item>
          <el-form-item label="后续处置">
            <el-input v-model="form.result" type="textarea" :rows="3" placeholder="如：要求 22:00 前到楼并生成返校码" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="submit">保存记录</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="card">
        <div class="card-title">历史记录</div>
        <el-timeline v-if="rows.length">
          <el-timeline-item v-for="r in rows" :key="r.id" :timestamp="formatTime(r.recordTime)" type="primary">
            <div class="timeline-title">{{ CARE_WAY[r.careWay] || r.careWay }} · {{ r.studentName }}</div>
            <div class="timeline-meta">情况：{{ r.content }}</div>
            <div class="timeline-meta">处置：{{ r.result }}（{{ r.recorderName }}）</div>
          </el-timeline-item>
        </el-timeline>
        <div v-else class="hint">暂无关怀记录</div>
        <el-pagination v-model:current-page="q.page" :page-size="q.size" :total="total" layout="prev, pager, next"
          small class="mt" @current-change="load" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { CARE_WAY, formatTime } from '../utils'

const route = useRoute()
const caseId = ref(route.query.caseId || '')
const students = ref([])
const rows = ref([])
const total = ref(0)
const saving = ref(false)
const q = ref({ page: 1, size: 10 })
const form = ref({ studentId: null, studentName: '', careWay: 'PHONE', content: '', result: '', caseId: caseId.value || null })

async function load() {
  const params = { ...q.value }
  if (caseId.value) params.caseId = caseId.value
  const page = await api.carePage(params)
  rows.value = page.records
  total.value = page.total
}
async function searchStudent(kw) {
  students.value = await api.studentOptions(kw)
}
function clearFilter() {
  caseId.value = ''
  form.value.caseId = null
  load()
}
async function submit() {
  if (!form.value.studentId) return ElMessage.warning('请选择学生')
  if (form.value.content.trim().length < 5 || form.value.result.trim().length < 5) {
    return ElMessage.warning('学生情况与后续处置均不少于 5 个字')
  }
  saving.value = true
  try {
    await api.careAdd(form.value)
    ElMessage.success('已保存关怀记录')
    form.value.content = ''
    form.value.result = ''
    load()
  } finally {
    saving.value = false
  }
}
onMounted(() => {
  searchStudent('')
  load()
})
</script>
