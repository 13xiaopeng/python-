"""扩展4:数据导出与一键报告 —— Excel / CSV / 图表 PNG / Word 报告 / 打包 ZIP。

图表导出始终使用【亮色主题】,方便放进文档;依赖 kaleido(调用本机 Chrome 渲染)。
"""
import io
import zipfile
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from common import LIGHT, PALETTE, WEEKDAYS

T = LIGHT
FONT = "Microsoft YaHei"
CN = {"order_id": "订单号", "order_time": "下单时间", "category": "品类", "product": "商品", "province": "省份",
      "channel": "渠道", "quantity": "数量", "unit_price": "单价", "discount": "折扣", "pay_amount": "实付金额",
      "status": "状态", "user_id": "用户ID", "date": "日期", "month": "月份", "weekday": "星期", "hour": "小时"}


# ============================== 图表(亮色,用于导出) ==============================
def _base(fig: go.Figure, title: str, h: int = 420) -> go.Figure:
    fig.update_layout(title=dict(text=title, font=dict(size=20)), template="plotly_white", height=h, width=980,
                      margin=dict(l=60, r=40, t=70, b=60), font=dict(family=FONT, size=14, color=T["text"]),
                      legend=dict(orientation="h", y=-0.18))
    return fig


def make_figs(v: pd.DataFrame) -> dict[str, go.Figure]:
    """生成报告用的 5 张图。键名即导出时的图片文件名。"""
    figs: dict[str, go.Figure] = {}
    c = v.groupby("category")["pay_amount"].sum().sort_values()
    f = go.Figure(go.Bar(x=c.values, y=c.index, orientation="h", marker_color=T["primary"],
                         text=[f"{x / 1e4:,.1f}万" for x in c.values], textposition="outside", cliponaxis=False))
    f.update_xaxes(range=[0, c.max() * 1.18], title="销售额(元)")
    figs["1_品类销售额对比"] = _base(f, "各品类销售额对比")

    ch = v.groupby("channel")["pay_amount"].sum()
    f = go.Figure(go.Pie(labels=ch.index, values=ch.values, hole=0.55, marker=dict(colors=PALETTE), textinfo="label+percent"))
    figs["2_渠道占比"] = _base(f, "各渠道销售额占比", 400)

    m = v.groupby("month").agg(s=("pay_amount", "sum"), n=("order_id", "count")).reset_index()
    f = go.Figure()
    f.add_bar(x=m["month"], y=m["s"], name="销售额(元)", marker_color=T["primary"])
    f.add_scatter(x=m["month"], y=m["n"], name="订单数", yaxis="y2", mode="lines+markers", line=dict(color=T["orange"], width=3))
    f.update_layout(yaxis=dict(title="销售额(元)"), yaxis2=dict(overlaying="y", side="right", showgrid=False, title="订单数"))
    figs["3_月度销售额与订单数"] = _base(f, "月度销售额与订单数")

    d = v.groupby("date")["pay_amount"].sum().reset_index()
    d["date"] = pd.to_datetime(d["date"])
    d["ma7"] = d["pay_amount"].rolling(7, min_periods=1).mean()
    f = go.Figure()
    f.add_scatter(x=d["date"], y=d["pay_amount"], name="日销售额", mode="lines", line=dict(color=T["cyan"], width=1.2),
                  fill="tozeroy", fillcolor="rgba(6,182,212,.12)")
    f.add_scatter(x=d["date"], y=d["ma7"], name="7日均线", mode="lines", line=dict(color=T["primary"], width=2.5))
    f.update_yaxes(title="销售额(元)")
    figs["4_日销售额趋势"] = _base(f, "日销售额趋势")

    hm = v.assign(wd=v["order_time"].dt.day_of_week).pivot_table(index="wd", columns="hour", values="order_id", aggfunc="count", fill_value=0)
    hm = hm.reindex(index=range(7), columns=range(24), fill_value=0)
    f = go.Figure(go.Heatmap(z=hm.values, x=[f"{h}时" for h in hm.columns], y=[f"周{w}" for w in WEEKDAYS], xgap=2, ygap=2,
                             colorscale=[[0, "#EFF6FF"], [0.5, "#60A5FA"], [1, T["primary"]]], colorbar=dict(title="订单数")))
    f.update_yaxes(autorange="reversed")
    figs["5_下单时段热力图"] = _base(f, "下单时段热力图(星期 × 小时)", 380)
    return figs


def to_png(fig: go.Figure) -> bytes:
    return fig.to_image(format="png", scale=2)


def to_pngs(figs: dict[str, go.Figure]) -> dict[str, bytes]:
    """批量渲染:共用一次浏览器启动,5 张图约 7 秒(逐张调用 to_image 要 25 秒)。"""
    import os
    import tempfile

    import plotly.io as pio
    with tempfile.TemporaryDirectory() as d:
        paths = [os.path.join(d, f"{i}.png") for i in range(len(figs))]
        pio.write_images(list(figs.values()), paths, format="png", scale=2)
        return {k: open(pth, "rb").read() for k, pth in zip(figs, paths)}


# ============================== 汇总数据 ==============================
def kpis(v: pd.DataFrame) -> list[tuple[str, str]]:
    return [("总销售额", f"¥{v['pay_amount'].sum() / 1e4:,.1f} 万"), ("订单数", f"{len(v):,}"),
            ("平均客单价", f"¥{v['pay_amount'].mean():,.0f}"), ("买家数", f"{v['user_id'].nunique():,}"),
            ("退款率", f"{(v['status'] == '已退款').mean() * 100:.1f}%"), ("取消率", f"{(v['status'] == '已取消').mean() * 100:.1f}%")]


def _summary(v: pd.DataFrame, key: str) -> pd.DataFrame:
    g = v.groupby(key).agg(销售额=("pay_amount", "sum"), 订单数=("order_id", "count"), 平均客单价=("pay_amount", "mean"),
                           退款率=("status", lambda s: (s == "已退款").mean()))
    g["销售额占比"] = g["销售额"] / g["销售额"].sum()
    return g.sort_values("销售额", ascending=False).round(4).reset_index().rename(columns={key: CN.get(key, key)})


# ============================== Excel / CSV ==============================
def build_xlsx(v: pd.DataFrame, findings: dict[str, list[str]], desc: str) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        wb = xw.book
        head = wb.add_format({"bold": True, "bg_color": "#2563EB", "font_color": "white", "border": 1, "align": "center"})
        money, pct = wb.add_format({"num_format": "#,##0.00"}), wb.add_format({"num_format": "0.0%"})

        def put(df: pd.DataFrame, name: str, money_cols=(), pct_cols=()) -> None:
            df.to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            for i, col in enumerate(df.columns):
                ws.write(0, i, col, head)
                w = max(len(str(col)) * 2, int(df[col].astype(str).str.len().quantile(0.9)) + 2) if len(df) else 12
                fmt = money if col in money_cols else pct if col in pct_cols else None
                ws.set_column(i, i, min(w, 28), fmt)
            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, len(df), len(df.columns) - 1)

        detail = v.sort_values("order_time").rename(columns=CN)
        put(detail, "订单明细", money_cols=("单价", "实付金额"))
        for key, name in [("category", "品类汇总"), ("channel", "渠道汇总"), ("province", "省份汇总"), ("month", "月度汇总")]:
            put(_summary(v, key), name, money_cols=("销售额", "平均客单价"), pct_cols=("退款率", "销售额占比"))
        rows = [("统计范围", desc)] + [(k, t) for k, xs in findings.items() for t in xs]
        put(pd.DataFrame(rows, columns=["类别", "内容"]), "分析结论")
        xw.sheets["分析结论"].set_column(1, 1, 110)
    return buf.getvalue()


def build_csv(v: pd.DataFrame) -> bytes:
    return v.sort_values("order_time").rename(columns=CN).to_csv(index=False).encode("utf-8-sig")


# ============================== Word 报告 ==============================
def _font(run, size=None, bold=None, color=None) -> None:
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def _heading(doc: Document, text: str, size: int = 15) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    _font(p.add_run(text), size, True, "2563EB")


def build_docx(v: pd.DataFrame, findings: dict[str, list[str]], desc: str, images: dict[str, bytes]) -> bytes:
    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(0.9)
    st_ = doc.styles["Normal"]
    st_.font.name = FONT
    st_.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _font(p.add_run("电商销售数据分析报告"), 24, True, "1E293B")
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _font(p.add_run(f"生成时间:{datetime.now():%Y-%m-%d %H:%M}    统计范围:{desc}"), 10, False, "64748B")

    _heading(doc, "一、核心指标")
    items = kpis(v)
    t = doc.add_table(rows=2, cols=len(items)); t.style = "Light Grid Accent 1"
    for i, (k, val) in enumerate(items):
        for r, (txt, bold, size) in enumerate([(k, False, 10), (val, True, 13)]):
            cell = t.cell(r, i); cell.text = ""
            para = cell.paragraphs[0]; para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _font(para.add_run(txt), size, bold)

    _heading(doc, "二、数据分析结论")
    for group, xs in findings.items():
        p = doc.add_paragraph(); _font(p.add_run(f"▌{group}"), 12, True, "1E293B")
        for x in xs:
            q = doc.add_paragraph(style="List Bullet"); _font(q.add_run(x), 10.5)

    _heading(doc, "三、可视化图表")
    for name in sorted(images):
        doc.add_picture(io.BytesIO(images[name]), width=Inches(6.4))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _font(cap.add_run(f"图:{name.split('_', 1)[1]}"), 9, False, "64748B")

    _heading(doc, "四、说明")
    for note in ["本报告基于模拟生成的 2025 年电商订单数据,统计口径为全部订单(含已退款、已取消)。",
                 "分析结论由程序根据当前筛选范围自动计算生成;样本过少时不给出结论。",
                 "看板中的预警阈值、全年销售目标均为演示用的模拟假设,不代表真实业务标准。"]:
        q = doc.add_paragraph(style="List Bullet"); _font(q.add_run(note), 10)
    buf = io.BytesIO(); doc.save(buf)
    return buf.getvalue()


# ============================== 一键打包 ==============================
def build_package(v: pd.DataFrame, findings: dict[str, list[str]], desc: str) -> tuple[bytes, dict[str, float]]:
    """渲染全部图表 → 生成 Word、Excel → 打成 ZIP。返回 (zip 字节, 各步耗时)。"""
    import time
    cost = {}
    t0 = time.time(); figs = make_figs(v); images = to_pngs(figs); cost["图表渲染"] = time.time() - t0
    t0 = time.time(); docx = build_docx(v, findings, desc, images); cost["Word"] = time.time() - t0
    t0 = time.time(); xlsx = build_xlsx(v, findings, desc); cost["Excel"] = time.time() - t0
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("电商销售数据分析报告.docx", docx)
        z.writestr("销售数据汇总.xlsx", xlsx)
        for k, b in images.items():
            z.writestr(f"图表/{k}.png", b)
    return buf.getvalue(), cost
