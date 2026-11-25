<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>晚归登记</h1>
        <p>{{ store.user?.dormBuilding || '6 栋' }} · 值班员 {{ store.user?.realName }} · 有效请假期间晚归不计违规，但保留验证记录</p>
      </div>
      <div class="head-actions">
        <el-tag type="warning">今晚登记 {{ rows.length }} 条</el-tag>
      </div>
    </div>

    <div class="grid2">
      <div class="card">
        <div class="card-title">新增晚归登记</div>
        <el-form :model="form" label-width="96px">
          <el-form-item label="学生">
            <el-select v-model="form.studentId" filterable remote :remote-method="searchStudent"
              placeholder="输入姓名或学号搜索" style="width:260px" @change="onStudent">
              <el-option v-for="s in students" :key="s.id" :label="`${s.realName} · ${s.userNo} · ${s.className}`" :value="s.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="返寝时间">
            <el-date-picker v-model="form.returnTime" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:220px" />
          </el-form-item>
          <el-form-item label="晚归原因">
            <el-select v-model="form.reason" style="width:200px">
              <el-option v-for="r in ['实习加班','交通延误','就医','其他']" :key="r" :label="r" :value="r" />
            </el-select>
          </el-form-item>
          <el-form-item label="现场照片">
            <el-upload :action="uploadUrl" :headers="headers" name="file" :show-file-list="false"
              :on-success="(res) => (form.imagePath = res.data.path)" accept=".jpg,.jpeg,.png">
              <el-button size="small">上传现场照片</el-button>
            </el-upload>
            <el-image v-if="form.imagePath" :src="form.imagePath" style="width:56px;height:42px;margin-left:10px;border-radius:3px" fit="cover" />
          </el-form-item>
          <el-form-item label="现场说明">
            <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="如：已出示请假单，口头提醒按时返寝" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="submit">提交登记</el-button>
            <span class="hint" style="margin-left:10px">提交后系统自动匹配有效请假并判定是否违规</span>
          </el-form-item>
        </el-form>
      </div>

      <div class="card">
        <div class="card-title">登记记录</div>
        <el-table :data="rows" size="small" v-loading="loading">
          <el-table-column label="返寝时间" min-width="140">
            <template #default="{ row }">{{ formatTime(row.returnTime) }}</template>
          </el-table-column>
          <el-table-column prop="studentName" label="学生" width="80" />
          <el-table-column prop="dorm" label="宿舍" width="90" />
          <el-table-column prop="reason" label="原因" width="90" />
          <el-table-column label="请假" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.hasLeave === 1 ? 'success' : 'info'">{{ row.hasLeave === 1 ? '有有效请假' : '无请假' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="违规" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="row.isViolation === 1 ? 'danger' : 'success'">{{ row.isViolation === 1 ? '是' : '否' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="照片" width="70">
            <template #default="{ row }">
              <el-image v-if="row.imagePath" :src="row.imagePath" :preview-src-list="[row.imagePath]" fit="cover"
                style="width:42px;height:30px;border-radius:3px" preview-teleported />
            </template>
          </el-table-column>
        </el-table>
        <el-pagination class="mt8" v-model:current-page="q.page" :page-size="q.size" :total="total"
          layout="prev, pager, next" small @current-change="load" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { store } from '../store'
import { formatTime } from '../utils'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const students = ref([])
const q = ref({ page: 1, size: 8 })
const uploadUrl = '/api/upload'
const headers = computed(() => ({ Authorization: 'Bearer ' + localStorage.getItem('token') }))
const form = ref({
  studentId: null, returnTime: new Date().toISOString().slice(0, 19).replace('T', ' '),
  reason: '交通延误', remark: '', imagePath: ''
})

async function searchStudent(kw) {
  students.value = await api.studentOptions(kw)
}
async function load() {
  loading.value = true
  try {
    const page = await api.latePage(q.value)
    rows.value = page.records
    total.value = page.total
  } finally {
    loading.value = false
  }
}
const onStudent = () => {}
async function submit() {
  if (!form.value.studentId) return ElMessage.warning('请选择学生')
  if (!form.value.returnTime) return ElMessage.warning('请填写返寝时间')
  saving.value = true
  try {
    const res = await api.lateAdd(form.value)
    ElMessage.success(res.isViolation === 1 ? '已登记：违规晚归，已通知辅导员' : '已登记：有效请假期间晚归，不计违规')
    form.value = { studentId: null, returnTime: form.value.returnTime, reason: '交通延误', remark: '', imagePath: '' }
    load()
  } finally {
    saving.value = false
  }
}
onMounted(() => {
  load()
  searchStudent('')
})
</script>
