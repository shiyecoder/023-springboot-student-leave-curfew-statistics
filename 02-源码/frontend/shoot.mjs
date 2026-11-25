// NEW-023 验证截图脚本：无头 Chrome，逐角色逐页截图，用完即关
import puppeteer from 'puppeteer-core'
import fs from 'fs'
import path from 'path'

const BASE = 'http://127.0.0.1:5174'
const SHOTS = '/Users/xiaoxin/showcase/build/NEW-023/verify/shots'
fs.mkdirSync(SHOTS, { recursive: true })

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const consoleErrors = []

const roles = [
  { user: 's2022001', pass: '123456', tag: 'student' },
  { user: 't1001', pass: '123456', tag: 'counselor' },
  { user: 't2001', pass: '123456', tag: 'dept' },
  { user: 'd3001', pass: '123456', tag: 'dorm' },
  { user: 'admin', pass: 'admin123', tag: 'admin' }
]

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function login(page, user, pass) {
  await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' })
  await page.evaluate(() => localStorage.clear())
  await page.goto(BASE + '/login', { waitUntil: 'networkidle2' })
  await sleep(600)
  await page.evaluate(({ u, p }) => {
    const setVal = (el, v) => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set
      setter.call(el, v)
      el.dispatchEvent(new Event('input', { bubbles: true }))
      el.dispatchEvent(new Event('change', { bubbles: true }))
    }
    const ins = document.querySelectorAll('input')
    setVal(ins[0], u)
    setVal(ins[1], p)
  }, { u: user, p: pass })
  await page.evaluate(() => {
    const btns = [...document.querySelectorAll('button')]
    const b = btns.find((x) => x.innerText.replace(/\s/g, '').includes('登录'))
    b && b.click()
  })
  await sleep(1800)
}

async function shot(page, name) {
  await sleep(900)
  await page.screenshot({ path: path.join(SHOTS, name), fullPage: false })
  console.log('shot', name)
}

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: 'new',
  args: ['--headless=new', '--disable-gpu', '--no-sandbox', '--window-size=1440,900', '--font-render-hinting=none']
})

try {
  for (const r of roles) {
    const page = await browser.newPage()
    await page.setViewport({ width: 1440, height: 900 })
    page.on('console', (m) => {
      if (m.type() === 'error') consoleErrors.push(`[${r.tag}] ${m.text()}`)
    })
    page.on('pageerror', (e) => consoleErrors.push(`[${r.tag}] PAGEERROR ${e.message}`))
    page.on('response', (res) => {
      if (res.status() === 404) consoleErrors.push(`[${r.tag}] 404 ${res.url()}`)
    })

    await login(page, r.user, r.pass)

    if (r.tag === 'student') {
      await shot(page, '02_student_dashboard.png')
      await page.goto(BASE + '/leave/list', { waitUntil: 'networkidle2' })
      await shot(page, '03_student_leave_list.png')
      await page.goto(BASE + '/leave/create', { waitUntil: 'networkidle2' })
      await shot(page, '04_student_leave_form.png')
      // 打开第一条待销假单据详情
      await page.goto(BASE + '/leave/list', { waitUntil: 'networkidle2' })
      await sleep(800)
      const detailHref = await page.evaluate(() => {
        const a = [...document.querySelectorAll('a,button')].find((x) => x.innerText.trim() === '查看')
        return a ? true : false
      })
      if (detailHref) {
        await page.evaluate(() => {
          const b = [...document.querySelectorAll('button,a')].find((x) => x.innerText.trim() === '查看')
          b.click()
        })
        await sleep(1500)
        await shot(page, '05_student_leave_detail.png')
      }
      await page.goto(BASE + '/leave/return', { waitUntil: 'networkidle2' })
      await shot(page, '06_student_return.png')
      await page.goto(BASE + '/profile', { waitUntil: 'networkidle2' })
      await shot(page, '07_student_profile.png')
      await page.goto(BASE + '/stats', { waitUntil: 'networkidle2' })
      await shot(page, '07b_student_stats.png')
    }

    if (r.tag === 'counselor') {
      await page.goto(BASE + '/approval/desk', { waitUntil: 'networkidle2' })
      await shot(page, '08_counselor_desk.png')
      await page.evaluate(() => {
        const b = [...document.querySelectorAll('button')].find((x) => x.innerText.trim() === '审批')
        b && b.click()
      })
      await sleep(900)
      await shot(page, '09_counselor_approve_drawer.png')
      await page.keyboard.press('Escape')
      await page.goto(BASE + '/safety/cases', { waitUntil: 'networkidle2' })
      await shot(page, '10_counselor_cases.png')
      await page.goto(BASE + '/safety/care', { waitUntil: 'networkidle2' })
      await shot(page, '11_counselor_care.png')
      await page.goto(BASE + '/stats', { waitUntil: 'networkidle2' })
      await shot(page, '12_counselor_stats.png')
      await page.goto(BASE + '/risk/center', { waitUntil: 'networkidle2' })
      await shot(page, '12b_counselor_risk.png')
    }

    if (r.tag === 'dept') {
      await page.goto(BASE + '/approval/dept', { waitUntil: 'networkidle2' })
      await shot(page, '13_dept_approve.png')
      await page.goto(BASE + '/stats', { waitUntil: 'networkidle2' })
      await shot(page, '14_dept_stats.png')
    }

    if (r.tag === 'dorm') {
      await page.goto(BASE + '/safety/late', { waitUntil: 'networkidle2' })
      await shot(page, '15_dorm_late.png')
      await page.goto(BASE + '/leave/return', { waitUntil: 'networkidle2' })
      await shot(page, '16_dorm_verify.png')
      await page.goto(BASE + '/safety/cases', { waitUntil: 'networkidle2' })
      await shot(page, '16b_dorm_cases.png')
    }

    if (r.tag === 'admin') {
      await page.goto(BASE + '/dashboard', { waitUntil: 'networkidle2' })
      await shot(page, '17_admin_dashboard.png')
      await page.goto(BASE + '/admin/rules', { waitUntil: 'networkidle2' })
      await shot(page, '18_admin_rules.png')
      await page.goto(BASE + '/admin/users', { waitUntil: 'networkidle2' })
      await shot(page, '19_admin_users.png')
      await page.goto(BASE + '/admin/roles', { waitUntil: 'networkidle2' })
      await shot(page, '20_admin_roles.png')
      await page.goto(BASE + '/admin/menus', { waitUntil: 'networkidle2' })
      await shot(page, '21_admin_menus.png')
      await page.goto(BASE + '/risk/center', { waitUntil: 'networkidle2' })
      await shot(page, '22_admin_risk.png')
      await page.goto(BASE + '/leave/list', { waitUntil: 'networkidle2' })
      await shot(page, '23_admin_leave_list.png')
    }

    // 登录页截图（用学生初始态）
    if (r.tag === 'student') {
      await page.evaluate(() => localStorage.removeItem('token'))
      await page.goto(BASE + '/login', { waitUntil: 'networkidle2' })
      await shot(page, '01_login.png')
    }
    await page.close()
  }
} catch (e) {
  console.error('FAILED', e.message)
} finally {
  fs.writeFileSync('/Users/xiaoxin/showcase/build/NEW-023/verify/console.json', JSON.stringify(consoleErrors, null, 2))
  await browser.close()
  console.log('done, console errors:', consoleErrors.length)
}
