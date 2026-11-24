"""电商销售数据看板(基础 + 进阶:筛选联动、动态效果、多维分析)。

运行:  streamlit run src/app.py
"""
import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import alerts
import analysis
import realtime
import report
from common import (ANNUAL_TARGET, COUNT_JS, PALETTE, WEEKDAYS, css, current_theme, dark_css, kpi_card, load)

T = current_theme()
DARK = T["name"] == "dark"
st.markdown(css(T), unsafe_allow_html=True)
if DARK:
    st.markdown(dark_css(T), unsafe_allow_html=True)

df = load()
CATS = sorted(df["category"].unique())


# ============================== 图表样式 ==============================
def style(fig: go.Figure, height: int = 340, legend: bool = True) -> go.Figure:
    fig.update_layout(
        template="plotly_dark" if DARK else "plotly_white",
        height=height, margin=dict(l=10, r=10, t=36, b=10), paper_bgcolor=T["card"], plot_bgcolor=T["card"],
        font=dict(color=T["text"]), showlegend=legend, legend=dict(orientation="h", y=-0.18),
        hoverlabel=dict(bgcolor=T["card"], font_size=13, bordercolor=T["primary"]),
        transition=dict(duration=500, easing="cubic-in-out"),
    )
    fig.update_xaxes(gridcolor=T["grid"], zeroline=False)
    fig.update_yaxes(gridcolor=T["grid"], zeroline=False)
    return fig


def wan(v: float) -> str:
    return f"{v / 1e4:,.1f}万"


# ============================== 侧边栏筛选 ==============================
if "ver" not in st.session_state:
    st.session_state.ver = 0  # 联动选择的"版本号",自增即可清空图表选择

with st.sidebar:
    st.toggle("🌙 暗色模式", key="dark")
    st.markdown("### 🔎 数据筛选")
    d0, d1 = df["order_time"].dt.date.min(), df["order_time"].dt.date.max()
    rng = st.date_input("时间范围", (d0, d1), min_value=d0, max_value=d1)
    sel_cats = st.multiselect("品类", CATS, placeholder="全部品类")
    sel_channels = st.multiselect("渠道", sorted(df["channel"].unique()), placeholder="全部渠道")
    sel_prov = st.multiselect("省份", sorted(df["province"].unique()), placeholder="全部省份")
    sel_status = st.multiselect("订单状态", ["已完成", "已退款", "已取消"], placeholder="全部状态")
    st.caption("留空 = 不限制。筛选后,所有图表同步更新。")

th = alerts.settings_ui()  # 预警阈值面板(侧边栏)

nodate = df
for col, vals in [("category", sel_cats), ("channel", sel_channels), ("province", sel_prov), ("status", sel_status)]:
    if vals:
        nodate = nodate[nodate[col].isin(vals)]
base = df
if isinstance(rng, (tuple, list)) and len(rng) == 2:
    base = base[(base["order_time"].dt.date >= rng[0]) & (base["order_time"].dt.date <= rng[1])]
for col, vals in [("category", sel_cats), ("channel", sel_channels), ("province", sel_prov), ("status", sel_status)]:
    if vals:
        base = base[base[col].isin(vals)]

# ---- 图表联动:点击品类柱状图,其余图表只显示该品类 ----
CAT_KEY = f"cat_chart_{st.session_state.ver}"


def clicked_category() -> str | None:
    s = st.session_state.get(CAT_KEY)
    try:
        pts = s["selection"]["points"]
    except (TypeError, KeyError):
        return None
    if not pts:
        return None
    cd = pts[0].get("customdata")
    return cd[0] if isinstance(cd, list) else cd


link_cat = clicked_category()
view = base[base["category"] == link_cat] if link_cat else base

if base.empty:
    st.warning("当前筛选条件下没有数据,请放宽筛选条件。")
    st.stop()

# ============================== 标题 + 联动提示 ==============================
st.markdown('<div class="dash-title"><h1>📊 电商销售数据看板</h1>'
            f'<p>数据周期:{base["order_time"].min():%Y-%m-%d} ~ {base["order_time"].max():%Y-%m-%d} · '
            f'当前订单 {len(view):,} / {len(df):,} 条 · 统计口径:全部订单(含退款、取消)</p></div>',
            unsafe_allow_html=True)
if link_cat:
    a, b = st.columns([6, 1])
    a.markdown(f'<span class="chip">图表联动:品类 = {link_cat}</span>点击品类图中同一根柱子可取消。',
               unsafe_allow_html=True)
    if b.button("清除联动", width="stretch"):
        st.session_state.ver += 1
        st.rerun()

# ============================== ① 数据概览 ==============================
st.markdown('<div class="section">① 数据概览</div>', unsafe_allow_html=True)
monthly = view.groupby("month")["pay_amount"].sum()
orders_m = view.groupby("month").size()


def mom(s: pd.Series) -> float | None:
    return (s.iloc[-1] / s.iloc[-2] - 1) * 100 if len(s) >= 2 and s.iloc[-2] else None


refund = (view["status"] == "已退款").mean() * 100
cancel = (view["status"] == "已取消").mean() * 100
sales_mom = mom(monthly)

# ---- 扩展2:预警判定 ----
alert_list = alerts.evaluate({"refund": refund, "cancel": cancel, "mom": sales_mom}, th)
alerts.banner(alert_list)
alerts.notify(alert_list)


def lvl(key: str, value: float | None) -> str:
    return alerts.level_of(value, th[key]) if st.session_state.get("alerts_on", True) else ""


def worst(*levels: str) -> str:
    return "crit" if "crit" in levels else "warn" if "warn" in levels else ""


st.html('<div class="kpi-row">'
        + kpi_card("总销售额", view["pay_amount"].sum() / 1e4, 1, "¥", "万", sales_mom, color=T["primary"],
                   level=lvl("mom", sales_mom))
        + kpi_card("订单数", len(view), 0, delta=mom(orders_m), color=T["cyan"])
        + kpi_card("平均客单价", view["pay_amount"].mean(), 0, "¥", sub=f"共 {view['user_id'].nunique():,} 位买家",
                   color=T["purple"])
        + kpi_card("退款率", refund, 1, suf="%", sub=f"取消率 {cancel:.1f}%", color=T["orange"],
                   level=worst(lvl("refund", refund), lvl("cancel", cancel)))
        + '</div>' + COUNT_JS, unsafe_allow_javascript=True)

# ============================== ② 维度统计 ==============================
st.markdown('<div class="section">② 维度统计</div>', unsafe_allow_html=True)
left, right = st.columns([3, 2])
with left, st.container(key="card_cat"):
    cat = base.groupby("category").agg(sales=("pay_amount", "sum"), orders=("order_id", "count")).reset_index()
    cat = cat.sort_values("sales")
    colors = [T["primary"] if (not link_cat or c == link_cat) else T["soft"] for c in cat["category"]]
    fig = go.Figure(go.Bar(
        x=cat["sales"], y=cat["category"], orientation="h", marker_color=colors,
        customdata=cat[["category", "orders"]].to_numpy(), text=[wan(v) for v in cat["sales"]],
        textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>销售额:¥%{x:,.0f}<br>订单数:%{customdata[1]:,}<br>"
                      "<i>点击可联动其他图表</i><extra></extra>"))
    fig.update_layout(title="各品类销售额对比(点击柱子联动)", xaxis_title="销售额(元)", clickmode="event+select")
    fig.update_xaxes(range=[0, cat["sales"].max() * 1.18])
    st.plotly_chart(style(fig, legend=False), key=CAT_KEY, on_select="rerun", selection_mode="points",
                    width="stretch", theme=None)
with right, st.container(key="card_channel"):
    ch = view.groupby("channel").agg(sales=("pay_amount", "sum"), orders=("order_id", "count")).reset_index()
    fig = go.Figure(go.Pie(
        labels=ch["channel"], values=ch["sales"], hole=0.55, customdata=ch["orders"], sort=False,
        marker=dict(colors=PALETTE), textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>销售额:¥%{value:,.0f}<br>占比:%{percent}<br>"
                      "订单数:%{customdata:,}<extra></extra>"))
    fig.update_layout(title="各渠道销售额占比")
    st.plotly_chart(style(fig), width="stretch", theme=None)

# ---- 自动轮播:同一位置循环展示多张图表 ----
CAROUSEL_SEC = 5


@st.fragment(run_every=CAROUSEL_SEC)
def carousel(v: pd.DataFrame) -> None:
    names = ["月度销售额与订单数", "省份销售额 Top10", "渠道 × 品类销售额"]
    with st.container(key="card_carousel"):
        h1, h2 = st.columns([5, 1])
        auto = h2.toggle("自动轮播", value=True, key="auto_carousel")
        if auto:
            idx = int(time.time() // CAROUSEL_SEC) % len(names)
        else:
            pick = h1.segmented_control("选择图表", names, default=names[0], key="car_pick",
                                        label_visibility="collapsed")
            idx = names.index(pick or names[0])
        if auto:
            h1.markdown('<div class="dots">' + "".join(
                f'<span class="dot{" on" if i == idx else ""}">{n}</span>' for i, n in enumerate(names)) + '</div>',
                unsafe_allow_html=True)
        if idx == 0:
            m = v.groupby("month").agg(sales=("pay_amount", "sum"), orders=("order_id", "count")).reset_index()
            fig = go.Figure()
            fig.add_bar(x=m["month"], y=m["sales"], name="销售额(元)", marker_color=T["primary"],
                        hovertemplate="%{x}<br>销售额:¥%{y:,.0f}<extra></extra>")
            fig.add_scatter(x=m["month"], y=m["orders"], name="订单数", yaxis="y2", mode="lines+markers",
                            line=dict(color=T["orange"], width=3),
                            hovertemplate="%{x}<br>订单数:%{y:,}<extra></extra>")
            fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, title="订单数"),
                              yaxis_title="销售额(元)")
        elif idx == 1:
            p = v.groupby("province")["pay_amount"].sum().sort_values().tail(10).reset_index()
            fig = go.Figure(go.Bar(x=p["pay_amount"], y=p["province"], orientation="h", marker_color=T["cyan"],
                                   text=[wan(x) for x in p["pay_amount"]], textposition="outside", cliponaxis=False,
                                   hovertemplate="<b>%{y}</b><br>销售额:¥%{x:,.0f}<extra></extra>"))
            fig.update_xaxes(range=[0, p["pay_amount"].max() * 1.15])
        else:
            c = v.groupby(["channel", "category"])["pay_amount"].sum().reset_index()
            fig = go.Figure()
            for i, cat_name in enumerate(CATS):
                s = c[c["category"] == cat_name]
                fig.add_bar(x=s["channel"], y=s["pay_amount"], name=cat_name, marker_color=PALETTE[i % 6],
                            hovertemplate=f"<b>{cat_name}</b><br>%{{x}}:¥%{{y:,.0f}}<extra></extra>")
            fig.update_layout(barmode="stack", yaxis_title="销售额(元)")
        fig.update_layout(title=names[idx])
        st.plotly_chart(style(fig, 330, legend=idx != 1), key=f"car_chart_{idx}", width="stretch", theme=None)


carousel(view)

# ============================== ③ 趋势分析 ==============================
st.markdown('<div class="section">③ 趋势分析</div>', unsafe_allow_html=True)
daily = view.groupby("date")["pay_amount"].sum().reset_index()
daily["date"] = pd.to_datetime(daily["date"])
daily["ma7"] = daily["pay_amount"].rolling(7, min_periods=1).mean()
with st.container(key="card_trend"):
    fig = go.Figure()
    fig.add_scatter(x=daily["date"], y=daily["pay_amount"], name="日销售额", mode="lines",
                    line=dict(color=T["cyan"], width=1.2), fill="tozeroy", fillcolor="rgba(6,182,212,.12)",
                    hovertemplate="¥%{y:,.0f}<extra>日销售额</extra>")
    fig.add_scatter(x=daily["date"], y=daily["ma7"], name="7日均线", mode="lines",
                    line=dict(color=T["primary"], width=2.5), hovertemplate="¥%{y:,.0f}<extra>7日均线</extra>")
    fig.update_layout(title="日销售额趋势(可拖动缩放,双击还原)", yaxis_title="销售额(元)", hovermode="x unified")
    st.plotly_chart(style(fig, 360), width="stretch", theme=None)

# ============================== ④ 多维度分析 ==============================
st.markdown('<div class="section">④ 多维度分析</div>', unsafe_allow_html=True)
hm_col, radar_col = st.columns([3, 2])
with hm_col, st.container(key="card_heat"):
    hm = view.assign(wd=view["order_time"].dt.day_of_week).pivot_table(
        index="wd", columns="hour", values="order_id", aggfunc="count", fill_value=0)
    hm = hm.reindex(index=range(7), columns=range(24), fill_value=0)
    fig = go.Figure(go.Heatmap(
        z=hm.values, x=[f"{h}时" for h in hm.columns], y=[f"周{w}" for w in WEEKDAYS], xgap=2, ygap=2,
        colorscale=[[0, "#16243B" if DARK else "#EFF6FF"], [0.5, "#2B6CB0" if DARK else "#60A5FA"], [1, T["primary"]]], colorbar=dict(title="订单数"),
        hovertemplate="%{y} %{x}<br>订单数:%{z}<extra></extra>"))
    fig.update_layout(title="下单时段热力图(星期 × 小时)")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style(fig, 340, legend=False), width="stretch", theme=None)
with radar_col, st.container(key="card_radar"):
    g = view.groupby("category").agg(sales=("pay_amount", "sum"), orders=("order_id", "count"),
                                     qty=("quantity", "mean"))
    g["price"] = g["sales"] / g["orders"]
    g["ok"] = view.assign(ok=view["status"] == "已完成").groupby("category")["ok"].mean() * 100
    dims = [("销售额", "sales"), ("订单数", "orders"), ("客单价", "price"), ("件均数量", "qty"), ("订单完成率", "ok")]
    fig = go.Figure()
    for i, (cat_name, r) in enumerate(g.iterrows()):
        vals = [r[k] / g[k].max() * 100 for _, k in dims]
        raw = [f"{r['sales']/1e4:,.1f}万", f"{int(r['orders']):,}", f"¥{r['price']:,.0f}", f"{r['qty']:.2f}",
               f"{r['ok']:.1f}%"]
        fig.add_trace(go.Scatterpolar(
            r=vals + vals[:1], theta=[n for n, _ in dims] + [dims[0][0]], name=cat_name, fill="toself",
            opacity=0.28 if len(g) > 1 else 0.5, line=dict(color=PALETTE[CATS.index(cat_name) % 6]),
            customdata=raw + raw[:1], hovertemplate=f"<b>{cat_name}</b><br>%{{theta}}:%{{customdata}}<extra></extra>"))
    fig.update_layout(title="品类综合能力雷达(各维度按最大值归一化)",
                      polar=dict(bgcolor=T["card"], radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor=T["grid"])))
    st.plotly_chart(style(fig, 340), width="stretch", theme=None)

rank_col, gauge_col = st.columns([3, 2])
with rank_col, st.container(key="card_rank"):
    top = view.groupby(["product", "category"]).agg(sales=("pay_amount", "sum"), orders=("order_id", "count")) \
        .reset_index().sort_values("sales", ascending=False).head(10)
    mx = top["sales"].max()
    rows = "".join(
        f'<tr><td class="no"><span class="badge g{i}">{i}</span></td><td><b>{r.product}</b>'
        f'<div style="font-size:.75rem;color:{T["muted"]}">{r.category} · {r.orders:,} 单</div></td>'
        f'<td style="width:38%"><div class="bar-bg"><div class="bar" style="width:{r.sales / mx * 100:.1f}%"></div>'
        f'</div></td><td style="text-align:right;font-weight:600">¥{r.sales / 1e4:,.1f}万</td></tr>'
        for i, r in enumerate(top.itertuples(), 1))
    st.markdown("**🏆 商品销售额排行榜 Top10**")
    st.html(f'<table class="rank">{rows}</table>')
with gauge_col:
    with st.container(key="card_gauge"):
        total_year = df["pay_amount"].sum()
        pct = total_year / ANNUAL_TARGET * 100
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=pct, number=dict(suffix="%", valueformat=".1f"),
            title=dict(text="全年销售目标完成度"),
            gauge=dict(axis=dict(range=[0, 120]), bar=dict(color=T["primary"]),
                       bgcolor="rgba(0,0,0,0)",
                       steps=[dict(range=[0, 60], color="rgba(220,38,38,.20)"), dict(range=[60, 90], color="rgba(245,158,11,.22)"),
                              dict(range=[90, 120], color="rgba(22,163,74,.20)")],
                       threshold=dict(line=dict(color=T["bad"], width=4), value=100))))
        st.plotly_chart(style(fig, 250, legend=False), width="stretch", theme=None)
        st.caption(f"目标 {ANNUAL_TARGET / 1e4:,.0f} 万元为**模拟假设**(数据中无真实目标);"
                   f"全年实际 {total_year / 1e4:,.1f} 万元,不受筛选器影响。")
    with st.container(key="card_ext"):
        best_day = daily.loc[daily["pay_amount"].idxmax()]
        worst_day = daily.loc[daily["pay_amount"].idxmin()]
        prov = view.groupby("province")["pay_amount"].sum()
        top_cat = view.groupby("category")["pay_amount"].sum()
        st.markdown(
            '<div class="ext-grid">'
            f'<div class="ext"><div class="t">📈 单日最高</div><div class="v">¥{best_day.pay_amount / 1e4:,.1f}万</div>'
            f'<div class="s">{best_day.date:%Y-%m-%d}</div></div>'
            f'<div class="ext"><div class="t">📉 单日最低</div><div class="v">¥{worst_day.pay_amount / 1e4:,.1f}万</div>'
            f'<div class="s">{worst_day.date:%Y-%m-%d}</div></div>'
            f'<div class="ext"><div class="t">🏅 销售额最高省份</div><div class="v">{prov.idxmax()}</div>'
            f'<div class="s">¥{prov.max() / 1e4:,.1f}万</div></div>'
            f'<div class="ext"><div class="t">⭐ 销售额最高品类</div><div class="v">{top_cat.idxmax()}</div>'
            f'<div class="s">占比 {top_cat.max() / top_cat.sum() * 100:.1f}%</div></div></div>',
            unsafe_allow_html=True)

# ============================== ⑤ 实时订单监控(扩展1) ==============================
st.markdown('<div class="section">⑤ 实时订单监控</div>', unsafe_allow_html=True)
INTERVALS = {"2秒": 2, "5秒": 5, "10秒": 10, "30秒": 30, "1分钟": 60}
rc1, rc2 = st.columns([4, 1])
iv = rc1.segmented_control("自动刷新间隔", list(INTERVALS), default="5秒", key="rt_interval")
live_on = rc2.toggle("实时刷新", value=True, key="rt_on")
refresh_sec = INTERVALS[iv or "5秒"]


@st.fragment(run_every=refresh_sec if live_on else None)
def live_panel(th_: dict) -> None:
    s = realtime.get_stream().snapshot()
    now = pd.Timestamp.now()
    w5 = s[s["order_time"] >= now - pd.Timedelta(minutes=5)]
    per_min = int((s["order_time"] >= now - pd.Timedelta(seconds=60)).sum())
    last200 = s.tail(200)
    rt_refund = (last200["status"] == "已退款").mean() * 100
    on = st.session_state.get("alerts_on", True)
    lv_rate = alerts.level_of(per_min, th_["rt"]) if on else ""
    lv_ref = alerts.level_of(rt_refund, th_["refund"]) if on else ""
    # 等级升高时弹 toast(避免每次刷新都重复弹)
    cur = (lv_rate, lv_ref)
    if cur != st.session_state.get("rt_last") and any(cur):
        if lv_rate:
            st.toast(f"实时预警:近1分钟订单数 {per_min} 单(警告线 {th_['rt']['warn']:g})", icon="🔴" if lv_rate == "crit" else "🟠")
        if lv_ref:
            st.toast(f"实时预警:近200单退款率 {rt_refund:.1f}%", icon="🔴" if lv_ref == "crit" else "🟠")
    st.session_state.rt_last = cur

    st.html('<div class="kpi-row">'
            + kpi_card("近5分钟订单数", len(w5), 0, color=T["primary"])
            + kpi_card("近5分钟销售额", w5["pay_amount"].sum() / 1e4, 2, "¥", "万", color=T["cyan"])
            + kpi_card("近1分钟订单数", per_min, 0, suf="单", sub="下单速率;高峰期会明显升高", color=T["purple"], level=lv_rate)
            + kpi_card("近200单退款率", rt_refund, 1, suf="%", sub=f"累计模拟订单 {realtime.get_stream().seq:,} 单",
                       color=T["orange"], level=lv_ref)
            + '</div>')
    lc, rc = st.columns([3, 2])
    with lc, st.container(key="card_live_chart"):
        b = w5.set_index("order_time").resample("10s").agg(orders=("order_id", "count"), sales=("pay_amount", "sum"))
        fig = go.Figure()
        fig.add_bar(x=b.index, y=b["orders"], name="订单数/10秒", marker_color=T["primary"],
                    hovertemplate="%{x|%H:%M:%S}<br>订单数:%{y}<extra></extra>")
        fig.add_scatter(x=b.index, y=b["sales"], name="销售额(元)", yaxis="y2", mode="lines",
                        line=dict(color=T["orange"], width=2), hovertemplate="¥%{y:,.0f}<extra></extra>")
        fig.update_layout(title="近5分钟订单流(每10秒)", yaxis_title="订单数",
                          yaxis2=dict(overlaying="y", side="right", showgrid=False, title="销售额"), bargap=0.15,
                          xaxis=dict(tickformat="%H:%M"))
        st.plotly_chart(style(fig, 300), width="stretch", theme=None)
    with rc, st.container(key="card_live_feed"):
        feed = s.tail(8).iloc[::-1][["order_time", "category", "product", "pay_amount", "status"]]
        feed = feed.assign(order_time=feed["order_time"].dt.strftime("%H:%M:%S")).rename(columns={
            "order_time": "时间", "category": "品类", "product": "商品", "pay_amount": "金额", "status": "状态"})
        st.markdown("**🛰️ 最新订单**")
        st.dataframe(feed, width="stretch", hide_index=True, height=300,
                     column_config={"金额": st.column_config.NumberColumn(format="¥%.2f")})
    st.caption(f"数据由 Python 后台线程实时模拟生成(非 2025 年历史数据),每 {refresh_sec} 秒自动刷新"
               f"{'' if live_on else '(已暂停)'} · 最后刷新 {now:%H:%M:%S}")


live_panel(th)

# ============================== ⑥ 历史对比(扩展5) ==============================
st.markdown('<div class="section">⑥ 历史数据对比</div>', unsafe_allow_html=True)
if isinstance(rng, (tuple, list)) and len(rng) == 2:
    n_days = (rng[1] - rng[0]).days + 1
    p_end, p_start = rng[0] - pd.Timedelta(days=1), rng[0] - pd.Timedelta(days=n_days)
    half_n = ((d1 - d0).days + 1) // 2
    sug_s = d1 - pd.Timedelta(days=half_n - 1)
    if p_start < d0:
        st.info(f"对比对象是紧邻的上一个等长周期({p_start} ~ {p_end}),它超出了数据范围(数据从 {d0} 开始),"
                f"所以暂时无法对比。所选时间范围的长度不能超过数据总长度的一半,"
                f"例如可选 {sug_s} ~ {d1}({half_n} 天)。")
    else:
        dts = nodate["order_time"].dt.date
        cur = nodate[(dts >= rng[0]) & (dts <= rng[1])]
        prv = nodate[(dts >= p_start) & (dts <= p_end)]
        if link_cat:
            cur, prv = cur[cur["category"] == link_cat], prv[prv["category"] == link_cat]

        def metrics(x: pd.DataFrame) -> dict:
            return {"销售额(万元)": x["pay_amount"].sum() / 1e4, "订单数": float(len(x)),
                    "平均客单价(元)": x["pay_amount"].mean() if len(x) else 0.0,
                    "退款率(%)": (x["status"] == "已退款").mean() * 100 if len(x) else 0.0}
        mc, mp = metrics(cur), metrics(prv)
        st.caption(f"本期 {rng[0]} ~ {rng[1]}({n_days} 天) vs 上期 {p_start} ~ {p_end}(紧邻的前 {n_days} 天)")
        hc1, hc2 = st.columns([2, 3])
        with hc1, st.container(key="card_hist_tbl"):
            rows = []
            for k in mc:
                ch_ = (mc[k] / mp[k] - 1) * 100 if mp[k] else None
                rows.append({"指标": k, "本期": round(mc[k], 2), "上期": round(mp[k], 2),
                             "变化": f"{ch_:+.1f}%" if ch_ is not None else "—"})
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        with hc2, st.container(key="card_hist_chart"):
            cd = cur.groupby(cur["order_time"].dt.date)["pay_amount"].sum().reset_index(drop=True)
            pdv = prv.groupby(prv["order_time"].dt.date)["pay_amount"].sum().reset_index(drop=True)
            fig = go.Figure()
            fig.add_scatter(x=list(range(1, len(cd) + 1)), y=cd, name="本期", mode="lines", line=dict(color=T["primary"], width=2.5),
                            hovertemplate="第%{x}天<br>¥%{y:,.0f}<extra>本期</extra>")
            fig.add_scatter(x=list(range(1, len(pdv) + 1)), y=pdv, name="上期", mode="lines",
                            line=dict(color=T["muted"], width=2, dash="dash"), hovertemplate="第%{x}天<br>¥%{y:,.0f}<extra>上期</extra>")
            fig.update_layout(title="日销售额:本期 vs 上期(按周期内第几天对齐)", xaxis_title="周期内第几天", yaxis_title="销售额(元)",
                              hovermode="x unified")
            st.plotly_chart(style(fig, 280), width="stretch", theme=None)

# ============================== ⑦ 数据钻取(扩展5) ==============================
st.markdown('<div class="section">⑦ 数据钻取:品类 → 商品 → 省份</div>', unsafe_allow_html=True)
with st.container(key="card_drill"):
    dc1, dc2 = st.columns(2)
    d_cat = dc1.selectbox("第 1 层:选择品类", ["(全部)"] + sorted(view["category"].unique()), key="drill_cat")
    lv1 = view if d_cat == "(全部)" else view[view["category"] == d_cat]
    prods = lv1.groupby("product")["pay_amount"].sum().sort_values(ascending=False)
    d_prod = dc2.selectbox("第 2 层:选择商品(可选)", ["(全部)"] + list(prods.index), key="drill_prod")
    lv2 = lv1 if d_prod == "(全部)" else lv1[lv1["product"] == d_prod]
    dl, dr = st.columns(2)
    with dl:
        by = prods.sort_values().tail(12)
        fig = go.Figure(go.Bar(x=by.values, y=by.index, orientation="h",
                               marker_color=[T["primary"] if (d_prod == "(全部)" or i == d_prod) else T["soft"] for i in by.index],
                               text=[wan(x) for x in by.values], textposition="outside", cliponaxis=False,
                               hovertemplate="<b>%{y}</b><br>¥%{x:,.0f}<extra></extra>"))
        fig.update_layout(title=f"{'全部品类' if d_cat == '(全部)' else d_cat} · 商品销售额")
        fig.update_xaxes(range=[0, by.max() * 1.2])
        st.plotly_chart(style(fig, 330, False), width="stretch", theme=None)
    with dr:
        pv_ = lv2.groupby("province")["pay_amount"].sum().sort_values().tail(12)
        fig = go.Figure(go.Bar(x=pv_.values, y=pv_.index, orientation="h", marker_color=T["cyan"], text=[wan(x) for x in pv_.values],
                               textposition="outside", cliponaxis=False, hovertemplate="<b>%{y}</b><br>¥%{x:,.0f}<extra></extra>"))
        fig.update_layout(title=f"{'' if d_prod == '(全部)' else d_prod + ' · '}省份分布(Top12)")
        fig.update_xaxes(range=[0, pv_.max() * 1.2])
        st.plotly_chart(style(fig, 330, False), width="stretch", theme=None)
    st.caption(f"当前钻取范围:{len(lv2):,} 单 · 销售额 {wan(lv2['pay_amount'].sum())} · 平均客单价 ¥{lv2['pay_amount'].mean():,.0f}")

# ============================== ⑧ 数据分析与报告导出(扩展4) ==============================
st.markdown('<div class="section">⑧ 数据分析与报告导出</div>', unsafe_allow_html=True)
desc = (f"{base['order_time'].min():%Y-%m-%d} ~ {base['order_time'].max():%Y-%m-%d}"
        f"{' · 品类=' + link_cat if link_cat else ''}{' · 品类:' + '/'.join(sel_cats) if sel_cats else ''}"
        f"{' · 渠道:' + '/'.join(sel_channels) if sel_channels else ''}{' · 省份:' + '/'.join(sel_prov) if sel_prov else ''}"
        f"{' · 状态:' + '/'.join(sel_status) if sel_status else ''}")
fnd = analysis.findings(view)
with st.container(key="card_analysis"):
    st.caption(f"统计范围:{desc}。以下结论由程序根据当前筛选范围自动计算,换筛选条件会随之变化。")
    a1, a2, a3 = st.columns(3)
    for col_, (grp, icon, title_) in zip((a1, a2, a3), [("规律", "📈", "数据规律"), ("优势", "💪", "业务优势"), ("问题", "⚠️", "存在问题")]):
        with col_:
            st.markdown(f"**{icon} {title_}**")
            for t_ in fnd[grp]:
                st.markdown(f"- {t_}")
with st.container(key="card_export"):
    st.markdown("**📥 数据与报告导出**(都基于当前筛选范围)")
    e1, e2, e3, e4 = st.columns(4)
    stamp = f"{datetime.now():%Y%m%d_%H%M}"
    e1.download_button("Excel 数据汇总", data=lambda: report.build_xlsx(view, fnd, desc), file_name=f"销售数据汇总_{stamp}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch",
                       help="含订单明细、4 张汇总表和分析结论,点击后才生成(约几秒)")
    e2.download_button("CSV 明细", data=lambda: report.build_csv(view), file_name=f"订单明细_{stamp}.csv", mime="text/csv", width="stretch")

    @st.fragment
    def png_export() -> None:
        figs = report.make_figs(view)
        pick = st.selectbox("选择图表", list(figs), format_func=lambda k: k.split("_", 1)[1], key="png_pick", label_visibility="collapsed")
        st.download_button("下载所选图表 PNG", data=lambda: report.to_png(figs[pick]), file_name=f"{pick}.png", mime="image/png", width="stretch")
    with e3:
        png_export()

    @st.fragment
    def pkg_export() -> None:
        if st.button("📦 一键生成完整报告包", type="primary", width="stretch", help="Word 报告 + Excel + 5 张图表 PNG,打成 ZIP"):
            with st.spinner("正在渲染图表并生成报告,约需 10 秒…"):
                data_, cost = report.build_package(view, fnd, desc)
            st.session_state.pkg = (data_, stamp, cost)
        if "pkg" in st.session_state:
            data_, st_, cost = st.session_state.pkg
            st.download_button(f"⬇️ 下载报告包({len(data_) / 1e6:.1f} MB)", data=data_, file_name=f"电商销售数据报告_{st_}.zip",
                               mime="application/zip", width="stretch")
    with e4:
        pkg_export()
    st.caption("报告包内:Word 报告(含核心指标、分析结论、5 张图表)、Excel 汇总、图表文件夹。导出的图表固定使用亮色,方便放进文档。")

# ============================== ⑨ 订单明细 ==============================
st.markdown('<div class="section">⑨ 订单明细</div>', unsafe_allow_html=True)
cols = {"order_id": "订单号", "order_time": "下单时间", "category": "品类", "product": "商品", "province": "省份",
        "channel": "渠道", "quantity": "数量", "unit_price": "单价", "discount": "折扣", "pay_amount": "实付金额",
        "status": "状态"}
sc1, sc2, sc3 = st.columns([2, 2, 3])
sort_by = sc1.selectbox("排序依据", ["下单时间", "实付金额", "单价", "数量", "折扣"], key="sort_by")
asc = sc2.radio("顺序", ["降序", "升序"], horizontal=True, key="sort_dir") == "升序"
shown = sc3.select_slider("显示条数", [50, 100, 200, 500, 1000], value=200, key="sort_n")
detail = view.rename(columns=cols).sort_values(sort_by, ascending=asc).head(shown)[list(cols.values())]
st.dataframe(detail, width="stretch", height=340, hide_index=True,
             column_config={"单价": st.column_config.NumberColumn(format="¥%.2f"),
                            "实付金额": st.column_config.NumberColumn(format="¥%.2f")})
st.caption(f"按「{sort_by}」{'升序' if asc else '降序'}显示前 {min(shown, len(view)):,} 条(符合条件共 {len(view):,} 条)。")
