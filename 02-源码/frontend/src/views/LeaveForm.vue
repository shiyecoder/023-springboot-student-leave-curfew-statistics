<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>{{ isEdit ? '编辑请假申请' : '发起请假' }}</h1>
        <p>系统按请假类型与天数自动匹配审批层级与必需材料</p>
      </div>
      <div class="head-actions">
        <el-button @click="$router.back()">返回</el-button>
        <el-button :loading="saving" @click="submit(true)">保存草稿</el-button>
        <el-button type="primary" :loading="saving" @click="submit(false)">提交审批</el-button>
      </div>
    </div>

    <div class="grid2">
      <div class="card">
        <div class="card-title">基础信息</div>
        <el-form ref="formRef" :model="form" :rules="formRules" label-width="104px">
          <el-form-item label="学生">
            <el-input :model-value="`${store.user?.realName} · ${store.user?.userNo}`" disabled />
          </el-form-item>
          <el-form-item label="学院班级">
            <el-input :model-value="`${store.user?.deptName || ''} / ${store.user?.className || ''}`" disabled />
          </el-form-item>
          <el-form-item label="请假类型" prop="leaveType">
            <el-select v-model="form.leaveType" style="width:220px">
              <el-option v-for="t in types" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="开始时间" prop="startTime">
            <el-date-picker v-model="form.startTime" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:220px" />
          </el-form-item>
          <el-form-item label="结束时间" prop="endTime">
            <el-date-picker v-model="form.endTime" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:220px" />
          </el-form-item>
          <el-form-item label="请假天数">
            <el-input :model-value="days + ' 天'" disabled style="width:220px" />
            <span class="hint" style="margin-left:10px">按 10 小时折算 1 天，后端复核</span>
          </el-form-item>
          <el-form-item label="外出地点">
            <el-input v-model="form.destination" maxlength="100" show-word-limit placeholder="如：市第一人民医院 城东院区" />
          </el-form-item>
          <el-form-item label="紧急联系人">
            <el-input v-model="form.contactName" maxlength="100" placeholder="姓名与关系" style="width:200px" />
          </el-form-item>
          <el-form-item label="联系电话" prop="contactPhone">
            <el-input v-model="form.contactPhone" placeholder="11 位手机号" style="width:200px" />
          </el-form-item>
          <el-form-item label="交通方式">
            <el-select v-model="form.transport" style="width:200px">
              <el-option v-for="t in transports" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="请假事由" prop="reason">
            <el-input v-model="form.reason" type="textarea" :rows="3" maxlength="500" show-word-limit
              placeholder="请说明具体事由，不少于 5 个字" />
          </el-form-item>
        </el-form>
      </div>

      <div>
        <div class="card">
          <div class="card-title">证明材料</div>
          <el-upload drag :action="uploadUrl" :headers="uploadHeaders" name="file" :show-file-list="false"
            :on-success="onUpload" :on-error="onUploadError" accept=".jpg,.jpeg,.png,.pdf">
            <el-icon style="font-size:26px;color:#2F6B8A"><UploadFilled /></el-icon>
            <div style="margin-top:6px">点击或拖拽上传诊断证明 / 活动通知</div>
            <div class="hint">支持 JPG / PNG / PDF，单文件 ≤ 10MB；仅本人与审批人可见</div>
          </el-upload>
          <div v-if="form.attachmentPath" class="file-row">
            <el-image :src="form.attachmentPath" fit="cover" style="width:56px;height:42px;border-radius:3px" />
            <div style="flex:1">
              <div>证明材料已上传</div>
              <div class="hint">{{ form.attachmentPath }}</div>
            </div>
            <el-button size="small" type="danger" plain @click="form.attachmentPath = ''">删除</el-button>
          </div>
        </div>

        <div class="card">
          <div class="card-title">自动校验与审批层级</div>
          <div v-if="!days" class="hint">选择起止时间后显示校验结果</div>
          <el-timeline v-else>
            <el-timeline-item :type="days > 0 ? 'success' : 'danger'" :timestamp="days > 0 ? '通过' : '不通过'">
              时间顺序与天数：{{ days }} 天
            </el-timeline-item>
            <el-timeline-item type="success" timestamp="通过">联系方式格式校验</el-timeline-item>
            <el-timeline-item :type="needProof ? 'warning' : 'success'"
              :timestamp="needProof ? (form.attachmentPath ? '已上传' : '缺少材料') : '无需材料'">
              材料要求：{{ rule?.requiredMaterial || '按类型匹配' }}
            </el-timeline-item>
            <el-timeline-item type="primary" :timestamp="'规则 ' + (rule?.version || 'v3')">
              审批层级：{{ levelText }}
            </el-timeline-item>
          </el-timeline>
          <div class="notice mt">提交后系统自动计算一次「请假行为风险分层」，结果随单据留痕，供辅导员参考。</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { store } from '../store'
import { calcDays } from '../utils'

const route = useRoute()
const router = useRouter()
const formRef = ref()
const saving = ref(false)
const types = ref(['病假', '事假', '公假', '实习', '跨省外出'])
const transports = ref(['地铁', '公交', '高铁', '飞机', '私家车', '步行'])
const ruleList = ref([])
const form = ref({
  leaveType: '病假', startTime: '', endTime: '', destination: '', contactName: '',
  contactPhone: store.user?.guardianPhone || '13800000000', transport: '地铁', reason: '', attachmentPath: ''
})
const uploadUrl = '/api/upload'
const uploadHeaders = computed(() => ({ Authorization: 'Bearer ' + localStorage.getItem('token') }))
const isEdit = computed(() => !!route.params.id)
const days = computed(() => calcDays(form.value.startTime, form.value.endTime))

const rule = computed(() => {
  const list = ruleList.value.filter((r) => r.leaveType === form.value.leaveType).sort((a, b) => a.dayThreshold - b.dayThreshold)
  if (!list.length) return null
  let hit = list[0]
  for (const r of list) if (days.value > r.dayThreshold) hit = r
  return hit
})
const levelText = computed(() => {
  if (!rule.value) return '-'
  return rule.value.approvalLevel.includes('DEPT') ? '辅导员审批 → 院系审批' : '辅导员审批'
})
const needProof = computed(() => (rule.value?.requiredMaterial || '').includes('证明'))

const validateNum = (rule, value, cb) => {
  if (!value) return cb(new Error('请填写联系电话'))
  if (!/^[0-9*\-]{6,20}$/.test(value)) return cb(new Error('电话格式不正确'))
  cb()
}
const formRules = {
  leaveType: [{ required: true, message: '请选择请假类型', trigger: 'change' }],
  startTime: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  endTime: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  reason: [{ required: true, min: 5, message: '事由不少于 5 个字', trigger: 'blur' }],
  contactPhone: [{ validator: validateNum, trigger: 'blur' }]
}

function onUpload(res) {
  if (res.code === 200) {
    form.value.attachmentPath = res.data.path
    ElMessage.success('上传成功')
  } else {
    ElMessage.error(res.msg || '上传失败')
  }
}
function onUploadError() {
  ElMessage.error('上传失败，请重试')
}

async function submit(draft) {
  await formRef.value.validate()
  if (needProof.value && !form.value.attachmentPath) {
    return ElMessage.warning('该请假类型需上传' + rule.value.requiredMaterial)
  }
  if (days.value <= 0) return ElMessage.warning('结束时间必须晚于开始时间')
  saving.value = true
  try {
    const payload = { ...form.value, draft, days: days.value }
    if (isEdit.value) {
      payload.version = Number(route.query.version || 0)
      await api.leaveUpdate(route.params.id, payload)
    } else {
      await api.leaveCreate(payload)
    }
    ElMessage.success(draft ? '已保存草稿' : '已提交审批')
    router.push('/leave/list')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  const opt = await api.leaveOptions()
  types.value = opt.types
  transports.value = opt.transports
  ruleList.value = opt.rules
  if (isEdit.value) {
    const d = await api.leaveDetail(route.params.id)
    const l = d.leave
    form.value = {
      leaveType: l.leaveType, startTime: l.startTime, endTime: l.endTime, destination: l.destination,
      contactName: l.contactName, contactPhone: l.contactPhone, transport: l.transport, reason: l.reason,
      attachmentPath: l.attachmentPath
    }
    router.replace({ query: { version: l.version } })
  }
})
</script>

<style scoped>
.file-row { display: flex; align-items: center; gap: 10px; border: 1px solid #E3E8EF; border-radius: 4px; padding: 10px; margin-top: 12px; }
</style>
