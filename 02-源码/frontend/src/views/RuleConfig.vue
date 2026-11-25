<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>规则配置</h1>
        <p>审批层级规则与风险分层权重 · 修改后生成新版本并记录生效时间</p>
      </div>
      <div class="head-actions">
        <el-button @click="openRule()">新增审批规则</el-button>
        <el-button type="primary" @click="publish">发布新规则版本</el-button>
      </div>
    </div>

    <div class="card" style="padding:0">
      <div style="padding:16px 16px 0" class="card-title">审批层级规则（{{ rules.length }} 条）</div>
      <el-table :data="rules" size="small">
        <el-table-column prop="leaveType" label="请假类型" width="110" />
        <el-table-column prop="dayThreshold" label="天数阈值" width="100" align="right" />
        <el-table-column prop="outScope" label="外出范围" width="140" />
        <el-table-column prop="requiredMaterial" label="必需材料" min-width="180" />
        <el-table-column label="审批层级" min-width="180">
          <template #default="{ row }">
            <el-tag size="small" :type="row.approvalLevel.includes('DEPT') ? 'warning' : 'success'">
              {{ row.approvalLevel.includes('DEPT') ? '辅导员 → 院系' : '辅导员' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="说明" min-width="240" show-overflow-tooltip />
        <el-table-column label="启用" width="80">
          <template #default="{ row }"><el-switch v-model="row.enabled" :active-value="1" :inactive-value="0" @change="saveRule(row)" /></template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }"><el-button link type="primary" @click="openRule(row)">编辑</el-button></template>
        </el-table-column>
      </el-table>
    </div>

    <div class="grid2 mt">
      <div class="card">
        <div class="card-title">风险分层权重（合计必须 100%）</div>
        <el-form label-width="140px">
          <el-form-item label="近30天请假次数"><el-input-number v-model="w.wFreq" :min="0" :max="100" :step="5" /></el-form-item>
          <el-form-item label="累计天数"><el-input-number v-model="w.wDays" :min="0" :max="100" :step="5" /></el-form-item>
          <el-form-item label="晚归次数"><el-input-number v-model="w.wLate" :min="0" :max="100" :step="5" /></el-form-item>
          <el-form-item label="逾期销假次数"><el-input-number v-model="w.wOverdue" :min="0" :max="100" :step="5" /></el-form-item>
          <el-form-item label="请假类型"><el-input-number v-model="w.wType" :min="0" :max="100" :step="5" /></el-form-item>
          <el-form-item label="审批驳回次数"><el-input-number v-model="w.wReject" :min="0" :max="100" :step="5" /></el-form-item>
          <el-form-item label="低关注上限"><el-input-number v-model="w.lowThreshold" :min="0" :max="100" /></el-form-item>
          <el-form-item label="中关注上限"><el-input-number v-model="w.highThreshold" :min="0" :max="100" /></el-form-item>
          <el-form-item label="权重合计">
            <el-tag :type="sum === 100 ? 'success' : 'danger'">{{ sum }}%</el-tag>
            <span class="hint" style="margin-left:10px">不等于 100% 时后端拒绝发布</span>
          </el-form-item>
        </el-form>
      </div>

      <div class="card">
        <div class="card-title">版本记录与效果</div>
        <el-table :data="versions" size="small">
          <el-table-column prop="version" label="版本" width="70" />
          <el-table-column label="生效时间" min-width="150"><template #default="{ row }">{{ formatTime(row.effectiveTime) }}</template></el-table-column>
          <el-table-column prop="createBy" label="发布人" width="90" />
          <el-table-column label="状态" width="80">
            <template #default="{ row }"><el-tag size="small" :type="row.enabled === 1 ? 'success' : 'info'">{{ row.enabled === 1 ? '生效' : '历史' }}</el-tag></template>
          </el-table-column>
        </el-table>
        <div class="mt">
          <div class="hint">推荐采纳率与人工调整率</div>
          <div class="kpis" style="grid-template-columns:repeat(3,1fr);margin-top:8px">
            <div class="kpi"><div class="lb">计算人次</div><div class="vl">{{ effect.total }}</div></div>
            <div class="kpi"><div class="lb">推荐采纳率</div><div class="vl">{{ effect.adopt }}%</div></div>
            <div class="kpi"><div class="lb">人工调整率</div><div class="vl">{{ effect.adjust }}%</div></div>
          </div>
        </div>
        <div class="notice mt">修改权重只影响新计算或主动重算的数据，历史结果保留原规则版本快照。</div>
      </div>
    </div>

    <el-dialog v-model="dialog" :title="form.id ? '编辑审批规则' : '新增审批规则'" width="520px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="请假类型"><el-input v-model="form.leaveType" style="width:200px" /></el-form-item>
        <el-form-item label="天数阈值">
          <el-input-number v-model="form.dayThreshold" :min="0" :max="60" :step="0.5" />
          <span class="hint" style="margin-left:8px">超过该天数升级审批，0 表示一律升级</span>
        </el-form-item>
        <el-form-item label="外出范围">
          <el-select v-model="form.outScope" style="width:200px">
            <el-option label="市内 CITY" value="CITY" /><el-option label="省内 PROVINCE" value="PROVINCE" />
            <el-option label="跨省 CROSS_PROVINCE" value="CROSS_PROVINCE" />
          </el-select>
        </el-form-item>
        <el-form-item label="必需材料"><el-input v-model="form.requiredMaterial" /></el-form-item>
        <el-form-item label="审批层级">
          <el-select v-model="form.approvalLevel" style="width:220px">
            <el-option label="辅导员" value="COUNSELOR" /><el-option label="辅导员 → 院系" value="COUNSELOR,DEPT" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="saveRule(form)">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { formatTime } from '../utils'

const rules = ref([])
const versions = ref([])
const dialog = ref(false)
const form = ref({})
const w = ref({ wFreq: 20, wDays: 20, wLate: 20, wOverdue: 25, wType: 10, wReject: 5, lowThreshold: 40, highThreshold: 70 })
const effect = ref({ total: 0, adopt: 0, adjust: 0 })
const sum = computed(() => Number(w.value.wFreq) + Number(w.value.wDays) + Number(w.value.wLate)
  + Number(w.value.wOverdue) + Number(w.value.wType) + Number(w.value.wReject))

async function load() {
  rules.value = await api.ruleList()
  versions.value = await api.riskRules()
  const cur = await api.riskRuleCurrent()
  if (cur) {
    w.value = { wFreq: Number(cur.wFreq), wDays: Number(cur.wDays), wLate: Number(cur.wLate),
      wOverdue: Number(cur.wOverdue), wType: Number(cur.wType), wReject: Number(cur.wReject),
      lowThreshold: Number(cur.lowThreshold), highThreshold: Number(cur.highThreshold) }
  }
  const d = await api.dashboard('30')
  const scores = await api.riskScorePage({ page: 1, size: 200 })
  const total = scores.total || 0
  const adjusted = (scores.records || []).filter((x) => x.adjustLevel).length
  effect.value = { total, adopt: total ? Math.round(((total - adjusted) / total) * 1000) / 10 : 0,
    adjust: total ? Math.round((adjusted / total) * 1000) / 10 : 0 }
}
function openRule(row) {
  form.value = row ? { ...row } : { leaveType: '', dayThreshold: 0, outScope: 'CITY', requiredMaterial: '', approvalLevel: 'COUNSELOR', remark: '', enabled: 1 }
  dialog.value = true
}
async function saveRule(row) {
  await api.ruleSave(row)
  ElMessage.success('已保存')
  dialog.value = false
  load()
}
async function publish() {
  if (sum.value !== 100) return ElMessage.warning('权重合计必须等于 100%')
  await api.riskRulePublish({ ...w.value, name: '请假行为风险分层规则' })
  ElMessage.success('新版本已发布并生效')
  load()
}
onMounted(load)
</script>
