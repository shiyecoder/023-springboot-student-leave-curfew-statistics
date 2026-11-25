<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>{{ greeting }}，{{ store.user?.realName }}</h1>
        <p>{{ subtitle }}</p>
      </div>
      <div class="head-actions">
        <el-select v-model="range" style="width:140px" @change="load">
          <el-option label="最近 30 天" value="30" />
          <el-option label="本季度" value="quarter" />
          <el-option label="本学年" value="year" />
        </el-select>
        <el-button v-if="isStudent" type="primary" @click="$router.push('/leave/create')">发起请假</el-button>
        <el-button v-if="isStudent" @click="$router.push('/leave/return')">返校销假</el-button>
        <el-button v-else @click="$router.push('/approval/desk')">去审批</el-button>
      </div>
    </div>

    <div class="kpis">
      <div class="kpi"><div class="lb">请假人次</div><div class="vl">{{ d.leaveCount || 0 }}</div><div class="dt">近 {{ rangeText }}</div></div>
      <div class="kpi"><div class="lb">请假人数</div><div class="vl">{{ d.studentCount || 0 }}</div><div class="dt">累计 {{ d.daysSum || 0 }} 天</div></div>
      <div class="kpi"><div class="lb">待审批</div><div class="vl" style="color:#A9761F">{{ d.pending || 0 }}</div><div class="dt">最长等待超 24h 需催办</div></div>
      <div class="kpi"><div class="lb">请假中</div><div class="vl" style="color:#2F6B8A">{{ d.onLeave || 0 }}</div><div class="dt">到期自动转待销假</div></div>
      <div class="kpi"><div class="lb">逾期未销假</div><div class="vl" style="color:#B3261E">{{ d.overdue || 0 }}</div><div class="dt">自动生成核查工单</div></div>
      <div class="kpi"><div class="lb">审批平均时效</div><div class="vl">{{ d.avgHours || 0 }}<span style="font-size:12px"> h</span></div><div class="dt">晚归 {{ d.lateCount || 0 }} 人次</div></div>
    </div>

    <div class="grid3 mt">
      <div class="card">
        <div class="card-title">请假趋势（按日）</div>
        <EChart :option="trendOpt" :height="196" />
      </div>
      <div class="card">
        <div class="card-title">请假类型分布</div>
        <EChart :option="typeOpt" :height="196" />
      </div>
      <div class="card">
        <div class="card-title">单据状态分布</div>
        <EChart :option="statusOpt" :height="196" />
      </div>
    </div>

    <div class="grid3 mt">
      <div class="card">
        <div class="card-title">晚归时段分布</div>
        <EChart :option="lateOpt" :height="176" />
      </div>
      <div class="card">
        <div class="card-title">风险分层结果分布</div>
        <EChart :option="riskOpt" :height="176" />
      </div>
      <div class="card">
        <div class="card-title">逾期排行 / 重点关注</div>
        <div v-if="focus.length === 0" class="hint" style="padding:12px 0">当前筛选条件下无重点关注学生</div>
        <div v-for="f in focus.slice(0, 4)" :key="f.name" class="focus-row">
          <span>{{ f.name }}</span>
          <span class="hint">{{ f.className }}</span>
          <el-tag :type="levelMeta(f.level).type" size="small">{{ levelMeta(f.level).text }}</el-tag>
          <span class="num">{{ f.score }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { store } from '../store'
import { levelMeta } from '../utils'
import EChart from '../components/EChart.vue'

const d = ref({})
const range = ref('30')
const focus = ref([])
const isStudent = computed(() => store.user?.roleCode === 'STUDENT')
const rangeText = computed(() => ({ 30: '30 天', quarter: '90 天', year: '365 天' }[range.value]))
const subtitle = computed(() => isStudent.value
  ? `${store.user?.className || ''} · 宿舍 ${store.user?.dormBuilding || ''} ${store.user?.dormRoom || ''}`
  : `数据更新于 ${new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })} · 统计范围按角色数据权限`)
const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 11 ? '早上好' : h < 14 ? '中午好' : h < 18 ? '下午好' : '晚上好'
})

const C = ['#1F2937', '#2F6B8A', '#3B627A', '#9AA8B6', '#C3CCD6']
const baseGrid = { left: 12, right: 16, top: 24, bottom: 6, containLabel: true }

const trendOpt = computed(() => ({
  grid: baseGrid,
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: (d.value.trend || []).map((i) => i.name), axisLine: { lineStyle: { color: '#E3E8EF' } }, axisLabel: { color: '#6B7785', fontSize: 10 } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F1F4F8' } }, axisLabel: { color: '#6B7785', fontSize: 10 } },
  series: [{ type: 'line', smooth: true, symbolSize: 4, data: (d.value.trend || []).map((i) => i.value),
    lineStyle: { width: 2, color: '#2F6B8A' }, itemStyle: { color: '#2F6B8A' }, areaStyle: { color: 'rgba(47,107,138,.08)' } }]
}))

const typeOpt = computed(() => ({
  grid: baseGrid,
  tooltip: { trigger: 'item' },
  xAxis: { type: 'category', data: (d.value.typeDist || []).map((i) => i.name), axisLabel: { color: '#6B7785', fontSize: 10 }, axisLine: { lineStyle: { color: '#E3E8EF' } } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F1F4F8' } }, axisLabel: { color: '#6B7785', fontSize: 10 } },
  series: [{ type: 'bar', barWidth: 22, data: (d.value.typeDist || []).map((i) => i.value),
    itemStyle: { color: '#2F6B8A', borderRadius: [2, 2, 0, 0] } }]
}))

const STATUS_TEXT = { DRAFT: '草稿', COUNSELOR_PENDING: '待辅导员', DEPT_PENDING: '待院系', ON_LEAVE: '请假中', RETURN_PENDING: '待销假', COMPLETED: '已销假', REJECTED: '已驳回', CANCELLED: '已取消' }
const statusOpt = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { fontSize: 10, color: '#6B7785' }, itemWidth: 8, itemHeight: 8 },
  series: [{
    type: 'pie', radius: ['46%', '68%'], center: ['50%', '42%'], avoidLabelOverlap: true,
    label: { show: false },
    data: (d.value.statusDist || []).map((i) => ({ name: STATUS_TEXT[i.name] || i.name, value: i.value })),
    color: C
  }]
}))

const lateOpt = computed(() => ({
  grid: baseGrid,
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: (d.value.lateHours || []).map((i) => i.name), axisLabel: { color: '#6B7785', fontSize: 10 }, axisLine: { lineStyle: { color: '#E3E8EF' } } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F1F4F8' } }, axisLabel: { color: '#6B7785', fontSize: 10 } },
  series: [{ type: 'bar', barWidth: 20, data: (d.value.lateHours || []).map((i) => i.value), itemStyle: { color: '#3B627A', borderRadius: [2, 2, 0, 0] } }]
}))

const riskOpt = computed(() => {
  const arr = d.value.riskDist || []
  const map = { LOW: '低关注', MID: '中关注', HIGH: '高关注' }
  return {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: '62%', center: ['50%', '50%'], label: { fontSize: 11, color: '#1F2937', formatter: '{b} {d}%' },
      data: arr.map((i) => ({ name: map[i.name] || i.name, value: i.value })), color: ['#2E7D5B', '#A9761F', '#B3261E']
    }]
  }
})

async function load() {
  d.value = await api.dashboard(range.value)
  focus.value = d.value.focusStudents || []
}
onMounted(load)
</script>

<style scoped>
.focus-row { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #F1F4F8; font-size: 12px; }
.focus-row:last-child { border-bottom: none; }
</style>
