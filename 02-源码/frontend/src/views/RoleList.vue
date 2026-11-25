<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>角色管理</h1>
        <p>角色、数据范围与菜单分配 · 菜单权限与按钮权限分开控制</p>
      </div>
    </div>

    <div class="grid2">
      <div class="card" style="padding:0">
        <div style="padding:16px" class="card-title">角色列表</div>
        <el-table :data="roles" size="small">
          <el-table-column prop="code" label="角色编码" min-width="120" />
          <el-table-column prop="name" label="角色名称" min-width="130" />
          <el-table-column label="数据范围" width="110">
            <template #default="{ row }">{{ scopeText[row.dataScope] || row.dataScope }}</template>
          </el-table-column>
          <el-table-column prop="userCount" label="用户数" width="90" align="right" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }"><el-button link type="primary" @click="pick(row)">分配菜单</el-button></template>
          </el-table-column>
        </el-table>
      </div>

      <div class="card">
        <div class="card-title">为「{{ current?.name || '-' }}」分配菜单</div>
        <el-tree ref="treeRef" :data="tree" show-checkbox node-key="id" :props="{ label: 'name', children: 'children' }"
          :default-checked-keys="checked" style="max-height:420px;overflow:auto" />
        <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:14px">
          <el-button @click="pick(current)">重置</el-button>
          <el-button type="primary" @click="save">保存权限</el-button>
        </div>
        <div class="notice mt">「菜单管理」为系统内置，不出现在角色分配树中，仅管理员可见。</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const scopeText = { SELF: '本人', CLASS: '本班级', DEPT: '本院系', ALL: '全校' }
const roles = ref([])
const current = ref(null)
const tree = ref([])
const checked = ref([])
const treeRef = ref()

async function load() {
  roles.value = await api.roleList()
  const t = await api.menuTree()
  // 需求：隐藏「菜单管理」选项，不参与角色分配
  tree.value = t.filter((m) => m.name !== '菜单管理')
  if (!current.value) current.value = roles.value[0]
  if (current.value) {
    checked.value = await api.roleMenus(current.value.id)
  }
}
async function pick(row) {
  current.value = row
  checked.value = await api.roleMenus(row.id)
}
async function save() {
  const ids = treeRef.value.getCheckedKeys().concat(treeRef.value.getHalfCheckedKeys())
  await api.roleAssign(current.value.id, ids)
  ElMessage.success('菜单权限已保存，用户下次登录生效')
}
onMounted(load)
</script>
