// NEW-023 演示录制：CDP Page.startScreencast 抓帧 -> ffmpeg 合成 1920x1080 mp4
import puppeteer from 'puppeteer-core'
import fs from 'fs'
import path from 'path'

const BASE = 'http://127.0.0.1:5174'
const OUT = '/Users/xiaoxin/showcase/build/NEW-023/demo'
const FRAMES = path.join(OUT, 'frames')
fs.rmSync(FRAMES, { recursive: true, force: true })
fs.mkdirSync(FRAMES, { recursive: true })

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: 'new',
  args: ['--headless=new', '--disable-gpu', '--no-sandbox', '--window-size=1920,1080', '--hide-scrollbars']
})
const page = await browser.newPage()
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 })

const client = await page.createCDPSession()
const frames = []
let lastSaved = 0
await client.send('Page.enable')
await client.send('Page.startScreencast', { format: 'jpeg', quality: 82, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 })
client.on('Page.screencastFrame', async (e) => {
  const now = Date.now()
  if (now - lastSaved >= 220) {
    lastSaved = now
    const name = `f${String(frames.length).padStart(5, '0')}.jpg`
    fs.writeFileSync(path.join(FRAMES, name), Buffer.from(e.data, 'base64'))
    frames.push({ name, ts: now })
  }
  try {
    await client.send('Page.screencastFrameAck', { sessionId: e.sessionId })
  } catch (_) {}
})

async function step(fn, ms = 1600) {
  await fn()
  await sleep(ms)
}

async function login(user, pass) {
  await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' })
  await page.evaluate(() => localStorage.clear())
  await page.goto(BASE + '/login', { waitUntil: 'networkidle2' })
  await sleep(700)
  await page.evaluate(({ u, p }) => {
    const setVal = (el, v) => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set
      setter.call(el, v)
      el.dispatchEvent(new Event('input', { bubbles: true }))
    }
    const ins = document.querySelectorAll('input')
    setVal(ins[0], u)
    setVal(ins[1], p)
  }, { u: user, p: pass })
  await sleep(900)
  await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => x.innerText.replace(/\s/g, '').includes('登录'))
    b && b.click()
  })
  await sleep(1600)
}

const go = async (p) => page.goto(BASE + p, { waitUntil: 'networkidle2' })

try {
  // 1. 学生端
  await login('s2022001', '123456')
  await sleep(4800)                                   // 工作台
  await go('/leave/list'); await sleep(4500)          // 我的请假
  await page.evaluate(() => {
    const b = [...document.querySelectorAll('button,a')].find((x) => x.innerText.trim() === '查看')
    b && b.click()
  })
  await sleep(5200)                                   // 详情
  await go('/leave/create'); await sleep(4800)        // 发起请假
  await go('/leave/return'); await sleep(4800)        // 返校销假
  await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => x.innerText.includes('生成返校码'))
    b && b.click()
  })
  await sleep(2600)                                   // 返校码 + 二维码
  await go('/stats'); await sleep(4500)
  await go('/profile'); await sleep(3600)

  // 2. 辅导员
  await login('t1001', '123456')
  await go('/approval/desk'); await sleep(4800)
  await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => x.innerText.trim() === '审批')
    b && b.click()
  })
  await sleep(2600)                                   // 审批抽屉
  await page.keyboard.press('Escape')
  await go('/safety/cases'); await sleep(4800)
  await go('/safety/care'); await sleep(4500)
  await go('/risk/center'); await sleep(4800)

  // 3. 院系负责人
  await login('t2001', '123456')
  await go('/approval/dept'); await sleep(4800)
  await go('/stats'); await sleep(4500)

  // 4. 宿管
  await login('d3001', '123456')
  await go('/safety/late'); await sleep(5200)
  await go('/leave/return'); await sleep(4800)
  await go('/safety/cases'); await sleep(4800)

  // 5. 管理员
  await login('admin', 'admin123')
  await go('/dashboard'); await sleep(2600)
  await go('/admin/rules'); await sleep(4800)
  await go('/admin/users'); await sleep(4800)
  await go('/admin/roles'); await sleep(4800)
  await go('/admin/menus'); await sleep(1600)
  await go('/risk/center'); await sleep(4800)

  // 回到登录页收尾
  await page.evaluate(() => localStorage.clear())
  await go('/login'); await sleep(2500)
} catch (e) {
  console.error('RECORD FAILED:', e.message)
} finally {
  await client.send('Page.stopScreencast')
  await sleep(300)
  // 生成 concat 清单：每帧时长 = 与下一帧的真实间隔，最后一帧停 2s
  const lines = []
  for (let i = 0; i < frames.length; i++) {
    const next = frames[i + 1] ? frames[i + 1].ts : frames[i].ts + 2000
    const dur = Math.max(0.1, Math.min(10, (next - frames[i].ts) / 1000))
    lines.push(`file 'frames/${frames[i].name}'`)
    lines.push(`duration ${dur.toFixed(3)}`)
  }
  if (frames.length) lines.push(`file 'frames/${frames[frames.length - 1].name}'`)
  fs.writeFileSync(path.join(OUT, 'frames.txt'), lines.join('\n'))
  fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify({ frames: frames.length, startedAt: new Date().toISOString() }, null, 2))
  await browser.close()
  console.log('frames:', frames.length)
}
