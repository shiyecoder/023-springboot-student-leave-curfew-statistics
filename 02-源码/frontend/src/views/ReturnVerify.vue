<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>返校销假</h1>
        <p>{{ isStudent ? '返校后生成 6 位限时返校码，由宿管核验或辅导员人工核销' : '核验学生返校码，通过后请假单自动闭环' }}</p>
      </div>
      <div class="head-actions">
        <el-tag v-if="isStudent" type="warning">待销假 {{ pendingList.length }} 条</el-tag>
      </div>
    </div>

    <div v-if="isStudent" class="grid2">
      <div class="card">
        <div class="card-title">我的待销假单据</div>
        <el-table :data="pendingList" size="small">
          <el-table-column prop="applyNo" label="申请编号" min-width="140" />
          <el-table-column prop="leaveType" label="类型" width="80" />
          <el-table-column label="应返时间" min-width="150">
            <template #default="{ row }">{{ formatTime(row.endTime) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="genCode(row)">生成返校码</el-button>
            </template>
          </el-table-column>
          <template #empty><div class="hint" style="padding:14px 0">当前没有待销假的请假单</div></template>
        </el-table>
      </div>
      <div class="card">
        <div class="card-title">返校码</div>
        <div v-if="!code" class="hint">选择左侧待销假单据后生成返校码，有效期 10 分钟</div>
        <div v-else style="text-align:center;padding:8px 0">
          <img v-if="qr" :src="qr" style="width:140px;height:140px" alt="返校码" />
          <div class="num" style="font-size:24px;letter-spacing:6px;margin-top:8px">{{ code }}</div>
          <div class="hint mt8">有效期至 {{ formatTime(expire) }} · 仅供宿管值班员核验</div>
          <div class="notice mt">销假后只能追加备注，原审批时间与材料不可修改。</div>
        </div>
      </div>
    </div>

    <div v-else class="grid2">
      <div class="card">
        <div class="card-title">扫码 / 输入返校码核验</div>
        <el-input v-model="verifyCodeInput" maxlength="6" placeholder="请输入 6 位返校码" size="large"
          style="width:260px;font-size:20px;letter-spacing:4px" />
        <el-button type="primary" class="mt" :loading="verifying" @click="verify">核验</el-button>
        <div v-if="result" class="result-box">
          <div class="res-ok">核验通过</div>
          <div class="mt8">{{ result.studentName }} · {{ result.applyNo }}</div>
          <div class="hint mt8">核验方式：{{ result.verifyType === 'CODE' ? '扫码' : '人工核销' }} · {{ formatTime(result.verifyTime) }} · 核验人 {{ result.verifierName }}</div>
        </div>
        <div class="notice mt">返校码有效期 10 分钟；过期需学生重新生成，或由辅导员人工核销（须填写原因）。</div>
      </div>
      <div class="card">
        <div class="card-title">今日核验与待核验记录</div>
        <el-table :data="records" size="small" v-loading="loading">
          <el-table-column prop="studentName" label="学生" width="90" />
          <el-table-column prop="applyNo" label="请假编号" min-width="140" />
          <el-table-column prop="returnCode" label="返校码" width="90" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'VERIFIED' ? 'success' : row.status === 'EXPIRED' ? 'danger' : 'warning'">
                {{ { VERIFIED: '已核销', PENDING: '待核验', EXPIRED: '已过期' }[row.status] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="时间" min-width="150">
            <template #default="{ row }">{{ formatTime(row.verifyTime || row.createTime) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button v-if="row.status !== 'VERIFIED'" size="small" link type="primary" @click="manual(row)">人工核销</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div v-if="isStudent" class="card mt" style="padding:0">
      <el-table :data="records" size="small">
        <el-table-column prop="applyNo" label="请假编号" min-width="150" />
        <el-table-column prop="returnCode" label="返校码" width="100" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'VERIFIED' ? 'success' : row.status === 'EXPIRED' ? 'danger' : 'warning'">
              {{ { VERIFIED: '已核销', PENDING: '待核验', EXPIRED: '已过期' }[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="核验人" width="110"><template #default="{ row }">{{ row.verifierName || '-' }}</template></el-table-column>
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ formatTime(row.verifyTime || row.createTime) }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import QRCode from 'qrcode'
import { api } from '../api'
import { store } from '../store'
import { formatTime } from '../utils'

const isStudent = computed(() => store.user?.roleCode === 'STUDENT')
const pendingList = ref([])
const records = ref([])
const code = ref('')
const qr = ref('')
const expire = ref('')
const verifyCodeInput = ref('')
const verifying = ref(false)
const result = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    if (isStudent.value) {
      const page = await api.leavePage({ page: 1, size: 20, status: 'RETURN_PENDING' })
      pendingList.value = page.records
    }
    const rp = await api.returnPage({ page: 1, size: 20 })
    records.value = rp.records
  } finally {
    loading.value = false
  }
}

async function genCode(row) {
  const leave = await api.leaveTransition(row.id, { action: 'RETURN_CODE', version: row.version })
  const page = await api.returnPage({ page: 1, size: 5 })
  const rec = page.records.find((r) => r.leaveId === leave.id && r.status === 'PENDING') || page.records[0]
  code.value = rec.returnCode
  expire.value = rec.codeExpire
  qr.value = await QRCode.toDataURL(`LEAVE:${rec.applyNo}:${rec.returnCode}`, { width: 280, margin: 1, color: { dark: '#1F2937' } })
  ElMessage.success('返校码已生成，10 分钟内有效')
  load()
}

async function verify() {
  verifying.value = true
  try {
    result.value = await api.returnVerify(verifyCodeInput.value)
    ElMessage.success('核验通过，已写入销假记录')
    verifyCodeInput.value = ''
    load()
  } finally {
    verifying.value = false
  }
}

async function manual(row) {
  const { value } = await ElMessageBox.prompt('人工核销需填写原因（不少于 5 个字）', '人工核销', {
    inputPattern: /^.{5,}$/, inputErrorMessage: '原因不少于 5 个字'
  })
  await api.returnManual(row.id, value)
  ElMessage.success('人工核销完成')
  load()
}

onMounted(load)
</script>

<style scoped>
.result-box { border: 1px solid #BEDCCD; background: #EFF7F3; border-radius: 4px; padding: 14px; margin-top: 16px; }
.res-ok { color: #2E7D5B; font-weight: 600; }
</style>
