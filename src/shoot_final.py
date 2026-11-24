"""重拍实验报告用的最终截图(用真实操作触发各功能,再按区块裁剪)。
运行前需要先启动看板: streamlit run src/app.py --server.port 8501
输出: screenshots/final_*.png
"""
import re
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from _dates_helper import set_range  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "screenshots"
URL = "http://localhost:8501"
W, H = 1440, 5800


def bbox(pg, selector, nth=0):
    loc = pg.locator(selector).nth(nth)
    loc.scroll_into_view_if_needed()
    return loc.bounding_box()


def clip(pg, name, top, bottom=None, pad=10, x0=300, x1=None):
    """截取 top 元素上沿 ~ bottom 元素下沿 之间的区域(bottom 缺省 = top 自己)。"""
    a = top if isinstance(top, dict) else bbox(pg, top)
    b = a if bottom is None else (bottom if isinstance(bottom, dict) else bbox(pg, bottom))
    y0, y1 = max(0, a["y"] - pad), b["y"] + b["height"] + pad
    pg.screenshot(path=str(OUT / name), clip={"x": x0, "y": y0, "width": (x1 or W) - x0, "height": y1 - y0})
    print("  ✓", name)


def new_page(b, w=W, h=H):
    pg = b.new_page(viewport={"width": w, "height": h})
    pg.goto(URL)
    pg.wait_for_selector(".kpi .value", timeout=40000)
    pg.wait_for_timeout(4500)
    return pg


def pick(pg, label, option):
    cb = pg.locator("[data-testid='stSelectbox']").filter(has_text=label).get_by_role("combobox")
    cb.scroll_into_view_if_needed(); pg.wait_for_timeout(400); cb.click(); pg.wait_for_timeout(900)
    pg.get_by_role("option", name=option, exact=True).click(); pg.wait_for_timeout(3200)


def section(pg, text):
    return pg.locator(".section", has_text=text).first.bounding_box()


with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)

    # ======== A. 默认状态(亮色、全年) ========
    print("A 默认亮色")
    pg = new_page(b)
    pg.screenshot(path=str(OUT / "final_00_full_light.png"), clip={"x": 0, "y": 0, "width": W, "height": 2000}); print("  ✓ final_00_full_light.png(整页上半)")
    clip(pg, "final_01_overview.png", ".dash-title", ".kpi-row", x0=300)
    # 基础任务:维度 + 趋势
    clip(pg, "final_02_dimension.png", section(pg, "② 维度统计"), bbox(pg, ".st-key-card_channel"))
    clip(pg, "final_03_trend.png", section(pg, "③ 趋势分析"), bbox(pg, ".st-key-card_trend"))

    # 进阶1:hover 提示 —— 鼠标悬停在品类柱上
    cat = bbox(pg, ".st-key-card_cat .bars .point path", 1)
    pg.mouse.move(cat["x"] + cat["width"] / 2, cat["y"] + cat["height"] / 2); pg.wait_for_timeout(900)
    a = bbox(pg, ".st-key-card_cat")
    pg.screenshot(path=str(OUT / "final_05_hover.png"), clip={"x": a["x"], "y": a["y"], "width": a["width"], "height": a["height"]}); print("  ✓ final_05_hover.png")
    pg.mouse.move(5, 5)

    # 进阶1:轮播的三张图(关掉自动轮播后逐个选择)
    pg.get_by_text("自动轮播").first.scroll_into_view_if_needed(); pg.get_by_text("自动轮播").first.click(); pg.wait_for_timeout(2500)
    parts = []
    for i, nm in enumerate(["月度销售额与订单数", "省份销售额 Top10", "渠道 × 品类销售额"]):
        pg.get_by_text(nm, exact=True).first.click(); pg.wait_for_timeout(2500)
        box = bbox(pg, ".st-key-card_carousel")
        f = OUT / f"_car{i}.png"
        pg.screenshot(path=str(f), clip={"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]}); parts.append(f)
    ims = [Image.open(f) for f in parts]
    sheet = Image.new("RGB", (ims[0].width, sum(i.height for i in ims)), "white")
    y = 0
    for im in ims:
        sheet.paste(im, (0, y)); y += im.height
    sheet.save(OUT / "final_06_carousel.png"); [f.unlink() for f in parts]; print("  ✓ final_06_carousel.png(三张图纵向拼接)")
    pg.get_by_text("自动轮播").first.click(); pg.wait_for_timeout(1500)

    # 进阶3:多维分析
    clip(pg, "final_07_multi.png", section(pg, "④ 多维度分析"), bbox(pg, ".st-key-card_gauge"), x0=300)
    # 扩展1 实时
    pg.wait_for_timeout(6000)
    clip(pg, "final_08_realtime.png", section(pg, "⑤ 实时订单监控"), bbox(pg, ".st-key-card_live_feed"), pad=60)
    # 扩展5:钻取(数码家电 → 平板电脑)
    pick(pg, "第 1 层", "数码家电"); pick(pg, "第 2 层", "平板电脑")
    clip(pg, "final_09_drill.png", section(pg, "⑦ 数据钻取"), bbox(pg, ".st-key-card_drill"))
    # 扩展4:分析结论 + 导出区(先生成报告包,让下载按钮出现)
    pg.get_by_text("一键生成完整报告包").first.scroll_into_view_if_needed(); pg.get_by_text("一键生成完整报告包").first.click()
    pg.get_by_text("下载报告包").first.wait_for(timeout=120000); pg.wait_for_timeout(1500)
    clip(pg, "final_10_analysis_export.png", section(pg, "⑧ 数据分析与报告导出"), bbox(pg, ".st-key-card_export"))
    # 扩展5:排序(实付金额降序)
    pick(pg, "排序依据", "实付金额")
    d = section(pg, "⑨ 订单明细")
    pg.screenshot(path=str(OUT / "final_11_sort.png"), clip={"x": 300, "y": d["y"] - 10, "width": W - 300, "height": 560}); print("  ✓ final_11_sort.png")
    pg.close()

    # ======== B. 筛选 + 点击联动 ========
    print("B 筛选与联动")
    pg = new_page(b)
    bars = pg.locator(".st-key-card_cat .bars .point path")
    bb = bars.nth(1).bounding_box(); pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2); pg.wait_for_timeout(4500)
    pg.screenshot(path=str(OUT / "final_12_linkage.png"), clip={"x": 0, "y": 0, "width": W, "height": 1180}); print("  ✓ final_12_linkage.png")
    pg.close()
    pg = new_page(b)
    pg.locator("[data-testid='stSidebar'] [data-testid='stMultiSelect']").first.click(); pg.wait_for_timeout(700)
    pg.get_by_role("option", name="服饰鞋包").click(); pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
    pg.locator("[data-testid='stSidebar'] [data-testid='stMultiSelect']").nth(1).click(); pg.wait_for_timeout(700)
    pg.get_by_role("option", name="App").click(); pg.keyboard.press("Escape"); pg.wait_for_timeout(4500)
    pg.screenshot(path=str(OUT / "final_13_filter.png"), clip={"x": 0, "y": 0, "width": W, "height": 1180}); print("  ✓ final_13_filter.png")

    # ======== C. 历史对比(缩短时间范围) ========
    print("C 历史对比")
    pg.close(); pg = new_page(b)
    set_range(pg, "七月", "九月", 30)
    clip(pg, "final_14_history.png", section(pg, "⑥ 历史数据对比"), bbox(pg, ".st-key-card_hist_chart"))
    pg.close()

    # ======== D. 预警 ========
    print("D 预警")
    pg = new_page(b)
    pg.screenshot(path=str(OUT / "final_15_alert_warn.png"), clip={"x": 300, "y": 80, "width": W - 300, "height": 440}); print("  ✓ final_15_alert_warn.png")
    pg.get_by_text("预警阈值").first.click(); pg.wait_for_timeout(500)
    box = pg.get_by_label("退款率 严重"); box.fill("5"); box.press("Enter"); pg.wait_for_timeout(3500)
    pg.screenshot(path=str(OUT / "final_16_alert_crit_dialog.png"), clip={"x": 0, "y": 0, "width": W, "height": 900}); print("  ✓ final_16_alert_crit_dialog.png")
    pg.get_by_role("button", name="我知道了").click(); pg.wait_for_timeout(2500)
    pg.screenshot(path=str(OUT / "final_17_alert_crit_after.png"), clip={"x": 300, "y": 80, "width": W - 300, "height": 440}); print("  ✓ final_17_alert_crit_after.png")
    pg.close()

    # ======== E. 暗色模式 ========
    print("E 暗色")
    pg = new_page(b)
    pg.get_by_text("暗色模式").first.click(); pg.wait_for_timeout(8000)
    pg.screenshot(path=str(OUT / "final_18_dark.png"), clip={"x": 0, "y": 0, "width": W, "height": 1900}); print("  ✓ final_18_dark.png")
    pg.close()

    # ======== F. 大屏 + 手机 ========
    print("F 大屏与移动端")
    pg = b.new_page(viewport={"width": 1920, "height": 1500})
    pg.goto(URL + "/bigscreen"); pg.wait_for_selector(".kpi .value", timeout=40000); pg.wait_for_timeout(8000)
    pg.screenshot(path=str(OUT / "final_19_bigscreen.png")); print("  ✓ final_19_bigscreen.png")
    pg.close()
    pg = b.new_page(viewport={"width": 390, "height": 2400})
    pg.goto(URL); pg.wait_for_selector(".kpi .value", timeout=40000); pg.wait_for_timeout(6000)
    pg.screenshot(path=str(OUT / "final_20_mobile.png")); print("  ✓ final_20_mobile.png")
    pg.close()
    pg = b.new_page(viewport={"width": 768, "height": 2400})
    pg.goto(URL); pg.wait_for_selector(".kpi .value", timeout=40000); pg.wait_for_timeout(6000)
    pg.screenshot(path=str(OUT / "final_21_tablet.png")); print("  ✓ final_21_tablet.png")
    b.close()
print("DONE")
