"""生成《实验2 数据看板的设计与实现》实验报告(.docx),直接套用「标准实验报告模板」的版式。

输入: data/tpl.docx(由模板 .doc 转换而来)、screenshots/final_*.png、data/*.csv
输出: E:\\pytest\\实验二作业\\实验2_数据看板_实验报告.docx(由调用方指定)
模板里的抬头、班级/学号/姓名、日期栏原样保留,只在四个小标题下填入内容。
"""
import sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "screenshots"
OUT = Path(sys.argv[1])

doc = Document(ROOT / "data" / "tpl.docx")
sec = doc.sections[0]
sec.bottom_margin = Cm(2.0)   # 模板转换后下边距为 0,会让文字贴住页底,改为 2cm(与上边距一致)
USABLE_CM = (sec.page_width - sec.left_margin - sec.right_margin) / 360000

_figno = [0]
_tabno = [0]
_new: list = []   # 本次新建的元素(按顺序),最后统一移动到对应小标题后面


# ====================== 基础写作函数 ======================
def _fmt(run, size=12, bold=False, color=None, font="宋体"):
    run.font.size = Pt(size)
    run.bold = bold
    run.font.name = "Times New Roman" if font == "宋体" else font   # 与模板一致:西文 TNR,中文宋体
    rpr = run._element.get_or_add_rPr()
    rpr.rFonts.set(qn("w:eastAsia"), font)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def para(text="", size=12, bold=False, indent=True, align=None, color=None, before=0, after=0, font="宋体"):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Pt(size * 2)
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.3
    if text:
        _fmt(p.add_run(text), size, bold, color, font)
    _new.append(p._p)
    return p


def h2(text):   # (一)基础任务
    return para(text, 13, True, indent=False, before=8, after=2, color="1F3A8A")


def h3(text):   # 任务1 ...
    return para(text, 12, True, indent=False, before=6, after=2)


def item(text, level=0):
    p = para("", indent=False)
    p.paragraph_format.left_indent = Cm(0.74 + 0.6 * level)
    p.paragraph_format.first_line_indent = Cm(-0.4)
    _fmt(p.add_run("• " + text), 11.5)
    return p


def picture(name, width_cm, caption):
    f = SHOTS / name
    assert f.exists(), f"缺少截图 {f}"
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(f), width=Cm(min(width_cm, USABLE_CM)))
    _new.append(p._p)
    _figno[0] += 1
    para(f"图{_figno[0]}  {caption}", 10, False, indent=False, align="center", color="475569", after=6)


def _shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def _borders(tbl, color="94A3B8"):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color)
        b.append(e)
    tblPr.append(b)


def table(rows, widths_cm, caption=None, header=True, size=10, align_cols=None):
    """rows: 二维列表,首行为表头。"""
    if caption:
        _tabno[0] += 1
        cp = para(f"表{_tabno[0]}  {caption}", 10, True, indent=False, align="center", before=4, after=2, color="334155")
        cp.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _borders(t)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.width = Cm(widths_cm[j])
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.keep_with_next = i < len(rows) - 1   # 整表同页
            if (align_cols and j in align_cols) or (header and i == 0):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _fmt(p.add_run(str(val)), size, bold=(header and i == 0))
            if header and i == 0:
                _shade(c, "DBEAFE")
    _new.append(t._tbl)
    para("", indent=False, after=2)
    return t


def sketch():
    """用合并单元格的 Word 表格画版面草图。"""
    t = doc.add_table(rows=6, cols=4)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _borders(t, "2563EB")
    w = USABLE_CM * 0.92 / 4
    spec = [
        (0, 0, 3, "标题栏:电商销售数据看板    ·    侧边栏筛选器(时间 / 品类 / 渠道 / 省份 / 状态)", "2563EB", "FFFFFF"),
        (1, 0, 0, "① 数据概览\n总销售额", "DBEAFE", "1E293B"), (1, 1, 1, "\n订单数", "DBEAFE", "1E293B"),
        (1, 2, 2, "\n平均客单价", "DBEAFE", "1E293B"), (1, 3, 3, "\n退款率", "FEF3C7", "1E293B"),
        (2, 0, 1, "② 维度统计 — 各品类销售额对比\n(横向柱状图)", "E0F2FE", "1E293B"),
        (2, 2, 3, "② 维度统计 — 各渠道占比\n(环形图)", "E0F2FE", "1E293B"),
        (3, 0, 3, "③ 趋势分析 — 全年日销售额折线图 + 7 日均线", "ECFEFF", "1E293B"),
        (4, 0, 3, "④ 多维分析(进阶):热力图 / 雷达图 / 排行榜 / 目标仪表盘      ⑤ 实时监控(扩展)", "EDE9FE", "1E293B"),
        (5, 0, 3, "⑥ 明细数据 — 订单明细表格(可排序、可导出)", "F1F5F9", "1E293B"),
    ]
    for r, c0, c1, text, fill, fg in spec:
        cell = t.cell(r, c0)
        if c1 > c0:
            cell = cell.merge(t.cell(r, c1))
        cell.width = Cm(w * (c1 - c0 + 1))
        cell.text = ""
        lines = text.split("\n")
        for k, line in enumerate(lines):
            p = cell.paragraphs[0] if k == 0 else cell.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(2); p.paragraph_format.space_before = Pt(2)
            _fmt(p.add_run(line), 10.5, bold=(k == 0 and c1 == 3 and r in (0, 3, 4, 5)), color=fg)
        _shade(cell, fill)
    _new.append(t._tbl)
    para("", indent=False, after=2)


# ====================== 数据(用于报告里的数字,直接从数据文件读取) ======================
df = pd.read_csv(ROOT / "data" / "orders_clean.csv", parse_dates=["order_time"])
total = df["pay_amount"].sum()
refund = (df["status"] == "已退款").mean() * 100
cancel = (df["status"] == "已取消").mean() * 100
mon = df.groupby("month")["pay_amount"].sum()
mom = (mon.iloc[-1] / mon.iloc[-2] - 1) * 100
cat_share = df.groupby("category")["pay_amount"].sum() / total * 100

# ====================== 正文 ======================
sections: dict[str, list] = {}


def start(key):
    global _new
    _new = []
    sections[key] = _new


# ---------- 一、实验目的 ----------
start("一")
for i, t in enumerate([
    "掌握数据看板的基本概念、核心功能与应用场景,理解数据可视化、数据大屏、实时看板的区别与联系。",
    "熟悉看板的设计原则与布局规范(视觉层级、色彩搭配、图表选型、信息降噪、自适应布局),能够根据业务需求规划看板结构。",
    "学会根据数据特征选择合适的图表(柱状图、折线图、环形图、仪表盘、热力图、雷达图、数据卡片等)进行多维度展示。",
    "培养数据思维与可视化设计能力,独立完成从需求分析、版面设计、数据处理到看板落地的完整流程。",
    "理解静态看板与动态实时看板的差异,掌握数据刷新、动态轮播、联动交互、预警等功能的实现原理。"], 1):
    para(f"{i}. {t}")

# ---------- 二、实验环境 ----------
start("二")
para("1. 硬件环境:Windows 11 专业版计算机,可访问互联网(用于安装依赖包)。")
para("2. 软件环境(以下版本均为本次实验环境中实际查询到的版本):")
table([["软件 / 库", "版本", "用途"],
       ["Python", "3.13.5", "运行环境(使用独立虚拟环境 E:\\pytest\\venv)"],
       ["Streamlit", "1.67.0", "看板框架:页面、控件、自动刷新、多页导航"],
       ["Pandas / NumPy", "3.1.1 / 2.5.5", "数据生成、清洗、统计分析"],
       ["Plotly", "7.1.0", "交互式图表(柱状、折线、环形、热力、雷达、仪表盘)"],
       ["openpyxl / xlsxwriter", "3.1.5 / 3.3.4", "Excel 读写与带格式导出"],
       ["kaleido", "1.5.2", "把 Plotly 图表导出为 PNG(调用本机 Chrome 渲染)"],
       ["python-docx", "1.2.0", "生成 Word 数据报告与本实验报告"],
       ["Playwright", "1.65.2", "自动化交互测试与截图(驱动 Chrome)"],
       ["VS Code / Chrome", "1.147.0 / 158", "编辑器 / 浏览器"]],
      [4.2, 3.2, 10.0], caption="实验软件环境", align_cols=[1])
para("3. 开发方式:本次作业采用 AI 辅助开发(vibe coding)。由我提出需求,AI 编程助手(Claude Code)负责写代码、运行与测试;"
     "遇到手册没有说明、需要取舍的地方,助手先向我确认再动手,全过程记录在《开发过程记录》中(见本报告第三部分的「(四)AI 辅助开发中的需求确认」)。")

# ---------- 三、实验内容 ----------
start("三")
h2("0. 业务场景与总体说明")
para("本实验选择「电商销售数据」作为业务场景,实现了一个基于 Streamlit 的数据看板,手册规定的基础任务、进阶任务和扩展任务全部完成。"
     "看板分为两个页面:「销售看板」(主看板,含基础、进阶及大部分扩展功能)和「数据大屏」(扩展3)。")
table([["文件", "作用"],
       ["src/generate_data.py", "生成 2025 全年约 2 万条电商订单(含故意混入的脏数据,随机种子固定可复现)"],
       ["src/preprocess.py", "数据预处理,输出 orders_clean.csv / .xlsx 与清洗报告"],
       ["src/app.py", "入口:多页路由(销售看板 / 数据大屏)"],
       ["src/dashboard.py、common.py", "主看板页面;配色主题、CSS、KPI 卡片等公共部分"],
       ["src/alerts.py、realtime.py", "预警规则与弹窗(扩展2);Python 实时订单流(扩展1)"],
       ["src/bigscreen.py", "数据大屏页面(扩展3)"],
       ["src/analysis.py、report.py", "自动分析结论;Excel / PNG / Word / ZIP 导出(扩展4)"],
       ["src/test_*.py、shoot_final.py", "交互测试脚本、截图脚本(Playwright)"]],
      [5.2, 12.2], caption="项目文件说明")

h2("(一)基础任务")
h3("任务1  看板需求分析与版面设计")
para(f"业务场景为电商销售。核心展示需求:总销售额、订单数、平均客单价、退款率等核心指标;各品类与各渠道的销售对比和占比;全年销售趋势;订单明细。"
     "整体划分为数据概览区、维度统计区、趋势分析区、明细数据区四大模块,配色方案见表3。")
table([["用途", "颜色", "色值"], ["主色", "蓝", "#2563EB"], ["辅助色", "青 / 橙(橙色用于预警与强调)", "#06B6D4 / #F59E0B"],
       ["背景色", "浅灰蓝(卡片为白色)", "#F3F6FB"], ["文字色", "深灰蓝", "#1E293B"]],
      [3, 8, 6.4], caption="配色方案")
para("版面草图如下(进阶与扩展任务的区块也一并画入):")
sketch()

h3("任务2  实验数据准备与预处理")
para("数据由脚本生成并固定随机种子(2025),字段包括订单号、下单时间、品类、商品、省份、渠道、数量、单价、折扣、订单状态、用户ID、实付金额,保存为 CSV。"
     "为了让预处理有真实的工作量,生成时故意混入了少量脏数据:空值、重复订单、非法数量、非法日期、被放大的异常金额。"
     "数据还模拟了春节前、618、双11、双12 的大促高峰,以及周末略高、晚间下单集中的规律。")
table([["步骤", "处理结果"],
       ["原始数据", "20,080 行,12 列"],
       ["去除重复订单(按订单号)", "剔除 80 行,剩余 20,000 行"],
       ["剔除关键字段空值(品类、省份、渠道、单价)", "剔除 259 行,剩余 19,741 行"],
       ["剔除非法日期", "剔除 15 行,剩余 19,726 行"],
       ["剔除非法数量(须为 1~10 的整数)", "剔除 25 行,剩余 19,701 行"],
       ["剔除金额 ≠ 数量×单价×折扣的订单", "剔除 20 行,剩余 19,681 行"],
       ["清洗完成", f"19,681 行;时间 2025-01-01 ~ 2025-12-31;无空值,订单号唯一"]],
      [8.4, 9.0], caption="数据预处理过程与结果")
para("整理出三类统计维度:时间维度(日期、月份、星期、小时)、分类维度(品类、省份、渠道、订单状态)、数值维度(数量、单价、实付金额)。"
     "预处理中有一个取舍:最初我还加了「IQR 3 倍离群值」一步,结果一次剔除了 434 行,远多于注入的 20 条异常,说明误删了真实的大额订单(如一次买 5 件手机)。"
     "因此去掉了这一步,金额异常改由「实付金额必须等于数量×单价×折扣」校验。")

h3("任务3  基础可视化图表搭建")
para("基于预处理后的数据,搭建了数据卡片、柱状图、折线图、环形图四类基础图表(统计口径为全部订单,含已退款、已取消订单,这是我确认过的口径):")
item("数据卡片:总销售额、订单数、平均客单价、退款率(含环比增长率)。")
item("横向柱状图:各品类销售额对比。  环形图:各渠道销售额占比。")
item("折线图:2025 年日销售额趋势,叠加 7 日移动平均线。")
picture("final_01_overview.png", 16.5, "数据概览区:标题栏与四张核心指标卡片")
picture("final_02_dimension.png", 16.5, "维度统计区:品类销售额柱状图与渠道占比环形图")
picture("final_03_trend.png", 16.5, "趋势分析区:日销售额折线图与 7 日均线")

h3("任务4  静态数据看板整合实现")
para("把标题栏、卡片、图表、明细表格整合到同一页面,统一圆角、阴影、字体与间距,并用主色/辅助色区分层级。整页效果如下(上半部分):")
picture("final_00_full_light.png", 14.5, "整合后的销售看板(亮色主题,页面上半部分)")

h3("任务5  实验结果验证与总结")
para("检查数据准确性的方法:不直接相信页面,而是用独立的 pandas 脚本重新计算,与页面显示逐项对比,两者一致:")
table([["指标", "pandas 独立计算", "页面显示"],
       ["总销售额", f"{total / 1e4:,.1f} 万元", "¥2,361.6万"],
       ["订单数", f"{len(df):,}", "19,681"],
       ["平均客单价", f"¥{df['pay_amount'].mean():,.0f}", "¥1,200"],
       ["退款率 / 取消率", f"{refund:.1f}% / {cancel:.1f}%", "7.1% / 5.1%"],
       ["12 月销售额环比", f"{mom:+.1f}%", "-26.2%(因 11 月有双11 高峰)"],
       ["数码家电销售额占比", f"{cat_share['数码家电']:.1f}%", "66.8%(柱状图 1,576.5 万)"]],
      [5, 6, 6.4], caption="看板数据与独立计算的核对", align_cols=[1, 2])
para("发现并经我确认的一个现象:数码家电占全年销售额的 66.8%,使占比图偏向一边。原因是手机、平板等商品单价较高。我选择保持现状,不改数据。"
     "整个过程中遇到的问题与解决办法汇总在第四部分。")

h2("(二)进阶任务")
h3("进阶1  动态视觉效果优化")
item("悬浮提示:所有图表都自定义了 hover 提示(品类、渠道、省份等会显示销售额、订单数、占比)。")
item("数值滚动动画:KPI 数值从 0 滚动到目标值。实测每 120ms 采样,依次读到 ¥774.1万 → ¥949.3万 → ¥2,334.4万 → ¥2,361.6万,确实在滚动。")
item("组件渐入、卡片悬浮上浮:用 CSS 动画实现。图表数据更新时有过渡动画。")
item("自动轮播:同一位置每 5 秒自动切换三张图表(月度销售额与订单数 / 省份 Top10 / 渠道×品类),可关闭轮播后手动选择。实测序列依次出现,与预期一致。")
item("自适应布局:屏宽大于 1100px 时 KPI 排成 4 列,小于 1100px 为 2 列,小于 640px 为单列;已在 1920、1440、1024、768、390 像素宽度下截图检查,无横向溢出。")
picture("final_05_hover.png", 12, "图表 hover 悬浮提示")
picture("final_06_carousel.png", 11, "自动轮播的三张图表(关闭轮播后逐个选取拼接)")
picture("final_22_responsive.png", 16.0, "自适应布局:手机宽度(左,390px)与平板宽度(右,768px),均自动重排、无横向溢出")

h3("进阶2  图表联动与筛选功能实现")
para("侧边栏提供时间范围、品类、渠道、省份、订单状态筛选,筛选后所有图表、卡片、排行榜同步更新;点击品类柱状图中的某一根柱子,其余图表只展示该品类的数据,再次点击同一根柱子或按「清除联动」可取消。"
     "实测:点击「家居日用」后订单数由 19,681 变为 3,038,与 pandas 统计的家居日用订单数一致;侧边栏选择「服饰鞋包」后为 4,237 单,同样一致。")
picture("final_12_linkage.png", 16.5, "点击品类柱状图后的联动效果(顶部显示联动提示,其余图表只显示该品类)")
picture("final_13_filter.png", 16.5, "侧边栏筛选(品类=服饰鞋包、渠道=App)后全部图表同步更新")
para("说明:Plotly 的环形图不支持「选择」事件,所以渠道环形图只能被联动,不能作为点击源。")

h3("进阶3  多维度数据分析可视化")
para("新增了下单时段热力图(星期×小时)、品类综合能力雷达图(销售额、订单数、客单价、件均数量、订单完成率,按各维度最大值归一化)、"
     "商品销售额 Top10 排行榜、全年销售目标完成度仪表盘,以及极值卡片(单日最高/最低、销售额最高省份和品类)。"
     "注意:仪表盘的全年目标 2500 万元是我设定的演示用假设(数据里没有真实目标),页面上已明确标注;仪表盘按全年数据计算,不受筛选器影响。")
picture("final_07_multi.png", 16.5, "多维度分析区:热力图、雷达图、排行榜、目标仪表盘与极值卡片")

h2("(三)扩展任务")
h3("扩展1  实时数据看板搭建")
para("数据源选用「Python 动态生成数据」:后台线程按泊松过程不断产生新订单(平时约 0.7 单/秒,每 90 秒出现一次订单高峰),看板用 st.fragment 定时刷新,"
     "刷新间隔可选 2 秒 / 5 秒 / 10 秒 / 30 秒 / 1 分钟,也可暂停。面板展示近 5 分钟订单数与销售额、近 1 分钟订单数(下单速率)、近 200 单退款率、近 5 分钟订单流图和最新订单列表。"
     "实时订单流是独立的监控模块,没有并入 2025 年历史统计,页面上已注明。")
para("测试:每 5.5 秒采样一次,「最后刷新」时间依次为 17:21:34、17:21:40、17:21:45、17:21:50、17:21:55,全部不同;累计订单由 251 增至 277,单调增长;关闭「实时刷新」开关后时间与订单数不再变化。")
picture("final_08_realtime.png", 16.5, "实时订单监控面板")

h3("扩展2  数据预警与异常监控")
para("对退款率、取消率、销售额月环比、近 1 分钟订单数设置了阈值。数据超出范围时:顶部出现预警横幅;对应 KPI 卡片变色(警告为橙色,严重为红色并闪烁);警告弹出右下角提示,严重弹出对话框,同一组预警每个会话只提醒一次。"
     "阈值在侧边栏可以实时调整。默认阈值是我依据本数据分布设的模拟假设(各品类、渠道的退款率都在 7% 左右),不是真实业务标准:")
table([["指标", "警告线", "严重线"], ["退款率", "≥ 7.5%", "≥ 9.0%"], ["取消率", "≥ 5.5%", "≥ 7.0%"],
       ["销售额月环比", "≤ -15%", "≤ -30%"], ["近 1 分钟订单数", "≥ 80 单", "≥ 110 单"]],
      [6, 5.7, 5.7], caption="预警阈值(演示假设)", align_cols=[1, 2])
para("测试:默认全年数据下,销售额月环比 -26.2% 触发警告,第 1 张卡片变橙;把退款率「严重线」调成 5% 后,弹出严重预警对话框,退款率卡片变红并闪烁,点击「我知道了」后弹窗关闭。")
picture("final_15_alert_warn.png", 16.5, "警告级预警:顶部横幅与卡片变橙")
picture("final_16_alert_crit_dialog.png", 16.5, "严重级预警:弹出提醒对话框")
picture("final_17_alert_crit_after.png", 16.5, "关闭对话框后:横幅仍在,对应卡片变红并闪烁")

h3("扩展3  大屏可视化与移动端适配")
para("单独做了一个「数据大屏」页面:深蓝渐变背景叠加网格线,标题发光;JS 绘制的动态粒子(粒子漂移、近距离连线);卡片为半透明毛玻璃并带沿边缘旋转的流光边框与折角;"
     "内容包含全年 KPI、品类/渠道/省份图表、目标仪表盘、实时订单(近 1 分钟订单数、订单流、滚动列表)、趋势图和热力图。"
     "根字号随屏宽缩放,≥2200px 的超宽屏再放大标题和边距,≤900px 自动变单列。已在 1920×1080、2560、768、390 宽度下测试,均无报错、无横向溢出。"
     "已知局限:1920×1080 一屏只能看到 KPI 和三列主体,底部的趋势图与热力图需要向下滚动。")
picture("final_19_bigscreen.png", 16.5, "数据大屏(1920 像素宽)")

h3("扩展4  数据统计分析与报告输出")
para("「数据分析」区的结论由代码根据当前筛选范围从数据中自动计算,不写死任何数字,分为数据规律、业务优势、存在问题三类。例如全年数据下得到:"
     "销售额最高月份是 2025-11(319.5 万元,占 13.5%);单日峰值 2025-11-11 是日销售额中位数的 5.6 倍;周末日均销售额比工作日高 14.4%;下单最集中的时段是 19~21 时;"
     "数码家电占 66.8%,品类集中度偏高。订单少于 50 条时程序拒绝给出结论,避免小样本误导。")
para("导出功能:Excel 数据汇总(订单明细 + 品类/渠道/省份/月度 4 张汇总表 + 分析结论)、CSV 明细、单张图表 PNG,以及「一键生成完整报告包」(Word 数据报告 + Excel + 5 张图表 PNG 打成 ZIP,图表固定使用亮色)。"
     "测试时 4 种下载都真实下到了文件;以 2025-07-01 ~ 2025-09-30 为筛选范围,Excel 明细 4,343 行、销售额合计 518.2 万元,与 pandas 独立计算一致。")
picture("final_10_analysis_export.png", 16.5, "自动生成的分析结论与导出区(已生成报告包,出现下载按钮)")

h3("扩展5  个性化定制与功能创新")
item("数据排序:订单明细可选择排序字段(下单时间、实付金额、单价、数量、折扣)、升降序和显示条数。")
item("数据钻取:品类 → 商品 → 省份两级下拉联动,逐层查看,例如「数码家电 → 平板电脑」的省份分布。")
item("历史数据对比:与紧邻的上一个等长周期对比。数据只有 2025 一年,所以所选范围不能超过数据总长度的一半;超过时程序会给出一个可行的建议区间。")
item("多主题切换:侧边栏开关切换亮色/暗色主题,图表、卡片、控件同步变化。")
picture("final_09_drill.png", 16.5, "数据钻取:数码家电 → 平板电脑")
picture("final_14_history.png", 16.5, "历史数据对比:2025-07-01~09-30 对比紧邻的前 92 天")
picture("final_11_sort.png", 16.5, "订单明细按实付金额排序")
picture("final_18_dark.png", 14.5, "暗色主题(页面上半部分)")

h2("(四)AI 辅助开发中的需求确认")
para("手册中有些地方没有说清楚。我要求助手遇到这种情况必须先问我、不得自行决定,以下是实际确认过的事项:")
table([["待确认事项", "我的决定"],
       ["业务场景", "电商销售数据"], ["默认主题与主色", "亮色简洁风,主色蓝色"], ["数据规模", "约 2 万条订单,2025 全年"],
       ["数码家电占比 66.8% 偏高", "保持现状,不调整数据"], ["销售额统计口径", "含退款、取消订单,另设退款率"],
       ["第 4 张卡片", "改为退款率(原与第 1 张重复)"], ["「自动轮播」轮播什么", "轮播多张图表"],
       ["进度仪表盘的目标值", "由助手设 2500 万并明确标注为假设"], ["实时数据源", "Python 实时模拟新订单"],
       ["预警阈值", "助手设默认值并标注为假设,可在侧边栏调整"], ["报告导出格式", "Word(.docx)+ 图表图片"],
       ["大屏与主看板的关系", "单独做一个大屏页面"]],
      [7, 10.4], caption="需求确认记录")

h2("(五)测试汇总")
para("所有功能都用 Playwright 驱动真实 Chrome 做过操作测试,而不是只看代码。主要结果:")
table([["功能", "测试方法", "结果"],
       ["数值滚动动画", "刷新后连续采样 KPI 文本", "774.1万→949.3万→2334.4万→2361.6万"],
       ["自动轮播", "每 5.5 秒读取高亮标签", "三张图依次出现"],
       ["点击联动", "按坐标点击柱子", "订单数 19,681 → 3,038(与 pandas 一致)"],
       ["筛选", "侧边栏选品类", "服饰鞋包 4,237 单(与 pandas 一致)"],
       ["实时刷新", "每 5.5 秒采样刷新时间与订单数", "时间全不同,订单数 251→277;暂停后不变"],
       ["预警", "调低阈值触发", "横幅、变色、弹窗、关闭弹窗均正常"],
       ["历史对比、钻取、排序", "日历点选日期并操作下拉框", "钻取 1,162 单 / 343.3 万 / 客单价 2,955,与 pandas 一致"],
       ["导出", "实际点击下载并检查文件", "xlsx / csv / png / zip 均成功;Excel 4,343 行与 pandas 一致"],
       ["响应式与大屏", "1920 / 2560 / 1024 / 768 / 390 宽度截图", "无报错、无横向溢出"]],
      [3.8, 6.2, 7.4], caption="功能测试汇总")

# ---------- 四、心得体会 ----------
start("四")
para("本次实验让我完整走了一遍「需求—数据—图表—整合—交互—实时—分析输出」的看板开发流程。下面只写实际遇到的问题与解决办法,以及由此得到的体会。")
para("遇到的问题与解决办法:", bold=True, indent=False)
probs = [
    ("命令行截图是空白页", "Streamlit 页面靠 websocket 渲染,Chrome 命令行截图在渲染完成前就拍了。改用 Playwright 驱动 Chrome,等页面渲染完再截图。"),
    ("预处理误删真实订单", "IQR 离群值规则一次删了 434 行,远多于注入的 20 条异常。去掉它,改用金额一致性校验,准确得多。"),
    ("数值滚动动画一直不生效", "排查时有两个原因:一是改了被导入的模块后没有重启服务,Streamlit 仍在用旧代码;二是 st.html 里的脚本只要含有「<」字符就不会执行(用最小例子验证过)。把比较运算改写为「>」形式,并在代码里加断言防止再犯。"),
    ("大屏页面一片空白", "我给 .stApp 加了 position:relative 和 z-index,把 Streamlit 的布局弄坏,容器高度变成 0,内容被裁掉。用脚本打印各层元素尺寸才定位到原因,最后让粒子画布用 z-index:-1,不再改动 .stApp。"),
    ("暗色模式下控件还是白底、图表文字看不见", "st.plotly_chart 默认套用 Streamlit 的亮色主题,需要传 theme=None;控件用脚本列出「背景偏白的元素」后逐个修复,而不是凭感觉猜选择器。"),
    ("历史对比的提示给错了建议", "超出数据范围时,我最初提示「选 7~12 月」,但这段的上一周期仍然在 2024 年,建议本身就是错的。测试时发现后,改成由程序计算出真正可行的区间。"),
    ("图表导出太慢", "逐张导出 5 张图要 25 秒(每张都重启一次浏览器内核),改用批量导出后约 7 秒。"),
    ("Word 自动化卡死", "用 Word 自动化打开文件时卡住了两次,我只结束了自己启动的那个进程,改用 WPS 自动化完成了模板格式转换。"),
]
for i, (a, b) in enumerate(probs, 1):
    para(f"{i}. {a}:{b}")
para("体会:", bold=True, indent=False, before=4)
for t in [
    "看板的数字必须用独立方法核对。我把页面显示的数据与另写的 pandas 计算逐项比对,才敢确认「数据准确」。",
    "「能运行」不等于「能用」。很多问题(动画不动、页面空白、颜色看不清)只有真实打开页面、真实操作之后才会暴露,所以后期我都用自动化脚本做交互测试。",
    "手册里有些内容(轮播什么、目标值是多少、阈值是多少)没有标准答案,这时先确认、再把假设写明白,比自作主张更可靠。本报告中的 2500 万目标和预警阈值都是明确标注的演示假设。",
    "实时看板的关键是「局部刷新」:只刷新需要变化的片段,而不是整页重绘,体验和性能都好得多。",
]:
    item(t)
para("说明与局限:", bold=True, indent=False, before=4)
for t in [
    "全部数据是模拟生成的,仅用于课程实验,不代表真实业务。",
    "仪表盘目标(2500 万)和预警阈值是演示假设;实时订单流是独立的模拟模块,没有并入历史统计。",
    "数据大屏在 1920×1080 下需向下滚动才能看到底部的趋势图与热力图。",
]:
    item(t)

# ====================== 装配:把新内容移动到对应小标题后面,并清掉模板里的空占位段 ======================
heads = {k: next(p for p in doc.paragraphs if p.text.strip().startswith(k + "、")) for k in sections}
for k, elems in sections.items():
    anchor = heads[k]._p
    # 删除该小标题到下一个小标题之间的空段
    nxt = anchor.getnext()
    while nxt is not None and nxt.tag == qn("w:p") and not "".join(nxt.itertext()).strip() and nxt not in elems:
        rm, nxt = nxt, nxt.getnext()
        rm.getparent().remove(rm)
    for e in elems:
        anchor.addnext(e)
        anchor = e

if len(sys.argv) > 2:      # 第 2 个参数 = 用户已修改过的版本;只沿用其"日期"行,不动别的
    user_p = Document(sys.argv[2]).paragraphs[3]
    new_p = doc.paragraphs[3]
    assert "日期" in user_p.text and "日期" in new_p.text and len(user_p.runs) == len(new_p.runs), "日期行结构不一致,放弃沿用"
    for ur, nr in zip(user_p.runs, new_p.runs):
        nr.text = ur.text
    print("已沿用用户修改的日期行:", repr(new_p.text.strip()))
doc.save(OUT)
print("saved", OUT, "| 图:", _figno[0], "| 表:", _tabno[0])
