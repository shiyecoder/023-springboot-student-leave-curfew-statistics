import { reactive } from 'vue'
import { api } from './api'

// 轻量全局状态：当前用户与菜单（避免引入额外状态库）
export const store = reactive({ user: null, menus: [], loaded: false })

export async function loadUser(force = false) {
  if (store.loaded && !force) return store
  const data = await api.me()
  store.user = data.user
  store.menus = data.menus || []
  store.loaded = true
  return store
}

export function setAvatar(path) {
  if (store.user) store.user.avatar = path
}

export function logout() {
  localStorage.removeItem('token')
  store.user = null
  store.menus = []
  store.loaded = false
}
