<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>统计分析</h1>
        <p>请假类型、时长、院系趋势、审批时效、超期未归、晚归时段与核查完成率</p>
      </div>
      <div class="head-actions">
        <el-select v-model="range" style="width:140px" @change="load">
          <el-option label="最近 30 天" value="30" />
          <el-option label="本季度" value="quarter" />
          <el-option label="本学年" value="year" />
        </el-select>
        <el-button @click="$router.push('/risk/center')">风险分层明细</el-button>
      </div>
    </div>

    <div class="kpis" style="grid-template-columns:repeat(5,1fr)">
      <div class="kpi"><div class="lb">请假人次</div><div class="vl">{{ d.leaveCount || 0 }}</div><div class="dt">累计 {{ d.daysSum || 0 }} 天</div></div>
      <div class="kpi"><div class="lb">审批平均时效</div><div class="vl">{{ d.avgHours || 0 }}<span style="font-size:12px"> h</span></div><div class="dt">目标 ≤ 6h</div></div>
      <div class="kpi"><div class="lb">逾期未销假</div><div class="vl" style="color:#B3261E">{{ d.overdue || 0 }}</div><div class="dt">生成工单 {{ d.openCase || 0 }} 条</div></div>
      <div class="kpi"><div class="lb">晚归人次</div><div class="vl">{{ d.lateCount || 0 }}</div><div class="dt">有假晚归不计违规</div></div>
      <div class="kpi"><div class="lb">核查完成率</div><div class="vl">{{ rate }}%</div><div class="dt">已闭环 {{ d.closedCase || 0 }} / {{ (d.closedCase || 0) + (d.openCase || 0) }}</div></div>
    </div>

    <div class="grid2 mt">
      <div class="card"><div class="card-title">请假趋势</div><EChart :option="trendOpt" :height="240" /></div>
      <div class="card"><div class="card-title">类型占比</div><EChart :option="typeOpt" :height="240" /></div>
    </div>
    <div class="grid3 mt">
      <div class="card"><div class="card-title">院系逾期排行</div><EChart :option="deptOpt" :height="220" /></div>
      <div class="card"><div class="card-title">晚归时段</div><EChart :option="lateOpt" :height="220" /></div>
      <div class="card"><div class="card-title">风险分层结果</div><EChart :option="riskOpt" :height="220" /></div>
    </div>

    <div class="card mt" style="padding:0">
      <div style="padding:16px 16px 0" class="card-title">重点关注学生（风险分层）</div>
      <el-table :data="focus" size="small">
        <el-table-column prop="name" label="学生" width="110" />
        <el-table-column prop="className" label="班级" width="150" />
        <el-table-column prop="score" label="得分" width="90" align="right">
          <template #default="{ row }"><span class="num">{{ row.score }}</span></template>
        </el-table-column>
        <el-table-column label="等级" width="100">
          <template #default="{ row }"><el-tag size="small" :type="levelMeta(row.level).type">{{ levelMeta(row.level).text }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="suggest" label="结果解释与建议" min-width="360" show-overflow-tooltip />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { levelMeta } from '../utils'
import EChart from '../components/EChart.vue'

const d = ref({})
const range = ref('30')
const focus = ref([])
const rate = computed(() => {
  const a = d.value.closedCase || 0
  const b = (d.value.closedCase || 0) + (d.value.openCase || 0)
  return b ? Math.round((a / b) * 1000) / 10 : 0
})
const C = ['#1F2937', '#2F6B8A', '#3B627A', '#9AA8B6', '#C3CCD6']
const grid = { left: 10, right: 16, top: 20, bottom: 6, containLabel: true }
const axis = { axisLine: { lineStyle: { color: '#E3E8EF' } }, axisLabel: { color: '#6B7785', fontSize: 10 } }

const trendOpt = computed(() => ({
  grid, tooltip: { trigger: 'axis' }, xAxis: { type: 'category', data: (d.value.trend || []).map((i) => i.name), ...axis },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F1F4F8' } }, axisLabel: { color: '#6B7785', fontSize: 10 } },
  series: [{ type: 'line', smooth: true, data: (d.value.trend || []).map((i) => i.value), lineStyle: { width: 2, color: '#2F6B8A' }, itemStyle: { color: '#2F6B8A' } }]
}))
const typeOpt = computed(() => ({
  tooltip: { trigger: 'item' }, legend: { bottom: 0, textStyle: { fontSize: 10, color: '#6B7785' }, itemWidth: 8, itemHeight: 8 },
  series: [{ type: 'pie', radius: ['44%', '66%'], center: ['50%', '44%'], label: { show: false },
    data: (d.value.typeDist || []).map((i) => ({ name: i.name, value: i.value })), color: C }]
}))
const deptOpt = computed(() => ({
  grid, tooltip: { trigger: 'axis' },
  xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F1F4F8' } }, axisLabel: { color: '#6B7785', fontSize: 10 } },
  yAxis: { type: 'category', data: (d.value.deptRank || []).map((i) => i.name).reverse(), ...axis },
  series: [{ type: 'bar', barWidth: 16, data: (d.value.deptRank || []).map((i) => i.value).reverse(), itemStyle: { color: '#3B627A', borderRadius: [0, 2, 2, 0] } }]
}))
const lateOpt = computed(() => ({
  grid, tooltip: { trigger: 'axis' }, xAxis: { type: 'category', data: (d.value.lateHours || []).map((i) => i.name), ...axis },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F1F4F8' } }, axisLabel: { color: '#6B7785', fontSize: 10 } },
  series: [{ type: 'bar', barWidth: 18, data: (d.value.lateHours || []).map((i) => i.value), itemStyle: { color: '#2F6B8A', borderRadius: [2, 2, 0, 0] } }]
}))
const riskOpt = computed(() => {
  const map = { LOW: '低关注', MID: '中关注', HIGH: '高关注' }
  return {
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: '60%', label: { fontSize: 11, color: '#1F2937', formatter: '{b} {d}%' },
      data: (d.value.riskDist || []).map((i) => ({ name: map[i.name] || i.name, value: i.value })), color: ['#2E7D5B', '#A9761F', '#B3261E'] }]
  }
})

async function load() {
  d.value = await api.dashboard(range.value)
  focus.value = d.value.focusStudents || []
}
onMounted(load)
</script>
