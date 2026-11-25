<template>
  <div>
    <div class="pagehead">
      <div>
        <h1>菜单管理</h1>
        <p>菜单按角色动态下发，前端路由与侧边栏由后端菜单树生成</p>
      </div>
      <div class="head-actions">
        <el-button type="primary" @click="open()">新增菜单</el-button>
      </div>
    </div>

    <div class="card" style="padding:0">
      <el-table :data="rows" row-key="id" default-expand-all size="small">
        <el-table-column prop="name" label="菜单名称" min-width="200" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.type === 'DIR' ? 'primary' : row.type === 'MENU' ? 'success' : 'info'">
              {{ { DIR: '目录', MENU: '菜单', BUTTON: '按钮' }[row.type] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路由" min-width="170" />
        <el-table-column prop="perm" label="权限标识" min-width="160" />
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column label="可见" width="80">
          <template #default="{ row }"><el-tag size="small" :type="row.visible === 1 ? 'success' : 'info'">{{ row.visible === 1 ? '显示' : '隐藏' }}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button link type="primary" @click="open(row)">编辑</el-button>
            <el-button link type="primary" @click="open({ parentId: row.id, type: 'MENU' })">新增子项</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialog" :title="form.id ? '编辑菜单' : '新增菜单'" width="520px">
      <el-form :model="form" label-width="96px">
        <el-form-item label="上级菜单">
          <el-select v-model="form.parentId" style="width:200px">
            <el-option label="根目录" :value="0" />
            <el-option v-for="m in flat" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio label="DIR">目录</el-radio><el-radio label="MENU">菜单</el-radio><el-radio label="BUTTON">按钮</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="路由"><el-input v-model="form.path" placeholder="/leave/list" /></el-form-item>
        <el-form-item label="组件"><el-input v-model="form.component" placeholder="views/LeaveList" /></el-form-item>
        <el-form-item label="权限标识"><el-input v-model="form.perm" placeholder="leave:list" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort" :min="0" :max="99" /></el-form-item>
        <el-form-item label="可见"><el-switch v-model="form.visible" :active-value="1" :inactive-value="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const rows = ref([])
const dialog = ref(false)
const form = ref({})
const flat = computed(() => rows.value.flatMap((r) => [r, ...(r.children || [])]))

async function load() {
  rows.value = await api.menuTree()
}
function open(row) {
  form.value = row ? { ...row } : { parentId: 0, name: '', type: 'MENU', path: '', component: '', perm: '', sort: 10, visible: 1 }
  dialog.value = true
}
async function save() {
  await api.menuSave(form.value)
  ElMessage.success('已保存')
  dialog.value = false
  load()
}
onMounted(load)
</script>
