<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>请假行为风险分层</h1>
        <p>规则版本 {{ rule?.version || '-' }} · 权重可配置 · 每次计算保存输入快照与明细，结果可解释、可人工修正</p>
      </div>
      <div class="head-actions">
        <el-select v-model="q.level" placeholder="关注等级" clearable style="width:150px" @change="search">
          <el-option label="低关注" value="LOW" /><el-option label="中关注" value="MID" /><el-option label="高关注" value="HIGH" />
        </el-select>
        <el-input v-model="q.keyword" placeholder="学生姓名" clearable style="width:180px" @keyup.enter="search" />
        <el-button type="primary" @click="search">查询</el-button>
      </div>
    </div>

    <div class="card">
      <div class="card-title">当前生效规则</div>
      <div v-if="rule" class="rule-grid">
        <div>近30天请假次数 <b>{{ rule.wFreq }}%</b></div>
        <div>累计天数 <b>{{ rule.wDays }}%</b></div>
        <div>晚归次数 <b>{{ rule.wLate }}%</b></div>
        <div>逾期销假次数 <b>{{ rule.wOverdue }}%</b></div>
        <div>请假类型 <b>{{ rule.wType }}%</b></div>
        <div>审批驳回次数 <b>{{ rule.wReject }}%</b></div>
        <div>低关注上限 <b>{{ rule.lowThreshold }}</b></div>
        <div>中关注上限 <b>{{ rule.highThreshold }}</b></div>
      </div>
      <div class="hint mt8">修改权重请前往「规则配置」，发布后仅影响新计算或主动重算的数据。</div>
    </div>

    <div class="card mt" style="padding:0">
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="studentName" label="学生" width="100" />
        <el-table-column prop="className" label="班级" min-width="140" />
        <el-table-column prop="ruleVersion" label="规则版本" width="90" />
        <el-table-column label="得分" width="90" align="right">
          <template #default="{ row }"><span class="num">{{ row.totalScore }}</span></template>
        </el-table-column>
        <el-table-column label="推荐等级" width="110">
          <template #default="{ row }"><el-tag size="small" :type="levelMeta(row.level).type">{{ levelMeta(row.level).text }}</el-tag></template>
        </el-table-column>
        <el-table-column label="人工调整" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.adjustLevel" size="small" type="info">{{ levelMeta(row.adjustLevel).text }}</el-tag>
            <span v-else class="hint">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="suggest" label="结果解释" min-width="320" show-overflow-tooltip />
        <el-table-column label="计算时间" min-width="150">
          <template #default="{ row }">{{ formatTime(row.calcTime) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">依据</el-button>
            <el-button link type="primary" @click="recalc(row)">重算</el-button>
            <el-button link type="primary" @click="openAdjust(row)">调整</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:space-between;padding:12px 16px">
        <span class="hint">共 {{ total }} 条</span>
        <el-pagination v-model:current-page="q.page" :page-size="q.size" :total="total" layout="prev, pager, next" @current-change="load" />
      </div>
    </div>

    <el-dialog v-model="detailVisible" title="计算依据与结果解释" width="620px">
      <div v-if="cur">
        <div class="row" style="justify-content:space-between">
          <div>{{ cur.studentName }} · {{ cur.className }}</div>
          <div><span class="num" style="font-size:24px;font-weight:600">{{ cur.totalScore }}</span> / 100</div>
        </div>
        <el-divider style="margin:12px 0" />
        <div class="hint">输入快照（计算时点）</div>
        <pre class="snap">{{ pretty(cur.snapshot) }}</pre>
        <div class="hint">各项得分</div>
        <div v-for="(v, k) in detailObj" :key="k" class="score-row">
          <span>{{ k }}</span><span class="num">{{ v }}</span>
        </div>
        <div class="hint mt">结果解释与改进建议</div>
        <div class="notice">{{ cur.suggest }}</div>
        <div v-if="cur.adjustLevel" class="notice mt" style="background:#FCF7EC;border-color:#A9761F;color:#7A5314">
          人工调整为 {{ levelMeta(cur.adjustLevel).text }}：{{ cur.adjustReason }}（{{ cur.adjustBy }} · {{ formatTime(cur.adjustTime) }}）；原始计算结果保留未覆盖。
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="adjustVisible" title="人工调整关注等级" width="460px">
      <el-form label-width="90px">
        <el-form-item label="目标等级">
          <el-select v-model="adjust.level" style="width:180px">
            <el-option label="低关注" value="LOW" /><el-option label="中关注" value="MID" /><el-option label="高关注" value="HIGH" />
          </el-select>
        </el-form-item>
        <el-form-item label="调整原因">
          <el-input v-model="adjust.reason" type="textarea" :rows="3" placeholder="不少于 5 个字，写入调整记录" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="adjustVisible = false">取消</el-button>
        <el-button type="primary" @click="doAdjust">确认调整</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { formatTime, levelMeta } from '../utils'

const q = ref({ page: 1, size: 10, level: '', keyword: '' })
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const rule = ref(null)
const cur = ref(null)
const detailVisible = ref(false)
const adjustVisible = ref(false)
const adjust = ref({ id: null, level: 'MID', reason: '' })

const detailObj = computed(() => {
  try {
    return JSON.parse(cur.value?.detailJson || '{}')
  } catch (e) {
    return {}
  }
})
const pretty = (s) => {
  try {
    return JSON.stringify(JSON.parse(s || '{}'), null, 2)
  } catch (e) {
    return s
  }
}

async function load() {
  loading.value = true
  try {
    const page = await api.riskScorePage(q.value)
    rows.value = page.records
    total.value = page.total
    rule.value = await api.riskRuleCurrent()
  } finally {
    loading.value = false
  }
}
function search() {
  q.value.page = 1
  load()
}
function openDetail(row) {
  cur.value = row
  detailVisible.value = true
}
async function recalc(row) {
  const s = await api.riskEvaluate(row.studentId)
  ElMessage.success(`已重算：${s.totalScore} 分 · ${levelMeta(s.level).text}`)
  load()
}
function openAdjust(row) {
  cur.value = row
  adjust.value = { id: row.id, level: row.adjustLevel || row.level, reason: '' }
  adjustVisible.value = true
}
async function doAdjust() {
  if (adjust.value.reason.trim().length < 5) return ElMessage.warning('原因不少于 5 个字')
  await api.riskAdjust(adjust.value.id, { level: adjust.value.level, reason: adjust.value.reason })
  ElMessage.success('已保存人工调整，原始结果保留')
  adjustVisible.value = false
  load()
}
onMounted(load)
</script>

<style scoped>
.rule-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 12px; color: #6B7785; }
.rule-grid b { color: #1F2937; font-variant-numeric: tabular-nums; }
.snap { background: #F8FAFC; border: 1px solid #E3E8EF; border-radius: 4px; padding: 10px; font-size: 12px; margin: 6px 0 12px; }
.score-row { display: flex; justify-content: space-between; font-size: 12px; padding: 5px 0; border-bottom: 1px solid #F1F4F8; }
.row { display: flex; align-items: center; }
</style>
