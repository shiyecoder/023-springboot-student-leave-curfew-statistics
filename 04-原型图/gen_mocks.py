#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NEW-023 原型生成器：按角色批量产出可点击的 HTML 稿（不是截图，可直接浏览）"""
import pathlib, html

ROOT = pathlib.Path(__file__).parent
CSS = (ROOT / "mock.css").read_text()

ROLES = {
    "student": ("学生端 · 请假门户", [("首页概览", "student-home.html", "◧"),
                                    ("我的请假", "student-list.html", "☰"),
                                    ("发起请假", "student-form.html", "＋"),
                                    ("返校销假", "student-return.html", "✓"),
                                    ("我的风险画像", "student-risk.html", "◔")]),
    "counselor": ("辅导员端 · 审批与核查", [("审批工作台", "counselor-desktop.html", "◧"),
                                          ("未归核查", "counselor-cases.html", "!"),
                                          ("关怀记录", "counselor-care.html", "✎"),
                                          ("班级统计", "counselor-stats.html", "◑")]),
    "dept": ("院系端 · 学工管理", [("院系审批", "dept-approve.html", "◧"),
                                  ("院系统计", "dept-stats.html", "◑")]),
    "dorm": ("宿管端 · 值班台", [("晚归登记", "dorm-late.html", "◧"),
                                ("返校码核验", "dorm-verify.html", "⌘")]),
    "admin": ("管理端 · 系统治理", [("数据看板", "admin-dashboard.html", "◧"),
                                   ("请假规则配置", "admin-rules.html", "⚙"),
                                   ("用户管理", "admin-users.html", "☰"),
                                   ("角色管理", "admin-roles.html", "◎"),
                                   ("菜单管理", "admin-menus.html", "≡")]),
}
ROLE_LABEL = {"student": "学生 张若曦", "counselor": "辅导员 陈立", "dept": "学工负责人 王志远",
              "dorm": "宿管值班员 刘梅", "admin": "系统管理员 admin"}
ROLE_SHORT = {"student": "学生", "counselor": "辅导员", "dept": "院系", "dorm": "宿管", "admin": "管理"}


def tag(text, kind="grey"):
    return f'<span class="tag {kind}">{text}</span>'


def shell(role, active, title, crumb, body, extra=""):
    label, navs = ROLES[role]
    items = "".join(
        f'<a href="{f}" class="{"on" if n == active else ""}"><span class="ic">{i}</span>{n}</a>'
        for n, f, i in navs)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{title} · 学生请销假与晚归统计管理系统</title>
<link rel="stylesheet" href="../mock.css">{extra}</head>
<body><div class="layout">
<aside class="sidebar">
  <div class="brand"><span class="dot">勤</span>学生安全请假平台</div>
  <nav class="nav"><div class="nav-group">{label}</div>{items}
   <div class="nav-group">个人</div>
   <a href="common-profile.html"><span class="ic">◍</span>个人中心</a>
  </nav>
  <div style="padding:12px 16px;font-size:11px;color:#7C8798;border-top:1px solid #ffffff14">v1.0 · {ROLE_SHORT[role]}视图</div>
</aside>
<div class="main">
  <header class="topbar">
    <div class="crumb">{crumb}</div>
    <div class="topright">
      <span class="bell">消息<i>6</i></span><span>帮助</span>
      <span class="who"><img class="ava" src="assets/avatar-1.jpg" alt="">{ROLE_LABEL[role]}</span>
    </div>
  </header>
  <div class="content">{body}</div>
</div></div></body></html>"""


def head(title, sub, actions=""):
    return f'<div class="pagehead"><div><h1>{title}</h1><p>{sub}</p></div><div class="row">{actions}</div></div>'


def pager(total=128):
    return f"""<div class="pager"><span>共 {total} 条 · 每页
  <select class="sel" style="height:26px;min-width:64px;max-width:70px;padding:0 4px"><option>10</option><option>20</option><option>50</option></select> 条</span>
  <div class="pgs"><span class="pg">‹</span><span class="pg on">1</span><span class="pg">2</span><span class="pg">3</span><span class="pg">…</span><span class="pg">13</span><span class="pg">›</span></div></div>"""


def table(headers, rows):
    th = "".join(f"<th>{h}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def kpi(label, value, delta=""):
    return f'<div class="kpi"><div class="lb">{label}</div><div class="vl">{value}</div><div class="dt">{delta}</div></div>'


PAGES = {}
D = "2026-10-31"

# ---------------- 学生端 ----------------
student_rows = [
    ["<span class='code'>QJ202610280012</span>", "病假", "2026-10-28 08:00", "2026-10-30 18:00", "3.0", "市第一人民医院", tag("已销假", "ok"), "陈立", "2026-10-30 19:12"],
    ["<span class='code'>QJ202610260007</span>", "事假", "2026-10-26 08:00", "2026-10-26 22:00", "0.6", "校本部 · 市区", tag("请假中", "run"), "陈立", "2026-10-26 07:41"],
    ["<span class='code'>QJ202610210003</span>", "病假", "2026-10-21 08:00", "2026-10-24 18:00", "4.0", "市口腔医院", tag("待销假", "wait"), "陈立", "2026-10-24 18:30"],
    ["<span class='code'>QJ202610150009</span>", "公假", "2026-10-15 13:00", "2026-10-16 18:00", "1.5", "省大学生运动会", tag("待院系审批", "wait"), "王志远", "2026-10-15 10:02"],
    ["<span class='code'>QJ202610080021</span>", "事假", "2026-10-08 08:00", "2026-10-09 20:00", "2.0", "邻市 · 家中", tag("已驳回", "bad"), "陈立", "2026-10-08 09:15"],
    ["<span class='code'>QJ202609260014</span>", "病假", "2026-09-26 08:00", "2026-09-28 18:00", "3.0", "校医院转诊", tag("已销假", "ok"), "陈立", "2026-09-28 20:05"],
]
PAGES["student-home.html"] = shell("student", "首页概览", "首页概览", "学生端 / <b>首页概览</b>", head(
    "张若曦，晚上好", "计算机学院 · 软件工程 2201 班 · 宿舍 6 栋 412", '<button class="btn primary">发起请假</button>') + f"""
<div class="kpis" style="grid-template-columns:repeat(4,1fr)">
  {kpi("本学期请假次数", "5", "近 30 天 2 次")}{kpi("累计请假天数", "13.1", "占本学期 6.2%")}
  {kpi("待我处理", "2", "1 条待销假 · 1 条待补材料")}{kpi("晚归记录", "1", "有假晚归 1 次，不计违规")}
</div>
<div class="grid2 mt">
  <div class="card"><div class="card-title"><span class="bar"></span>未完成的请假</div>
    {table(["编号", "类型", "起止时间", "状态", "下一步"],[
      ["<span class='code'>QJ202610210003</span>","病假","10-21 → 10-24","<span class='tag wait'>待销假</span>","<a href='student-return.html'>提交返校销假</a>"],
      ["<span class='code'>QJ202610150009</span>","公假","10-15 → 10-16","<span class='tag wait'>待院系审批</span>","<span class='hint'>等待王志远审批</span>"],
      ["<span class='code'>QJ202610080021</span>","事假","10-08 → 10-09","<span class='tag bad'>已驳回</span>","<a href='student-form.html'>修改后重申</a>"]] if False else table(["编号","类型","起止时间","状态","下一步"],[
      ["<span class='code'>QJ202610210003</span>","病假","10-21 → 10-24","<span class='tag wait'>待销假</span>","<a href='student-return.html'>提交返校销假</a>"],
      ["<span class='code'>QJ202610150009</span>","公假","10-15 → 10-16","<span class='tag wait'>待院系审批</span>","<span class='hint'>等待王志远审批</span>"],
      ["<span class='code'>QJ202610080021</span>","事假","10-08 → 10-09","<span class='tag bad'>已驳回</span>","<a href='student-form.html'>修改后重申</a>"]]))}
  </div>
  <div class="card"><div class="card-title"><span class="bar"></span>安全提示</div>
    <div class="notice">你有 1 条请假将于 <b>2026-10-31 18:00</b> 到期，请返校后 2 小时内提交销假，超期将生成未归核查工单。</div>
    <div class="timeline mt">
      <div class="tl-item done"><div class="tl-t">返校码已生成</div><div class="tl-m">QJ202610280012 · 验证码 8 分钟内有效 · 2026-10-30 19:02</div></div>
      <div class="tl-item done"><div class="tl-t">宿管核验通过</div><div class="tl-m">刘梅 · 6 栋门禁 · 2026-10-30 19:12</div></div>
      <div class="tl-item"><div class="tl-t">辅导员确认归档</div><div class="tl-m">陈立 · 待处理</div></div>
    </div>
  </div>
</div>""")

PAGES["student-list.html"] = shell("student", "我的请假", "我的请假", "学生端 / <b>我的请假</b>", head(
    "我的请假", "共 12 条记录 · 支持按类型、状态、时间区间筛选", '<button class="btn">导出当前筛选</button><button class="btn primary">发起请假</button>') + f"""
<div class="card"><div class="filters">
  <div class="field"><label>请假类型</label><select class="sel"><option>全部</option><option>病假</option><option>事假</option><option>公假</option></select></div>
  <div class="field"><label>审批状态</label><select class="sel"><option>全部</option><option>待辅导员审批</option><option>待院系审批</option><option>请假中</option><option>待销假</option><option>已销假</option></select></div>
  <div class="field"><label>开始时间</label><input class="inp sm" value="2026-05-01"></div>
  <div class="field"><label>结束时间</label><input class="inp sm" value="2026-10-31"></div>
  <div class="row" style="margin-left:auto"><button class="btn primary">查询</button><button class="btn">重置</button></div>
</div></div>
<div class="mt">{table(["申请编号","类型","开始时间","结束时间","天数","外出地点","审批状态","当前审批人","最近更新","操作"], [
  [r[0], r[1], r[2], r[3], f"<span class='num'>{r[4]}</span>", r[5], r[6], r[7], f"<span class='num'>{r[8]}</span>",
   f"<span class='ops'><a href='student-detail.html'>查看</a>{'<a href=student-return.html>销假</a>' if '待销假' in r[6] else '<a href=student-form.html>延期</a>'}</span>"]
  for r in student_rows])}
{pager(12)}</div>""")

PAGES["student-form.html"] = shell("student", "发起请假", "发起请假", "学生端 / 我的请假 / <b>发起请假</b>", head(
    "发起请假", "系统将按规则自动匹配审批层级与必需材料", '<button class="btn">保存草稿</button><button class="btn primary">提交审批</button>') + """
<div class="grid2">
  <div class="card"><div class="card-title"><span class="bar"></span>基础信息</div>
    <div class="field mt8"><label>学生</label><input class="inp" value="张若曦 · 20220113" disabled style="min-width:360px;max-width:520px"></div>
    <div class="field mt8"><label>学院班级</label><input class="inp" value="计算机学院 / 软件工程 2201 班" disabled style="min-width:360px;max-width:520px"></div>
    <div class="field mt8"><label>请假类型 <span style="color:#B3261E">*</span></label>
      <select class="sel" style="min-width:200px"><option>病假</option><option>事假</option><option>公假</option><option>实习</option><option>跨省外出</option></select></div>
    <div class="row mt8"><div class="field"><label>开始时间 <span style="color:#B3261E">*</span></label><input class="inp sm" value="2026-11-02 08:00"></div>
      <div class="field"><label>结束时间 <span style="color:#B3261E">*</span></label><input class="inp sm" value="2026-11-04 18:00"></div></div>
    <div class="field mt8"><label>请假天数（自动计算）</label><input class="inp sm" value="2.5 天" disabled></div>
    <div class="field mt8"><label>外出地点</label><input class="inp" value="市第一人民医院 · 城东院区" style="min-width:360px;max-width:520px"></div>
    <div class="row mt8"><div class="field"><label>紧急联系人</label><input class="inp sm" value="张建国（父亲）"></div>
      <div class="field"><label>联系电话</label><input class="inp sm" value="138****6621"></div></div>
    <div class="field mt8"><label>交通方式</label><select class="sel" style="min-width:200px"><option>地铁</option><option>高铁</option><option>私家车</option><option>飞机</option></select></div>
    <div class="field mt8"><label>请假事由 <span style="color:#B3261E">*</span></label>
      <textarea class="inp" style="height:76px;min-width:420px;max-width:520px;padding:8px 10px">需住院复查，医生建议休息三天，附诊断证明。</textarea></div>
  </div>
  <div>
    <div class="card"><div class="card-title"><span class="bar"></span>证明材料</div>
      <div style="border:1px dashed #C6D5E0;border-radius:6px;padding:22px;text-align:center;background:#FBFCFE">
        <div style="font-size:20px;color:#2F6B8A">⇪</div>
        <div class="mt8">点击或拖拽上传诊断证明</div>
        <div class="hint mt8">支持 JPG / PNG / PDF，单文件 ≤ 10MB；仅本人与审批人可见</div>
      </div>
      <div class="row mt8" style="border:1px solid #E3E8EF;border-radius:4px;padding:10px">
        <img src="assets/proof-1.jpg" style="width:56px;height:42px;object-fit:cover;border-radius:3px" alt="">
        <div style="flex:1"><div>诊断证明-20261031.jpg</div><div class="hint">386 KB · 已上传</div></div>
        <button class="btn sm danger">删除</button>
      </div>
    </div>
    <div class="card"><div class="card-title"><span class="bar"></span>自动校验结果</div>
      <div class="timeline">
        <div class="tl-item done"><div class="tl-t">时间不重叠</div><div class="tl-m">与 12 条历史记录比对，无冲突</div></div>
        <div class="tl-item done"><div class="tl-t">无超期未销假</div><div class="tl-m">最近一次已销假 2026-10-30</div></div>
        <div class="tl-item done"><div class="tl-t">材料齐备</div><div class="tl-m">病假 ≥ 2 天需诊断证明，已上传</div></div>
        <div class="tl-item"><div class="tl-t" style="color:#A9761F">审批层级：辅导员 → 院系（3 天 ≥ 2 天阈值）</div><div class="tl-m">规则版本 v3 · 2026-09-01 生效</div></div>
      </div>
    </div>
  </div>
</div>""")

PAGES["student-detail.html"] = shell("student", "我的请假", "请假详情", "学生端 / 我的请假 / <b>QJ202610150009</b>", head(
    "QJ202610150009", "公假 · 省大学生运动会 · 提交于 2026-10-14 20:16", tag("待院系审批", "wait")) + """
<div class="groups">
  <div class="g-item"><div class="lb">申请编号</div><div class="vl code">QJ202610150009</div></div>
  <div class="g-item"><div class="lb">当前状态</div><div class="vl"><span class="tag wait">待院系审批</span></div></div>
  <div class="g-item"><div class="lb">学生</div><div class="vl">张若曦 · 计算机学院 / 软件工程 2201</div></div>
  <div class="g-item"><div class="lb">当前责任人</div><div class="vl">王志远（院系学工负责人）</div></div>
  <div class="g-item"><div class="lb">请假时间</div><div class="vl num">2026-10-15 13:00 → 2026-10-16 18:00（1.5 天）</div></div>
  <div class="g-item"><div class="lb">外出地点</div><div class="vl">省体育中心 · 跨市</div></div>
  <div class="g-item"><div class="lb">紧急联系人</div><div class="vl">李教练 139****0021</div></div>
  <div class="g-item"><div class="lb">创建 / 更新</div><div class="vl num">2026-10-14 20:16 / 2026-10-15 10:02</div></div>
</div>
<div class="grid2 mt">
  <div class="card"><div class="card-title"><span class="bar"></span>审批时间轴</div><div class="timeline">
    <div class="tl-item done"><div class="tl-t">提交申请</div><div class="tl-m">张若曦 · 2026-10-14 20:16</div></div>
    <div class="tl-item done"><div class="tl-t">辅导员审批通过</div><div class="tl-m">陈立 · 意见：情况属实，同意外出 · 2026-10-15 09:40</div></div>
    <div class="tl-item"><div class="tl-t">院系审批（进行中）</div><div class="tl-m">王志远 · 待处理 · 已等待 1 天 2 小时</div></div>
    <div class="tl-item"><div class="tl-t">返校销假</div><div class="tl-m">待发起</div></div>
  </div></div>
  <div class="card"><div class="card-title"><span class="bar"></span>证明材料与关联单据</div>
    <div class="row" style="border:1px solid #E3E8EF;border-radius:4px;padding:10px"><img src="assets/proof-2.jpg" style="width:56px;height:42px;object-fit:cover;border-radius:3px" alt=""><div style="flex:1"><div>运动会通知.pdf</div><div class="hint">210 KB · 仅本人与审批人可见</div></div><a>预览</a></div>
    <div class="mt8 hint">关联单据</div>
    <div class="mt8"><a>QJ202610080021（驳回后重申）</a> · 返校销假：未生成</div>
    <div class="card-title mt"><span class="bar"></span>可执行操作</div>
    <div class="row"><button class="btn">申请延期</button><button class="btn danger">取消请假</button><button class="btn ghost">催办</button></div>
    <div class="hint mt8">离校前可取消；请假中提交延期将按新总时长重新匹配审批层级。</div>
  </div>
</div>""")

PAGES["student-return.html"] = shell("student", "返校销假", "返校销假", "学生端 / <b>返校销假</b>", head(
    "返校销假", "QJ202610210003 · 病假 · 2026-10-21 08:00 → 2026-10-24 18:00", tag("待销假", "wait")) + """
<div class="grid2">
  <div class="card"><div class="card-title"><span class="bar"></span>返校信息</div>
    <div class="field mt8"><label>实际返校时间 <span style="color:#B3261E">*</span></label><input class="inp sm" value="2026-10-24 17:36"></div>
    <div class="field mt8"><label>返校方式</label><select class="sel" style="min-width:200px"><option>地铁</option><option>校车</option><option>私家车</option></select></div>
    <div class="field mt8"><label>返校情况说明</label><textarea class="inp" style="height:72px;min-width:380px;max-width:480px;padding:8px 10px">已返校，身体恢复良好，已在宿管处刷卡进楼。</textarea></div>
    <div class="notice mt">销假后原审批时间与材料不可修改，仅可追加备注。</div>
    <div class="row mt"><button class="btn">暂存</button><button class="btn primary">生成返校码并提交</button></div>
  </div>
  <div class="card"><div class="card-title"><span class="bar"></span>限时返校码</div>
    <div style="text-align:center;padding:10px 0">
      <div style="display:inline-block;padding:14px 18px;border:1px solid #E3E8EF;border-radius:6px;background:#fff">
        <img src="assets/qrcode.svg" style="width:132px;height:132px" alt="返校码"></div>
      <div class="mt8 code" style="font-size:20px;letter-spacing:4px">8 4 2 7 1 9</div>
      <div class="hint mt8">有效期至 2026-10-24 18:06（10 分钟）· 仅供宿管值班员核验</div>
    </div>
    <div class="card-title"><span class="bar"></span>核验方式</div>
    <div class="timeline">
      <div class="tl-item done"><div class="tl-t">宿管扫码核验</div><div class="tl-m">刘梅 · 6 栋门禁 · 推荐方式</div></div>
      <div class="tl-item"><div class="tl-t">辅导员人工核销</div><div class="tl-m">返校码过期或设备异常时使用</div></div>
    </div>
  </div>
</div>""")

PAGES["student-risk.html"] = shell("student", "我的风险画像", "我的风险画像", "学生端 / <b>我的风险画像</b>", head(
    "我的风险画像", "请假行为风险分层 · 规则版本 v3 · 计算于 2026-10-30 20:00", tag("低关注", "ok")) + """
<div class="kpis" style="grid-template-columns:repeat(4,1fr)">
  <div class="kpi"><div class="lb">综合得分</div><div class="vl">28.5</div><div class="dt">满分 100 · 越高越需关注</div></div>
  <div class="kpi"><div class="lb">关注等级</div><div class="vl" style="color:#2E7D5B">低关注</div><div class="dt">阈值：0-40 低 / 40-70 中 / 70+ 高</div></div>
  <div class="kpi"><div class="lb">近 30 天请假</div><div class="vl">2 次</div><div class="dt">权重 20%</div></div>
  <div class="kpi"><div class="lb">晚归次数</div><div class="vl">1 次</div><div class="dt">权重 20% · 有假晚归不计违规</div></div>
</div>
<div class="card mt"><div class="card-title"><span class="bar"></span>得分构成（可解释）</div>
  <div class="bars">
    <div style="height:38%"><span>请假频次 8.0</span></div><div style="height:24%"><span>累计天数 4.5</span></div>
    <div style="height:16%"><span>晚归 3.0</span></div><div style="height:44%"><span>逾期销假 9.0</span></div>
    <div style="height:12%"><span>请假类型 2.0</span></div><div style="height:10%"><span>驳回 2.0</span></div>
  </div>
  <div class="hint mt">每项得分 = 归一化指标 × 权重 × 100，缺失项不参与计算并在结果中标注。</div>
</div>
<div class="grid2 mt">
  <div class="card"><div class="card-title"><span class="bar"></span>主要影响因素</div>
    <div class="timeline">
      <div class="tl-item done"><div class="tl-t">近 30 天请假 2 次（偏低）</div><div class="tl-m">低于专业平均 3.1 次</div></div>
      <div class="tl-item done"><div class="tl-t">累计 13.1 天（中等）</div><div class="tl-m">含 1 次 4 天病假</div></div>
      <div class="tl-item"><div class="tl-t" style="color:#A9761F">1 次逾期销假（需改进）</div><div class="tl-m">2026-09-28 超期 2 小时，已核销</div></div>
    </div>
  </div>
  <div class="card"><div class="card-title"><span class="bar"></span>未满足条件与改进建议</div>
    <ul style="padding-left:18px;color:#3B4A5A">
      <li>请假结束后 2 小时内提交销假可避免逾期标记</li>
      <li>返校码有效期仅 10 分钟，进楼前再生成</li>
      <li>连续 3 晚晚归将升级为中关注</li>
    </ul>
    <div class="notice mt">本结果为业务辅助参考，不替代辅导员判断；可申请人工复核。</div>
  </div>
</div>""")

# ---------------- 辅导员 ----------------
counselor_rows = [
    ["<span class='code'>QJ202610300018</span>", "李昊然", "软件 2201", "病假", "10-30 → 11-02", "3.0", tag("待辅导员审批", "wait"), "剩余 5h20m"],
    ["<span class='code'>QJ202610300015</span>", "周文琪", "软件 2202", "事假", "10-31 → 10-31", "0.5", tag("待辅导员审批", "wait"), "剩余 18h"],
    ["<span class='code'>QJ202610290011</span>", "赵一鸣", "软件 2201", "跨省外出", "11-01 → 11-05", "5.0", tag("待辅导员审批", "wait"), "剩余 3h05m"],
    ["<span class='code'>QJ202610290006</span>", "孙可", "软件 2203", "病假", "10-29 → 10-31", "2.5", tag("待院系审批", "run"), "已流转"],
    ["<span class='code'>QJ202610280004</span>", "陈思远", "软件 2202", "事假", "10-28 → 10-28", "1.0", tag("待销假", "wait"), "超期 1 天"],
]
PAGES["counselor-desktop.html"] = shell("counselor", "审批工作台", "审批工作台", "辅导员端 / <b>审批工作台</b>", head(
    "审批工作台", "软件工程 2201-2203 · 待我审批 3 条 · 超期未归 2 条", '<button class="btn">批量通过</button><button class="btn primary">批量驳回</button>') + f"""
<div class="kpis" style="grid-template-columns:repeat(5,1fr)">
  {kpi("待我审批","3","最紧急剩余 3h05m")}{kpi("本月审批","46","平均时效 3.6 小时")}
  {kpi("待销假","4","超期 1 条")}{kpi("未归核查","2","1 条处理中")}{kpi("重点关注学生","6","较上月 -1")}
</div>
<div class="card mt"><div class="row" style="justify-content:space-between">
  <div class="row"><span class="tag run">全部 58</span><span class="tag">待我审批 3</span><span class="tag">已流转 12</span><span class="tag bad">超期 1</span></div>
  <div class="row"><select class="sel" style="min-width:160px"><option>按紧急度排序</option><option>按提交时间</option></select></div>
</div></div>
<div class="mt">{table(["申请编号","学生","班级","类型","起止时间","天数","状态","时效","操作"],[
  [r[0],r[1],r[2],r[3],r[4],f"<span class='num'>{r[5]}</span>",r[6],f"<span class='hint'>{r[7]}</span>",
   "<span class='ops'><a href='student-detail.html'>查看</a><a>通过</a><a>驳回</a></span>"] for r in counselor_rows])}
{pager(58)}</div>
<div class="drawer"><div class="dh"><span>审批 · QJ202610300018</span><span class="hint">✕</span></div>
  <div class="db">
    <div class="hint">学生</div><div>李昊然 · 软件 2201 · 6 栋 408</div>
    <div class="hint mt8">请假</div><div>病假 10-30 08:00 → 11-02 18:00（3.0 天）</div>
    <div class="hint mt8">事由</div><div>急性肠胃炎，附门诊病历。</div>
    <div class="hint mt8">风险分层</div><div>得分 46.0 · <span class="tag wait">中关注</span> · 近 30 天 3 次请假</div>
    <div class="hint mt8">审批意见 <span style="color:#B3261E">*</span></div>
    <textarea class="inp" style="width:100%;height:64px;padding:8px;min-width:0">已电话核实本人与家长，同意请假。</textarea>
  </div>
  <div class="df"><button class="btn">退回修改</button><button class="btn primary">通过</button></div>
</div>""")

PAGES["counselor-cases.html"] = shell("counselor", "未归核查", "未归核查", "辅导员端 / <b>未归核查</b>", head(
    "未归核查", "超期未销假 1 · 夜不归 1 · 连续晚归 1", '<button class="btn">生成工单</button>') + f"""
<div class="card"><div class="filters">
  <div class="field"><label>异常类型</label><select class="sel"><option>全部</option><option>超期未销假</option><option>夜不归</option><option>连续晚归</option></select></div>
  <div class="field"><label>处理状态</label><select class="sel"><option>全部</option><option>待处理</option><option>处理中</option><option>已闭环</option></select></div>
  <div class="field"><label>负责人</label><select class="sel"><option>全部</option><option>陈立</option></select></div>
  <div class="row" style="margin-left:auto"><button class="btn primary">查询</button><button class="btn">重置</button></div>
</div></div>
<div class="mt">{table(["工单编号","学生","异常类型","等级","触发依据","状态","负责人","截止时间","操作"],[
  ["<span class='code'>YC20261030002</span>","陈思远","超期未销假",tag("高","bad"),"QJ202610280004 超期 1 天未销假",tag("处理中","run"),"陈立","2026-11-01 12:00","<span class='ops'><a href='counselor-care.html'>核查</a><a>关闭</a></span>"],
  ["<span class='code'>YC20261031001</span>","王梓萱","夜不归",tag("高","bad"),"23:30 未返寝且无有效请假",tag("待处理","wait"),"陈立","2026-10-31 23:59","<span class='ops'><a href='counselor-care.html'>核查</a><a>转派</a></span>"],
  ["<span class='code'>YC20261029003</span>","刘子豪","连续晚归",tag("中","wait"),"近 14 天内晚归 3 次",tag("已闭环","ok"),"陈立","2026-10-30 18:00","<span class='ops'><a>查看</a></span>"],
])}{pager(9)}</div>
<div class="card mt"><div class="card-title"><span class="bar"></span>工单 YC20261030002 · 时间轴</div><div class="timeline">
  <div class="tl-item done"><div class="tl-t">系统自动生成工单</div><div class="tl-m">超期未销假规则触发 · 2026-10-30 20:00</div></div>
  <div class="tl-item done"><div class="tl-t">电话核查</div><div class="tl-m">陈立 · 学生称已在返校途中 · 2026-10-30 20:35</div></div>
  <div class="tl-item"><div class="tl-t">等待宿管返校码核验</div><div class="tl-m">截止 2026-11-01 12:00</div></div>
</div></div>""")

PAGES["counselor-care.html"] = shell("counselor", "关怀记录", "关怀记录", "辅导员端 / 未归核查 / <b>关怀记录</b>", head(
    "关怀记录", "工单 YC20261030002 · 陈思远 · 软件 2202", '<button class="btn primary">新增关怀记录</button>') + """
<div class="grid2">
  <div class="card"><div class="card-title"><span class="bar"></span>新增记录</div>
    <div class="field mt8"><label>核查方式 <span style="color:#B3261E">*</span></label><select class="sel" style="min-width:200px"><option>电话联系学生</option><option>联系家长</option><option>宿舍走访</option><option>同学侧面了解</option></select></div>
    <div class="field mt8"><label>联系时间</label><input class="inp sm" value="2026-10-31 19:40"></div>
    <div class="field mt8"><label>学生情况</label><textarea class="inp" style="height:70px;min-width:380px;max-width:480px;padding:8px">学生在返程高铁上，因车次延误导致超期，情绪平稳。</textarea></div>
    <div class="field mt8"><label>后续处置 <span style="color:#B3261E">*</span></label><textarea class="inp" style="height:70px;min-width:380px;max-width:480px;padding:8px">要求 22:00 前到楼并生成返校码，明日上午补交车票凭证。</textarea></div>
    <div class="row mt"><button class="btn">取消</button><button class="btn primary">保存</button></div>
  </div>
  <div class="card"><div class="card-title"><span class="bar"></span>历史记录（4 条）</div><div class="timeline">
    <div class="tl-item done"><div class="tl-t">电话联系学生 · 陈立</div><div class="tl-m">2026-10-31 19:40 · 已在返程，车次延误</div></div>
    <div class="tl-item done"><div class="tl-t">联系家长 · 陈立</div><div class="tl-m">2026-10-30 21:10 · 家长确认学生明日返校</div></div>
    <div class="tl-item done"><div class="tl-t">宿舍走访 · 刘梅</div><div class="tl-m">2026-10-30 20:50 · 室友称其回家取衣物</div></div>
    <div class="tl-item done"><div class="tl-t">工单生成 · 系统</div><div class="tl-m">2026-10-30 20:00 · 超期未销假</div></div>
  </div></div>
</div>""")

PAGES["counselor-stats.html"] = shell("counselor", "班级统计", "班级统计", "辅导员端 / <b>班级统计</b>", head(
    "班级统计", "软件工程 2201-2203 · 最近 30 天", '<select class="sel" style="min-width:140px"><option>最近 30 天</option><option>本月</option><option>本季度</option></select>') + f"""
<div class="kpis" style="grid-template-columns:repeat(4,1fr)">
  <div class="kpi"><div class="lb">请假人数 / 总人数</div><div class="vl">37 / 128</div><div class="dt">占比 28.9%</div></div>
  <div class="kpi"><div class="lb">审批平均时效</div><div class="vl">3.6h</div><div class="dt">较上月 -0.8h</div></div>
  <div class="kpi"><div class="lb">逾期销假</div><div class="vl">3</div><div class="dt">已全部核查</div></div>
  <div class="kpi"><div class="lb">晚归人次</div><div class="vl">14</div><div class="dt">有假晚归 9 次不计违规</div></div>
</div>
<div class="grid2 mt">
  <div class="chart"><h4>请假类型分布</h4><div class="sub">近 30 天 · 共 52 条</div>
    <div class="donut"></div>
    <div class="legend"><span><i style="background:#1F2937"></i>病假 42%</span><span><i style="background:#2F6B8A"></i>事假 26%</span><span><i style="background:#3B627A"></i>公假 18%</span><span><i style="background:#9AA8B6"></i>其他 14%</span></div>
  </div>
  <div class="chart"><h4>晚归时段分布</h4><div class="sub">按返寝时间聚合</div>
    <div class="bars"><div style="height:35%"><span>22-23</span></div><div style="height:78%"><span>23-24</span></div><div style="height:52%"><span>00-01</span></div><div style="height:22%"><span>01-02</span></div><div style="height:10%"><span>02+</span></div></div>
  </div>
</div>
<div class="card mt"><div class="card-title"><span class="bar"></span>重点关注学生</div>
  {table(["学生","班级","得分","等级","主要因素","最近事件","操作"], [
    ["陈思远","软件 2202","<span class='num'>76.5</span>",tag("高","bad"),"逾期 2 次 + 晚归 3 次","10-30 超期未销假","<a href='counselor-care.html'>核查</a>"],
    ["王梓萱","软件 2201","<span class='num'>71.0</span>",tag("高","bad"),"夜不归 1 次 + 连续晚归","10-31 23:30 未返寝","<a href='counselor-care.html'>核查</a>"],
    ["李昊然","软件 2201","<span class='num'>46.0</span>",tag("中","wait"),"近 30 天 3 次请假","10-30 病假申请","<a>查看</a>"],
  ])}</div>""")

# ---------------- 院系 ----------------
PAGES["dept-approve.html"] = shell("dept", "院系审批", "院系审批", "院系端 / <b>院系审批</b>", head(
    "院系审批", "计算机学院 · 待我审批 2 条（长假 / 跨省 / 特殊类型）", '<button class="btn">导出</button>') + f"""
<div class="card"><div class="filters">
  <div class="field"><label>审批状态</label><select class="sel"><option>待院系审批</option><option>全部</option></select></div>
  <div class="field"><label>请假类型</label><select class="sel"><option>全部</option><option>跨省外出</option><option>公假</option></select></div>
  <div class="field"><label>院系</label><select class="sel"><option>计算机学院</option></select></div>
  <div class="row" style="margin-left:auto"><button class="btn primary">查询</button></div>
</div></div>
<div class="mt">{table(["申请编号","学生","班级","类型","起止时间","天数","辅导员意见","状态","操作"],[
  ["<span class='code'>QJ202610290011</span>","赵一鸣","软件 2201","跨省外出","11-01 → 11-05","5.0","陈立 · 同意，已核家长","<span class='tag wait'>待院系审批</span>","<span class='ops'><a href='student-detail.html'>查看</a><a>通过</a><a>驳回</a></span>"],
  ["<span class='code'>QJ202610150009</span>","张若曦","软件 2201","公假","10-15 → 10-16","1.5","陈立 · 情况属实","<span class='tag wait'>待院系审批</span>","<span class='ops'><a href='student-detail.html'>查看</a><a>通过</a><a>驳回</a></span>"],
  ["<span class='code'>QJ202610120004</span>","吴桐","计科 2201","病假","10-12 → 10-20","8.0","陈立 · 同意","<span class='tag ok'>已通过</span>","<span class='ops'><a>查看</a></span>"],
])}{pager(24)}</div>
<div class="card mt"><div class="card-title"><span class="bar"></span>审批依据</div>
  <div class="notice">规则 v3：请假 ≥ 3 天 或 跨省外出 或 特殊类型，需追加院系审批；当前记录命中「跨省外出 + 5 天」双条件。</div>
</div>""")

PAGES["dept-stats.html"] = shell("dept", "院系统计", "院系统计", "院系端 / <b>院系统计</b>", head(
    "院系统计", "计算机学院 · 2026-2027 学年第一学期", '<select class="sel" style="min-width:140px"><option>本学期</option><option>本月</option><option>本季度</option></select>') + f"""
<div class="kpis" style="grid-template-columns:repeat(5,1fr)">
  <div class="kpi"><div class="lb">请假人数</div><div class="vl">312</div><div class="dt">占在册 24.6%</div></div>
  <div class="kpi"><div class="lb">请假总天数</div><div class="vl">1,284</div><div class="dt">人均 4.1 天</div></div>
  <div class="kpi"><div class="lb">审批时效</div><div class="vl">5.2h</div><div class="dt">院系节点 2.1h</div></div>
  <div class="kpi"><div class="lb">逾期销假</div><div class="vl">11</div><div class="dt">闭环率 90.9%</div></div>
  <div class="kpi"><div class="lb">核查完成率</div><div class="vl">96.4%</div><div class="dt">目标 ≥ 95%</div></div>
</div>
<div class="grid2 mt">
  <div class="chart"><h4>院系请假趋势</h4><div class="sub">按月 · 2026-05 至 2026-10</div>
    <div class="spark"><svg viewBox="0 0 300 100" preserveAspectRatio="none">
      <polyline points="0,72 50,60 100,66 150,42 200,34 250,48 300,28" fill="none" stroke="#2F6B8A" stroke-width="2"/>
      <polyline points="0,86 50,80 100,72 150,74 200,58 250,62 300,50" fill="none" stroke="#9AA8B6" stroke-width="1.5" stroke-dasharray="3 3"/>
    </svg></div>
    <div class="legend"><span><i style="background:#2F6B8A"></i>计算机学院</span><span><i style="background:#9AA8B6"></i>全校均值</span></div>
  </div>
  <div class="chart"><h4>审批时效对比（小时）</h4><div class="sub">辅导员 / 院系 / 全校</div>
    <div class="bars"><div style="height:70%"><span>辅导员 3.6</span></div><div style="height:42%"><span>院系 2.1</span></div><div style="height:88%"><span>全校 4.4</span></div></div>
  </div>
</div>
<div class="card mt"><div class="card-title"><span class="bar"></span>班级排行</div>
  {table(["班级","请假人次","总天数","逾期","晚归","核查完成率","重点关注"],[
    ["软件 2201","18","62","1","4","100%","2"],["软件 2202","15","48","2","6","94%","3"],
    ["软件 2203","11","37","0","2","100%","1"],["计科 2201","22","79","3","5","91%","3"]] if False else table(["班级","请假人次","总天数","逾期","晚归","核查完成率","重点关注"],[
    ["软件 2201","18","62","1","4","100%","2"],["软件 2202","15","48","2","6","94%","3"],
    ["软件 2203","11","37","0","2","100%","1"],["计科 2201","22","79","3","5","91%","3"]]))}
</div>""")

# ---------------- 宿管 ----------------
PAGES["dorm-late.html"] = shell("dorm", "晚归登记", "晚归登记", "宿管端 / <b>晚归登记</b>", head(
    "晚归登记", "6 栋 · 值班员刘梅 · 2026-10-31 19:40", '<button class="btn primary">新增登记</button>') + f"""
<div class="grid2">
  <div class="card"><div class="card-title"><span class="bar"></span>登记表单</div>
    <div class="field mt8"><label>学生 <span style="color:#B3261E">*</span></label><input class="inp" placeholder="学号或姓名，支持刷卡" style="min-width:320px;max-width:420px"></div>
    <div class="field mt8"><label>返寝时间 <span style="color:#B3261E">*</span></label><input class="inp sm" value="2026-10-31 23:42"></div>
    <div class="field mt8"><label>晚归原因</label><select class="sel" style="min-width:200px"><option>实习加班</option><option>交通延误</option><option>就医</option><option>其他</option></select></div>
    <div class="field mt8"><label>请假核验</label>
      <div class="row"><input class="inp sm" value="自动匹配：QJ202610260007（事假 至 22:00）" style="min-width:320px"><span class="tag ok">有有效请假</span></div>
      <div class="hint mt8">有效请假期间晚归不计入违规，但保留验证记录。</div></div>
    <div class="field mt8"><label>现场说明</label><textarea class="inp" style="height:64px;min-width:320px;max-width:420px;padding:8px">学生出示请假单，22:10 后返寝，已口头提醒。</textarea></div>
    <div class="row mt"><button class="btn">取消</button><button class="btn primary">提交登记</button></div>
  </div>
  <div class="card"><div class="card-title"><span class="bar"></span>今晚登记（6 条）</div>
    {table(["时间","学生","宿舍","原因","请假","是否违规"], [
      ["23:42","赵一鸣","6-412","交通延误","有（至 22:00）","<span class='tag ok'>否</span>"],
      ["23:20","王梓萱","6-305","未说明","无","<span class='tag bad'>是 · 已生成工单</span>"],
      ["22:51","孙可","6-208","就医","有（至 23:00）","<span class='tag ok'>否</span>"],
      ["22:33","刘子豪","6-411","实习加班","无","<span class='tag bad'>是</span>"],
      ["22:18","周文琪","6-302","交通延误","有","<span class='tag ok'>否</span>"],
      ["22:05","陈思远","6-210","其他","无","<span class='tag bad'>是</span>"],
    ])}</div>
</div>""")

PAGES["dorm-verify.html"] = shell("dorm", "返校码核验", "返校码核验", "宿管端 / <b>返校码核验</b>", head(
    "返校码核验", "扫描学生限时返校码，核验后写入销假记录", tag("值班中", "ok")) + f"""
<div class="grid2">
  <div class="card"><div class="card-title"><span class="bar"></span>扫码 / 输入核验码</div>
    <div class="field mt8"><label>返校码（6 位数字）</label><input class="inp" value="842719" style="font-size:20px;letter-spacing:6px;height:44px;min-width:240px;max-width:280px;font-variant-numeric:tabular-nums"></div>
    <div class="row mt"><button class="btn primary">核验</button><button class="btn">手动核销</button></div>
    <div class="card" style="background:#EFF7F3;border-color:#BEDCCD;margin-top:16px">
      <div style="font-weight:600;color:#2E7D5B">核验通过</div>
      <div class="mt8">张若曦 · 软件 2201 · 6 栋 412</div>
      <div class="hint mt8">对应请假 QJ202610210003 · 病假 · 应返 10-24 18:00 · 实际 10-24 17:36 · 未超期</div>
      <div class="hint">核验人：刘梅 · 2026-10-24 17:38 · 已写入销假记录</div>
    </div>
  </div>
  <div class="card"><div class="card-title"><span class="bar"></span>今日核验记录（12 条）</div>
    {table(["时间","学生","请假编号","核验方式","结果"], [
      ["17:38","张若曦","QJ202610210003","扫码","<span class='tag ok'>通过</span>"],
      ["16:12","孙可","QJ202610290006","扫码","<span class='tag ok'>通过</span>"],
      ["15:40","吴桐","QJ202610120004","人工核销","<span class='tag wait'>码过期 · 人工</span>"],
      ["14:05","李昊然","QJ202610300018","扫码","<span class='tag ok'>通过</span>"],
    ])}
    <div class="notice mt">返校码有效期 10 分钟，超时需重新生成或由辅导员人工核销，人工核销必须填写原因（≥5 字）。</div>
  </div>
</div>""")

# ---------------- 管理端 ----------------
PAGES["admin-dashboard.html"] = shell("admin", "数据看板", "学生安全数据看板", "管理端 / <b>数据看板</b>", head(
    "学生安全数据看板", "全校 · 最近 30 天 · 数据更新于 19:00", '<select class="sel" style="min-width:140px"><option>最近 30 天</option><option>本月</option><option>本季度</option><option>本学年</option></select><button class="btn">导出 PDF</button>') + """
<div class="kpis">
  <div class="kpi"><div class="lb">请假人数</div><div class="vl">1,246</div><div class="dt"><span class="up">↑ 4.2%</span> 环比</div></div>
  <div class="kpi"><div class="lb">审批平均时效</div><div class="vl">4.4h</div><div class="dt"><span class="down">↓ 0.6h</span> 环比</div></div>
  <div class="kpi"><div class="lb">逾期销假</div><div class="vl">37</div><div class="dt">闭环 34 条 · 91.9%</div></div>
  <div class="kpi"><div class="lb">晚归人数</div><div class="vl">218</div><div class="dt">有假晚归 132 次</div></div>
  <div class="kpi"><div class="lb">请假类型占比</div><div class="vl">42%</div><div class="dt">病假最高</div></div>
  <div class="kpi"><div class="lb">重点关注人数</div><div class="vl">64</div><div class="dt"><span class="down">↓ 3</span> 人</div></div>
</div>
<div class="grid3 mt" style="grid-template-columns:1.3fr 1fr 1fr">
  <div class="chart"><h4>请假趋势</h4><div class="sub">按日 · 近 30 天</div>
    <div class="spark"><svg viewBox="0 0 300 100" preserveAspectRatio="none">
      <polyline points="0,80 30,72 60,76 90,58 120,64 150,44 180,52 210,38 240,46 270,30 300,36" fill="none" stroke="#2F6B8A" stroke-width="2"/>
      <polyline points="0,88 30,84 60,86 90,78 120,80 150,70 180,74 210,66 240,70 270,60 300,64" fill="none" stroke="#9AA8B6" stroke-width="1.5"/>
    </svg></div></div>
  <div class="chart"><h4>状态分布</h4><div class="sub">全部在途单据</div><div class="donut"></div>
    <div class="legend"><span><i style="background:#1F2937"></i>请假中</span><span><i style="background:#2F6B8A"></i>待审批</span><span><i style="background:#3B627A"></i>待销假</span><span><i style="background:#9AA8B6"></i>其他</span></div></div>
  <div class="chart"><h4>责任单位排行</h4><div class="sub">逾期未销假</div>
    <div class="bars"><div style="height:82%"><span>计科</span></div><div style="height:64%"><span>软件</span></div><div style="height:48%"><span>电子</span></div><div style="height:30%"><span>外语</span></div><div style="height:18%"><span>其他</span></div></div></div>
</div>
<div class="grid3 mt">
  <div class="chart"><h4>晚归时段</h4><div class="sub">按返寝小时</div>
    <div class="bars"><div style="height:30%"><span>22</span></div><div style="height:72%"><span>23</span></div><div style="height:50%"><span>00</span></div><div style="height:20%"><span>01</span></div><div style="height:8%"><span>02+</span></div></div></div>
  <div class="chart"><h4>创新模块结果分布</h4><div class="sub">风险分层 · 共 1,246 人次</div>
    <div class="bars"><div style="height:86%"><span>低 68%</span></div><div style="height:52%"><span>中 24%</span></div><div style="height:18%"><span>高 8%</span></div></div></div>
  <div class="chart"><h4>核查完成率</h4><div class="sub">异常工单闭环</div>
    <div style="font-size:34px;font-weight:600;padding-top:14px;font-variant-numeric:tabular-nums">96.4%</div>
    <div class="hint">已完成 214 / 应完成 222 · 目标 95%</div>
    <div class="spark" style="height:56px;margin-top:14px"><svg viewBox="0 0 300 40" preserveAspectRatio="none">
      <polyline points="0,32 50,28 100,24 150,26 200,18 250,14 300,10" fill="none" stroke="#2E7D5B" stroke-width="2"/></svg></div></div>
</div>""")

PAGES["admin-rules.html"] = shell("admin", "请假规则配置", "请假规则配置", "管理端 / <b>请假规则配置</b>", head(
    "请假规则配置", "审批层级规则 + 风险分层权重 · 当前生效 v3（2026-09-01）", '<button class="btn">历史版本</button><button class="btn primary">保存并发布</button>') + f"""
<div class="grid2">
  <div class="card"><div class="card-title"><span class="bar"></span>审批层级规则</div>
    {table(["请假类型","天数阈值","外出范围","必需材料","审批层级","启用"],[
      ["病假","≤ 2 天","市内","诊断证明","辅导员","<span class='tag ok'>是</span>"],
      ["病假","&gt; 2 天","不限","诊断证明 + 病历","辅导员 → 院系","<span class='tag ok'>是</span>"],
      ["事假","≤ 1 天","市内","无","辅导员","<span class='tag ok'>是</span>"],
      ["公假","不限","不限","活动通知","辅导员 → 院系","<span class='tag ok'>是</span>"],
      ["跨省外出","不限","跨省","家长确认 + 行程","辅导员 → 院系","<span class='tag ok'>是</span>"],
    ])}
    <div class="notice mt">阈值修改后仅影响新提交的申请；已在途单据按提交时的规则版本执行。</div>
  </div>
  <div class="card"><div class="card-title"><span class="bar"></span>风险分层权重（合计 100%）</div>
    <div class="row"><div class="field"><label>近 30 天请假次数</label><input class="inp sm" value="20%"></div><div class="field"><label>累计天数</label><input class="inp sm" value="20%"></div></div>
    <div class="row mt8"><div class="field"><label>晚归次数</label><input class="inp sm" value="20%"></div><div class="field"><label>逾期销假次数</label><input class="inp sm" value="25%"></div></div>
    <div class="row mt8"><div class="field"><label>请假类型</label><input class="inp sm" value="10%"></div><div class="field"><label>审批驳回次数</label><input class="inp sm" value="5%"></div></div>
    <div class="card-title mt"><span class="bar"></span>等级阈值</div>
    <div class="row"><div class="field"><label>低关注上限</label><input class="inp sm" value="40"></div><div class="field"><label>中关注上限</label><input class="inp sm" value="70"></div></div>
    <div class="notice mt">权重合计必须 = 100%，否则不允许发布；每次修改生成新版本号并记录生效时间。</div>
    <div class="hint mt8">版本记录：v1 2026-03-01 · v2 2026-06-15 · v3 2026-09-01（当前）</div>
  </div>
</div>
<div class="card mt"><div class="card-title"><span class="bar"></span>推荐采纳率与人工调整率</div>
  <div class="kpis" style="grid-template-columns:repeat(4,1fr)">
    <div class="kpi"><div class="lb">计算总人次</div><div class="vl">1,246</div><div class="dt">近 30 天</div></div>
    <div class="kpi"><div class="lb">推荐采纳率</div><div class="vl">91.2%</div><div class="dt">未调整即采纳</div></div>
    <div class="kpi"><div class="lb">人工调整率</div><div class="vl">8.8%</div><div class="dt">全部填写原因</div></div>
    <div class="kpi"><div class="lb">调整后风险下降</div><div class="vl">62%</div><div class="dt">后续 30 天无异常</div></div>
  </div>
</div>""")

PAGES["admin-users.html"] = shell("admin", "用户管理", "用户管理", "管理端 / <b>用户管理</b>", head(
    "用户管理", "全校账号 1,286 个 · 启用 1,271 · 停用 15", '<button class="btn">批量导入</button><button class="btn primary">新增用户</button>') + f"""
<div class="card"><div class="filters">
  <div class="field"><label>姓名 / 学号</label><input class="inp sm" placeholder="输入关键字"></div>
  <div class="field"><label>角色</label><select class="sel"><option>全部</option><option>学生</option><option>辅导员</option><option>院系负责人</option><option>宿管</option></select></div>
  <div class="field"><label>院系</label><select class="sel"><option>全部</option><option>计算机学院</option><option>电子信息学院</option></select></div>
  <div class="field"><label>状态</label><select class="sel"><option>全部</option><option>启用</option><option>停用</option></select></div>
  <div class="row" style="margin-left:auto"><button class="btn primary">查询</button><button class="btn">重置</button></div>
</div></div>
<div class="mt">{table(["账号","姓名","学号/工号","角色","院系 / 班级","宿舍","联系电话","状态","最近登录","操作"],[
  ["<span class='code'>admin</span>","系统管理员","A0001","管理员","信息中心","-","138****0001",tag("启用","ok"),"2026-10-31 19:02","<span class='ops'><a>编辑</a><a>重置密码</a></span>"],
  ["<span class='code'>s20220113</span>","张若曦","20220113","学生","计算机学院 / 软件 2201","6-412","138****6621",tag("启用","ok"),"2026-10-31 18:40","<span class='ops'><a>编辑</a><a>停用</a></span>"],
  ["<span class='code'>t1002</span>","陈立","T1002","辅导员","计算机学院","-","139****2201",tag("启用","ok"),"2026-10-31 19:10","<span class='ops'><a>编辑</a><a>停用</a></span>"],
  ["<span class='code'>t2001</span>","王志远","T2001","院系负责人","计算机学院","-","139****3302",tag("启用","ok"),"2026-10-31 16:22","<span class='ops'><a>编辑</a><a>停用</a></span>"],
  ["<span class='code'>d3001</span>","刘梅","D3001","宿管","后勤保障部 / 6 栋","-","137****8801",tag("启用","ok"),"2026-10-31 19:35","<span class='ops'><a>编辑</a><a>停用</a></span>"],
  ["<span class='code'>s20220208</span>","陈思远","20220208","学生","计算机学院 / 软件 2202","6-210","136****5521",tag("停用","grey"),"2026-10-12 08:10","<span class='ops'><a>编辑</a><a>启用</a></span>"],
])}{pager(1286)}</div>""")

PAGES["admin-roles.html"] = shell("admin", "角色管理", "角色管理", "管理端 / <b>角色管理</b>", head(
    "角色管理", "5 个角色 · 数据范围分为本人 / 本班级 / 本院系 / 全校", '<button class="btn primary">新增角色</button>') + f"""
<div class="grid2">
  <div class="card"><div class="card-title"><span class="bar"></span>角色列表</div>
  {table(["角色编码","角色名称","数据范围","用户数","操作"],[
    ["<span class='code'>STUDENT</span>","学生","本人","1,204","<span class='ops'><a>分配菜单</a><a>编辑</a></span>"],
    ["<span class='code'>COUNSELOR</span>","辅导员 / 班主任","本班级","42","<span class='ops'><a>分配菜单</a><a>编辑</a></span>"],
    ["<span class='code'>DEPT_HEAD</span>","院系学工负责人","本院系","12","<span class='ops'><a>分配菜单</a><a>编辑</a></span>"],
    ["<span class='code'>DORM</span>","宿管值班员","本楼栋","18","<span class='ops'><a>分配菜单</a><a>编辑</a></span>"],
    ["<span class='code'>ADMIN</span>","系统管理员","全校","3","<span class='ops'><a>分配菜单</a><a>编辑</a></span>"],
  ])}</div>
  <div class="card"><div class="card-title"><span class="bar"></span>为「辅导员」分配菜单</div>
    <div style="border:1px solid #E3E8EF;border-radius:4px;padding:12px">
      <div><label><input type="checkbox" checked> 审批工作台</label></div>
      <div style="padding-left:20px"><label><input type="checkbox" checked> 待我审批</label> <label><input type="checkbox" checked> 批量审批</label></div>
      <div class="mt8"><label><input type="checkbox" checked> 未归核查</label></div>
      <div style="padding-left:20px"><label><input type="checkbox" checked> 生成工单</label> <label><input type="checkbox"> 批量派发</label></div>
      <div class="mt8"><label><input type="checkbox" checked> 关怀记录</label></div>
      <div class="mt8"><label><input type="checkbox" checked> 班级统计</label></div>
      <div class="mt8" style="color:#6B7785"><label><input type="checkbox" disabled> 菜单管理（系统内置，不可分配）</label></div>
    </div>
    <div class="row mt"><button class="btn">重置</button><button class="btn primary">保存权限</button></div>
  </div>
</div>""")

PAGES["admin-menus.html"] = shell("admin", "菜单管理", "菜单管理", "管理端 / <b>菜单管理</b>", head(
    "菜单管理", "菜单按角色动态下发，前端路由由后端菜单树生成", '<button class="btn primary">新增菜单</button>') + f"""
<div class="card">{table(["菜单名称","类型","路由","权限标识","排序","可见","操作"],[
  ["<span style='padding-left:0'>审批工作台</span>","目录","/counselor","counselor:desk","1",tag("显示","ok"),"<span class='ops'><a>编辑</a><a>新增子项</a></span>"],
  ["<span style='padding-left:20px'>待我审批</span>","菜单","/counselor/pending","leave:approve","1",tag("显示","ok"),"<span class='ops'><a>编辑</a><a>删除</a></span>"],
  ["<span style='padding-left:20px'>批量审批</span>","按钮","-","leave:batch","2",tag("隐藏","grey"),"<span class='ops'><a>编辑</a><a>删除</a></span>"],
  ["<span style='padding-left:0'>未归核查</span>","目录","/cases","case:list","2",tag("显示","ok"),"<span class='ops'><a>编辑</a><a>新增子项</a></span>"],
  ["<span style='padding-left:0'>晚归登记</span>","菜单","/dorm/late","late:add","3",tag("显示","ok"),"<span class='ops'><a>编辑</a><a>删除</a></span>"],
  ["<span style='padding-left:0'>请假规则配置</span>","菜单","/admin/rules","rule:config","8",tag("显示","ok"),"<span class='ops'><a>编辑</a><a>删除</a></span>"],
])}
<div class="notice mt">按需求「隐藏菜单管理选项」：菜单管理仅对管理员可见，且不出现在角色分配菜单的树中。</div></div>""")

# ---------------- 登录 / 个人中心 ----------------
PAGES["login.html"] = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>登录 · 学生请销假与晚归统计管理系统</title>
<link rel="stylesheet" href="../mock.css"></head><body>
<div class="login">
  <div class="left">
    <div>
      <div class="brand" style="border:none;padding:0"><span class="dot">勤</span>学生安全请假平台</div>
      <h2 style="margin-top:46px">请假有据<br>返校有码<br>安全有数</h2>
      <p>从请假申请、分级审批、限时返校码到晚归核查与关怀记录，形成学生外出安全管理的完整闭环。</p>
      <div class="badges"><span>分级审批</span><span>限时返校码</span><span>晚归核查</span><span>风险分层</span></div>
    </div>
    <div class="duty">技术支持：信息中心 · 24 小时值班电话 0571-8888 0000</div>
  </div>
  <div class="right"><div class="form-box">
    <div class="tabs"><span class="on">账号登录</span><span>扫码登录</span></div>
    <h3>欢迎回来</h3><div class="sub">请使用学号 / 工号登录，连续 5 次失败将锁定 10 分钟</div>
    <div class="fi"><label>学号 / 工号</label><input value="s20220113"></div>
    <div class="fi"><label>密码</label><input type="password" value="123456"></div>
    <div class="rows"><label><input type="checkbox" checked> 记住账号</label><a>忘记密码</a></div>
    <button class="btn primary" style="width:100%;height:40px;justify-content:center">登 录</button>
    <div class="hint mt" style="text-align:center">测试账号：admin / admin123 · t1002 / 123456 · d3001 / 123456</div>
  </div></div>
</div></body></html>"""

PAGES["common-profile.html"] = shell("student", "个人中心", "个人中心", "个人 / <b>个人中心</b>", head(
    "个人中心", "账号 s20220113 · 最近登录 2026-10-31 18:40", '<button class="btn primary">保存修改</button>') + """
<div class="grid2">
  <div class="card"><div class="card-title"><span class="bar"></span>基本资料</div>
    <div class="row"><img class="ava" style="width:64px;height:64px" src="assets/avatar-1.jpg" alt="">
      <div><button class="btn sm">更换头像</button><div class="hint mt8">JPG / PNG ≤ 2MB，上传后右上角同步</div></div></div>
    <div class="field mt"><label>姓名</label><input class="inp" value="张若曦" style="min-width:320px;max-width:420px"></div>
    <div class="field mt8"><label>手机号</label><input class="inp" value="138****6621" style="min-width:320px;max-width:420px"></div>
    <div class="field mt8"><label>紧急联系人</label><input class="inp" value="张建国（父亲）138****6621" style="min-width:320px;max-width:420px"></div>
    <div class="field mt8"><label>宿舍</label><input class="inp" value="6 栋 412" disabled style="min-width:320px;max-width:420px"></div>
  </div>
  <div class="card"><div class="card-title"><span class="bar"></span>修改密码</div>
    <div class="field mt8"><label>原密码</label><input class="inp" type="password" value="········" style="min-width:320px;max-width:420px"></div>
    <div class="field mt8"><label>新密码</label><input class="inp" type="password" style="min-width:320px;max-width:420px"></div>
    <div class="hint mt8">至少 8 位，包含字母与数字；密码使用 BCrypt 存储，任何接口不返回密码字段。</div>
    <div class="card-title mt"><span class="bar"></span>最近操作</div>
    <div class="timeline">
      <div class="tl-item done"><div class="tl-t">提交返校销假</div><div class="tl-m">QJ202610280012 · 2026-10-30 19:02</div></div>
      <div class="tl-item done"><div class="tl-t">登录系统</div><div class="tl-m">2026-10-31 18:40 · 192.168.1.36</div></div>
    </div>
  </div>
</div>""")

# ---- write pages (design/pages 下放独立可打开的副本) ----
count = 0
for name, content in PAGES.items():
    (ROOT / name).write_text(content)
    # 独立稿：内联样式，可单独打开
    inline = content.replace('<link rel="stylesheet" href="../mock.css">',
                             "<style>\n" + CSS + "\n</style>")
    (ROOT / "pages" / name).write_text(inline)
    count += 1
print("pages:", count)
