"""扩展3:数据大屏页面 —— 科技风背景、动态粒子、流光边框、超宽屏与移动端自适应。

特点:始终使用暗色科技风;不带筛选器(大屏用于展示,展示全年数据 + 实时订单流)。
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import alerts
import realtime
from common import ANNUAL_TARGET, COUNT_JS, DARK, PALETTE, WEEKDAYS, css, dark_css, kpi_card, load

T = DARK
CY = "#22D3EE"
st.markdown(css(T), unsafe_allow_html=True)
st.markdown(dark_css(T), unsafe_allow_html=True)

BIG_CSS = """
<style>
@property --a { syntax:'<angle>'; inherits:false; initial-value:0deg; }
@keyframes spin { to { --a: 360deg; } }
@keyframes glow { 0%,100% { text-shadow:0 0 12px rgba(34,211,238,.55); } 50% { text-shadow:0 0 28px rgba(34,211,238,.95); } }
@keyframes scan { 0% { background-position:0 0; } 100% { background-position:0 60px; } }
html { font-size: clamp(13px, 0.85vw + 6px, 24px); }                       /* 随屏宽缩放:手机 13px → 超宽屏 24px */
html { background-color:#060D1A !important; min-height:100%; }
body { background: radial-gradient(ellipse at 50% -10%, #0F2A4A 0%, #060D1A 55%, #03070F 100%) fixed !important; min-height:100vh; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: transparent !important; }
.stApp {
  background-image: linear-gradient(rgba(34,211,238,.045) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(34,211,238,.045) 1px, transparent 1px) !important;
  background-size: 48px 48px !important; }
[data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stSidebarCollapsedControl"] { display:none !important; }
.block-container { max-width: 100% !important; padding: 1rem 1.6rem 2rem !important; }
.bs-title { text-align:center; margin:0 0 .4rem; }
.bs-title h1 { font-size:2rem; letter-spacing:.35em; margin:0; padding:0; color:#E0F7FF !important;
  animation: glow 3s ease-in-out infinite; }
.bs-title .sub { color:#7DD3FC; font-size:.9rem; letter-spacing:.2em; margin-top:.2rem; }
.bs-title .bar { height:3px; width:46%; margin:.6rem auto 0; border-radius:3px;
  background: linear-gradient(90deg, transparent, #22D3EE, #3B82F6, #22D3EE, transparent); }
.bs-clock { color:#7DD3FC; font-variant-numeric: tabular-nums; }
/* KPI:科技风 */
.kpi.bs { background: rgba(13,25,45,.72); border:1px solid rgba(34,211,238,.35); border-left:4px solid #22D3EE;
  backdrop-filter: blur(4px); }
.kpi.bs .value { font-size:2.1rem; color:#E0F7FF; text-shadow:0 0 14px rgba(34,211,238,.5); }
.kpi.bs .label { color:#7DD3FC; letter-spacing:.1em; }
.kpi.warn.bs .value { color:#FBBF24; } .kpi.crit.bs .value { color:#F87171; }
/* 卡片:半透明 + 流光边框 */
[class*="st-key-bs_"] { position:relative; background: rgba(13,25,45,.72) !important; border:1px solid rgba(34,211,238,.22) !important;
  border-radius:12px; padding:.5rem .8rem .3rem; backdrop-filter: blur(4px); box-shadow: 0 0 22px rgba(34,211,238,.08) inset; }
[class*="st-key-bs_"]::before { content:''; position:absolute; inset:-1px; border-radius:13px; padding:2px; pointer-events:none;
  background: conic-gradient(from var(--a), transparent 0 72%, rgba(34,211,238,.95) 88%, transparent 100%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0); animation: spin 7s linear infinite; }
[class*="st-key-bs_"]::after { content:''; position:absolute; left:-1px; top:-1px; width:16px; height:16px; pointer-events:none;
  border-top:3px solid #22D3EE; border-left:3px solid #22D3EE; border-top-left-radius:12px; }
.feed { width:100%; font-size:.82rem; border-collapse:collapse; }
.feed td { padding:.28rem .3rem; border-bottom:1px solid rgba(34,211,238,.12); color:#CBD5E1; white-space:nowrap; }
.feed tr:first-child td { color:#E0F7FF; animation: fadeUp .6s ease both; }
.tag { padding:1px 8px; border-radius:99px; font-size:.72rem; }
.tag.ok { background:rgba(74,222,128,.15); color:#4ADE80; } .tag.rf { background:rgba(248,113,113,.15); color:#F87171; }
.tag.cc { background:rgba(251,191,36,.15); color:#FBBF24; }
.bignum { font-size:2.6rem; font-weight:800; color:#E0F7FF; text-shadow:0 0 18px rgba(34,211,238,.6); line-height:1.1; }
@media (min-width: 2200px) { .bs-title h1 { font-size:3.2rem; } .block-container { padding: 1.4rem 3rem !important; } }
@media (max-width: 900px) { .bs-title h1 { font-size:1.5rem; letter-spacing:.15em; } .bs-title .bar { width:80%; } }
</style>
"""
st.markdown(BIG_CSS, unsafe_allow_html=True)

# ---- 动态粒子背景 + 实时时钟(JS)。#bs-marker 在页面里存在时才运行,切页后自动销毁 ----
PARTICLE_JS = """
<div id="bs-marker"></div>
<script>
(function(){
  if (document.getElementById('bs-particles')) return;
  var c=document.createElement('canvas'); c.id='bs-particles';
  c.style.cssText='position:fixed;inset:0;z-index:-1;pointer-events:none;';
  document.body.appendChild(c);
  var ctx=c.getContext('2d'), W=0, H=0, pts=[];
  function resize(){ W=c.width=window.innerWidth; H=c.height=window.innerHeight; }
  resize(); window.addEventListener('resize', resize);
  var N=Math.max(30, Math.min(110, Math.floor(window.innerWidth*window.innerHeight/16000)));
  for (var i=0;i!==N;i++) pts.push({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.45,vy:(Math.random()-.5)*.45,r:Math.random()*1.6+.6});
  (function loop(){
    if (!document.getElementById('bs-marker')) { c.remove(); return; }   // 已切到别的页面
    ctx.clearRect(0,0,W,H);
    for (var i=0;i!==N;i++){
      var p=pts[i]; p.x+=p.vx; p.y+=p.vy;
      if (0>p.x||p.x>W) p.vx*=-1; if (0>p.y||p.y>H) p.vy*=-1;
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,6.2832); ctx.fillStyle='rgba(34,211,238,.75)'; ctx.fill();
      for (var j=i+1;j!==N;j++){
        var q=pts[j], dx=p.x-q.x, dy=p.y-q.y, d=dx*dx+dy*dy;
        if (130*130>d){ ctx.strokeStyle='rgba(34,211,238,'+(0.22*(1-Math.sqrt(d)/130))+')'; ctx.lineWidth=1;
          ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); }
      }
    }
    requestAnimationFrame(loop);
  })();
  setInterval(function(){
    var el=document.getElementById('bs-clock'); if(!el) return;
    var d=new Date(), z=function(n){return (n>9?'':'0')+n;};
    el.textContent=d.getFullYear()+'-'+z(d.getMonth()+1)+'-'+z(d.getDate())+'  '+z(d.getHours())+':'+z(d.getMinutes())+':'+z(d.getSeconds());
  }, 1000);
})();
</script>
"""

# st.html 里的脚本只要含 "<" 就不会执行(已实测),这里做运行期检查防止以后改坏
_body = PARTICLE_JS[PARTICLE_JS.index("<script>") + 8: PARTICLE_JS.index("</script>")]
assert "<" not in _body, "PARTICLE_JS 里不能出现 < 字符"

df = load()


def style(fig: go.Figure, height: int = 300, legend: bool = True) -> go.Figure:
    fig.update_layout(template="plotly_dark", height=height, margin=dict(l=8, r=8, t=34, b=8),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"),
                      showlegend=legend, legend=dict(orientation="h", y=-0.2),
                      title_font=dict(color="#7DD3FC", size=15),
                      hoverlabel=dict(bgcolor="#0B1424", bordercolor=CY, font_size=13))
    fig.update_xaxes(gridcolor="rgba(34,211,238,.10)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(34,211,238,.10)", zeroline=False)
    return fig


def show(fig: go.Figure, h: int = 300, legend: bool = True) -> None:
    st.plotly_chart(style(fig, h, legend), width="stretch", theme=None)


# ============================== 标题栏 ==============================
st.html(PARTICLE_JS, unsafe_allow_javascript=True)
nav1, nav_mid, nav2 = st.columns([1, 8, 1])
nav2.page_link("dashboard.py", label="返回看板", icon="📊")
nav_mid.markdown('<div class="bs-title"><h1>电商销售数据大屏</h1>'
            '<div class="sub">E-COMMERCE SALES · DATA SCREEN &nbsp;|&nbsp; <span class="bs-clock" id="bs-clock">--</span></div>'
            '<div class="bar"></div></div>', unsafe_allow_html=True)

# ============================== KPI ==============================
mon = df.groupby("month")["pay_amount"].sum()
mom = (mon.iloc[-1] / mon.iloc[-2] - 1) * 100
refund = (df["status"] == "已退款").mean() * 100
st.html('<div class="kpi-row">'
        + kpi_card("全年销售额", df["pay_amount"].sum() / 1e4, 1, "¥", "万", mom, level="bs")
        + kpi_card("订单总数", len(df), 0, sub="含退款、取消订单", level="bs")
        + kpi_card("平均客单价", df["pay_amount"].mean(), 0, "¥", sub=f"买家 {df['user_id'].nunique():,} 人", level="bs")
        + kpi_card("退款率", refund, 1, suf="%", sub=f"取消率 {(df['status'] == '已取消').mean() * 100:.1f}%", level="bs")
        + '</div>' + COUNT_JS, unsafe_allow_javascript=True)
# ============================== 主体三列 ==============================
left, mid, right = st.columns([5, 6, 5])

with left:
    with st.container(key="bs_cat"):
        cat = df.groupby("category")["pay_amount"].sum().sort_values()
        fig = go.Figure(go.Bar(x=cat.values, y=cat.index, orientation="h", text=[f"{v / 1e4:,.0f}万" for v in cat.values],
                               textposition="outside", cliponaxis=False,
                               marker=dict(color=cat.values, colorscale=[[0, "#164E63"], [1, CY]]),
                               hovertemplate="<b>%{y}</b><br>销售额:¥%{x:,.0f}<extra></extra>"))
        fig.update_layout(title="品类销售额")
        fig.update_xaxes(range=[0, cat.max() * 1.22], showticklabels=False)
        show(fig, 235, False)
    with st.container(key="bs_channel"):
        ch = df.groupby("channel")["pay_amount"].sum()
        fig = go.Figure(go.Pie(labels=ch.index, values=ch.values, hole=0.62, marker=dict(colors=["#22D3EE", "#3B82F6", "#A78BFA"]),
                               textinfo="label+percent", hovertemplate="<b>%{label}</b><br>¥%{value:,.0f}<br>%{percent}<extra></extra>"))
        fig.update_layout(title="渠道占比")
        show(fig, 215, False)

with mid:
    with st.container(key="bs_gauge"):
        total = df["pay_amount"].sum()
        pct = total / ANNUAL_TARGET * 100
        fig = go.Figure(go.Indicator(mode="gauge+number", value=pct, number=dict(suffix="%", valueformat=".1f", font=dict(color="#E0F7FF", size=46)),
                                     gauge=dict(axis=dict(range=[0, 120], tickcolor="#64748B"), bar=dict(color=CY), bgcolor="rgba(0,0,0,0)",
                                                steps=[dict(range=[0, 60], color="rgba(220,38,38,.22)"), dict(range=[60, 90], color="rgba(245,158,11,.24)"),
                                                       dict(range=[90, 120], color="rgba(22,163,74,.22)")],
                                                threshold=dict(line=dict(color="#F87171", width=4), value=100))))
        st.markdown('<div style="color:#7DD3FC;font-size:.95rem;text-align:center">全年销售目标完成度'
                    '<span style="color:#94A3B8;font-size:.78rem">(目标 2500 万为模拟假设)</span></div>', unsafe_allow_html=True)
        show(fig, 215, False)
    with st.container(key="bs_prov"):
        pv = df.groupby("province")["pay_amount"].sum().sort_values().tail(10)
        fig = go.Figure(go.Bar(x=pv.values, y=pv.index, orientation="h", marker=dict(color=pv.values, colorscale=[[0, "#1E3A8A"], [1, "#60A5FA"]]),
                               text=[f"{v / 1e4:,.0f}万" for v in pv.values], textposition="outside", cliponaxis=False,
                               hovertemplate="<b>%{y}</b><br>¥%{x:,.0f}<extra></extra>"))
        fig.update_layout(title="省份销售额 Top10")
        fig.update_xaxes(range=[0, pv.max() * 1.2], showticklabels=False)
        show(fig, 265, False)


@st.fragment(run_every=5)
def live_column() -> None:
    s = realtime.get_stream().snapshot()
    now = pd.Timestamp.now()
    per_min = int((s["order_time"] >= now - pd.Timedelta(seconds=60)).sum())
    w5 = s[s["order_time"] >= now - pd.Timedelta(minutes=5)]
    with st.container(key="bs_live_now"):
        rt = alerts.DEFAULTS["rt"]
        lv = alerts.level_of(per_min, rt)
        col = {"": "#E0F7FF", "warn": "#FBBF24", "crit": "#F87171"}[lv]
        st.markdown(f'<div style="color:#7DD3FC;letter-spacing:.1em;font-size:.85rem">近1分钟订单数 · 实时</div>'
                    f'<div class="bignum" style="color:{col}">{per_min} <span style="font-size:1rem">单/分钟</span></div>'
                    f'<div style="color:#94A3B8;font-size:.8rem">近5分钟 {len(w5)} 单 · ¥{w5["pay_amount"].sum() / 1e4:,.2f}万'
                    f'{" · 🔴 订单高峰" if lv == "crit" else " · 🟠 订单偏多" if lv == "warn" else ""}</div>', unsafe_allow_html=True)
        b = w5.set_index("order_time").resample("10s")["order_id"].count()
        fig = go.Figure(go.Scatter(x=b.index, y=b.values, mode="lines", fill="tozeroy", line=dict(color=CY, width=2),
                                   fillcolor="rgba(34,211,238,.18)", hovertemplate="%{x|%H:%M:%S}<br>%{y} 单<extra></extra>"))
        fig.update_layout(xaxis=dict(tickformat="%H:%M"), margin=dict(t=6))
        show(fig, 120, False)
    with st.container(key="bs_live_feed"):
        feed = s.tail(7).iloc[::-1]
        tag = {"已完成": ("ok", "完成"), "已退款": ("rf", "退款"), "已取消": ("cc", "取消")}
        rows = "".join(f'<tr><td>{r.order_time:%H:%M:%S}</td><td>{r.category}</td><td>{r.product}</td>'
                       f'<td style="text-align:right">¥{r.pay_amount:,.0f}</td><td><span class="tag {tag[r.status][0]}">{tag[r.status][1]}</span></td></tr>'
                       for r in feed.itertuples())
        st.markdown('<div style="color:#7DD3FC;letter-spacing:.1em;font-size:.85rem;margin-bottom:.3rem">🛰️ 实时订单滚动</div>', unsafe_allow_html=True)
        st.html(f'<table class="feed">{rows}</table>')
        st.caption(f"Python 实时模拟 · 每 5 秒刷新 · {now:%H:%M:%S}")


with right:
    live_column()

# ============================== 底部:趋势 + 热力图 ==============================
b1, b2 = st.columns([3, 2])
with b1, st.container(key="bs_trend"):
    daily = df.groupby("date")["pay_amount"].sum().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily["ma7"] = daily["pay_amount"].rolling(7, min_periods=1).mean()
    fig = go.Figure()
    fig.add_scatter(x=daily["date"], y=daily["pay_amount"], name="日销售额", mode="lines", line=dict(color="rgba(34,211,238,.55)", width=1),
                    fill="tozeroy", fillcolor="rgba(34,211,238,.10)", hovertemplate="¥%{y:,.0f}<extra>日销售额</extra>")
    fig.add_scatter(x=daily["date"], y=daily["ma7"], name="7日均线", mode="lines", line=dict(color="#60A5FA", width=2.5),
                    hovertemplate="¥%{y:,.0f}<extra>7日均线</extra>")
    fig.update_layout(title="2025 年日销售额趋势", hovermode="x unified")
    show(fig, 250)
with b2, st.container(key="bs_heat"):
    hm = df.assign(wd=df["order_time"].dt.day_of_week).pivot_table(index="wd", columns="hour", values="order_id", aggfunc="count", fill_value=0)
    hm = hm.reindex(index=range(7), columns=range(24), fill_value=0)
    fig = go.Figure(go.Heatmap(z=hm.values, x=[f"{h}时" for h in hm.columns], y=[f"周{w}" for w in WEEKDAYS], xgap=2, ygap=2,
                               colorscale=[[0, "#0B1A30"], [0.5, "#1D4ED8"], [1, CY]], showscale=False,
                               hovertemplate="%{y} %{x}<br>订单数:%{z}<extra></extra>"))
    fig.update_layout(title="下单时段热力图")
    fig.update_yaxes(autorange="reversed")
    show(fig, 250, False)
