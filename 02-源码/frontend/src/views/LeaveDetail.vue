<template>
  <div v-if="l">
    <div class="pagehead">
      <div>
        <h1 class="num">{{ l.applyNo }}</h1>
        <p>{{ l.leaveType }} · {{ l.studentName }} · {{ l.className }} · 提交于 {{ formatTime(l.createTime) }}</p>
      </div>
      <div class="head-actions">
        <el-tag :type="statusMeta(l.status).type" size="large">{{ statusMeta(l.status).text }}</el-tag>
        <el-button v-if="l.overdueFlag === 1" type="danger" plain size="small">超期未销假</el-button>
      </div>
    </div>

    <div class="groups">
      <div class="g"><div class="lb">当前责任人</div><div class="vl">{{ l.currentApproverName || '—' }}</div></div>
      <div class="g"><div class="lb">审批层级</div><div class="vl">{{ l.needDept === 1 ? '辅导员 → 院系' : '辅导员' }}（规则 {{ l.approvalLevel }}）</div></div>
      <div class="g"><div class="lb">请假时间</div><div class="vl num">{{ formatTime(l.startTime) }} → {{ formatTime(l.endTime) }}（{{ l.days }} 天）</div></div>
      <div class="g"><div class="lb">应销假时间</div><div class="vl num">{{ formatTime(l.returnDeadline) }}</div></div>
      <div class="g"><div class="lb">外出地点</div><div class="vl">{{ l.destination || '-' }}</div></div>
      <div class="g"><div class="lb">紧急联系人</div><div class="vl">{{ l.contactName }} · {{ l.contactPhone }}</div></div>
      <div class="g"><div class="lb">交通方式</div><div class="vl">{{ l.transport || '-' }}</div></div>
      <div class="g"><div class="lb">创建 / 更新</div><div class="vl num">{{ formatTime(l.createTime) }} / {{ formatTime(l.updateTime) }}</div></div>
    </div>

    <div class="grid2 mt">
      <div class="card">
        <div class="card-title">审批与流转时间轴</div>
        <el-timeline>
          <el-timeline-item :timestamp="formatTime(l.createTime)" type="primary">
            <div class="timeline-title">提交申请</div>
            <div class="timeline-meta">{{ l.studentName }} · 事由：{{ l.reason }}</div>
          </el-timeline-item>
          <el-timeline-item v-for="a in d.approvals" :key="a.id" :timestamp="formatTime(a.createTime)"
            :type="a.action === 'REJECT' ? 'danger' : 'success'">
            <div class="timeline-title">{{ a.node === 'DEPT' ? '院系审批' : '辅导员审批' }} · {{ a.action === 'APPROVE' ? '通过' : '驳回' }}</div>
            <div class="timeline-meta">{{ a.approverName }} · {{ a.opinion }}</div>
          </el-timeline-item>
          <el-timeline-item v-for="r in d.returns" :key="'r' + r.id" :timestamp="formatTime(r.verifyTime || r.createTime)"
            :type="r.status === 'VERIFIED' ? 'success' : 'warning'">
            <div class="timeline-title">返校销假 · {{ r.status === 'VERIFIED' ? '已核销' : '待核验' }}</div>
            <div class="timeline-meta">返校码 {{ r.returnCode }} · {{ r.verifierName || '系统生成' }} · {{ r.remark }}</div>
          </el-timeline-item>
          <el-timeline-item v-if="l.status === 'CANCELLED'" type="info" :timestamp="formatTime(l.updateTime)">
            <div class="timeline-title">已取消</div>
            <div class="timeline-meta">{{ l.cancelReason }}</div>
          </el-timeline-item>
        </el-timeline>
      </div>

      <div>
        <div class="card">
          <div class="card-title">证明材料</div>
          <div v-if="l.attachmentPath" class="row">
            <el-image :src="l.attachmentPath" :preview-src-list="[l.attachmentPath]" fit="cover"
              style="width:120px;height:88px;border-radius:4px" preview-teleported />
            <div class="hint">仅本人与审批人可见；销假后不可修改原审批时间与材料</div>
          </div>
          <div v-else class="hint">未上传证明材料</div>
        </div>

        <div class="card">
          <div class="card-title">请假行为风险分层</div>
          <div v-if="score">
            <div class="row" style="justify-content:space-between">
              <div>
                <span class="num" style="font-size:28px;font-weight:600">{{ score.totalScore }}</span>
                <span class="hint"> / 100</span>
              </div>
              <el-tag :type="levelMeta(score.adjustLevel || score.level).type">{{ levelMeta(score.adjustLevel || score.level).text }}</el-tag>
            </div>
            <div class="hint mt8">规则版本 {{ score.ruleVersion }} · 计算于 {{ formatTime(score.calcTime) }}</div>
            <div class="mt8" v-for="(v, k) in detail" :key="k" style="display:flex;justify-content:space-between;font-size:12px">
              <span>{{ k }}</span><span class="num">{{ v }}</span>
            </div>
            <div class="notice mt">{{ score.suggest }}</div>
            <div v-if="score.adjustLevel" class="hint mt8">人工调整为 {{ levelMeta(score.adjustLevel).text }}：{{ score.adjustReason }}（{{ score.adjustBy }}）</div>
            <el-button size="small" class="mt" @click="evaluate">重新计算</el-button>
          </div>
          <div v-else>
            <div class="hint">尚未计算，点击下方按钮生成可解释的风险分层结果</div>
            <el-button size="small" type="primary" class="mt" @click="evaluate">立即计算</el-button>
          </div>
        </div>

        <div class="card">
          <div class="card-title">可执行操作</div>
          <div style="display:flex;gap:10px;flex-wrap:wrap">
            <el-button v-if="isOwner && (l.status === 'DRAFT' || l.status === 'REJECTED')" type="primary" @click="act('SUBMIT')">提交审批</el-button>
            <el-button v-if="isOwner && (l.status === 'ON_LEAVE' || l.status === 'RETURN_PENDING')" type="primary" @click="act('RETURN_CODE')">生成返校码</el-button>
            <el-button v-if="canApprove" type="primary" @click="act('APPROVE')">审批通过</el-button>
            <el-button v-if="canApprove" type="danger" plain @click="act('REJECT')">驳回</el-button>
            <el-button v-if="isOwner && !['COMPLETED','CANCELLED','REJECTED'].includes(l.status)" type="danger" plain @click="act('CANCEL')">取消请假</el-button>
          </div>
          <div class="hint mt8">退回、驳回、取消必须填写不少于 5 个字的原因，操作会写入日志与时间轴。</div>
        </div>

        <div class="card">
          <div class="card-title">操作日志</div>
          <div v-for="log in d.logs" :key="log.id" class="log-row">
            <span class="hint">{{ formatTime(log.createTime) }}</span>
            <span>{{ log.userName }}</span>
            <span>{{ log.action }}</span>
            <span class="hint">{{ log.beforeStatus || '-' }} → {{ log.afterStatus || '-' }}</span>
          </div>
          <div v-if="!d.logs || d.logs.length === 0" class="hint">暂无日志</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { store } from '../store'
import { formatTime, levelMeta, statusMeta } from '../utils'

const route = useRoute()
const d = ref({})
const l = computed(() => d.value.leave)
const score = ref(null)
const isOwner = computed(() => l.value?.studentId === store.user?.id)
const canApprove = computed(() => ['COUNSELOR_PENDING', 'DEPT_PENDING'].includes(l.value?.status) && !isOwner.value)
const detail = computed(() => {
  try {
    return JSON.parse(score.value?.detailJson || '{}')
  } catch (e) {
    return {}
  }
})

async function load() {
  d.value = await api.leaveDetail(route.params.id)
  const list = d.value?.leave
  if (list?.riskScore) {
    score.value = {
      totalScore: list.riskScore, level: list.riskLevel, detailJson: '{}',
      suggest: '该分数为提交时按规则计算的结果快照，可点击「重新计算」获取最新依据与分项得分。',
      ruleVersion: 'v3', calcTime: list.createTime, adjustLevel: null
    }
  }
}

async function evaluate() {
  score.value = await api.leaveEvaluate(route.params.id)
  ElMessage.success('已按当前规则版本完成计算')
}

async function act(action) {
  let reason = ''
  if (['REJECT', 'CANCEL'].includes(action)) {
    const { value } = await ElMessageBox.prompt('请填写原因（不少于 5 个字）', action === 'REJECT' ? '驳回申请' : '取消请假',
      { inputPattern: /^.{5,}$/, inputErrorMessage: '原因不少于 5 个字' })
    reason = value
  } else {
    await ElMessageBox.confirm(`确认执行「${action}」操作？`, '提示', { type: 'warning' })
  }
  await api.leaveTransition(route.params.id, { action, reason, opinion: reason, version: l.value.version })
  ElMessage.success('操作成功')
  load()
}

onMounted(load)
</script>

<style scoped>
.groups { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1px; background: #E3E8EF; border: 1px solid #E3E8EF; border-radius: 6px; overflow: hidden; }
.g { background: #fff; padding: 12px 16px; }
.g .lb { font-size: 12px; color: #6B7785; }
.g .vl { margin-top: 4px; }
.row { display: flex; gap: 12px; align-items: flex-start; }
.log-row { display: flex; gap: 10px; font-size: 12px; padding: 6px 0; border-bottom: 1px solid #F1F4F8; }
</style>
