"""交互验证脚本:用 Playwright 真实点击/筛选,检查联动、轮播、动画是否生效。"""
import sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8501"
SHOTS = "E:/pytest/screenshots/"

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 2400})
    pg.goto(URL); pg.wait_for_selector(".kpi .value", timeout=30000)

    # 1 数值滚动动画:刷新后很快读取,应处于中间值
    pg.reload(); pg.wait_for_selector(".kpi .value", timeout=30000)
    samples = []
    for _ in range(6):
        samples.append(pg.locator(".kpi .value").first.inner_text()); pg.wait_for_timeout(120)
    pg.wait_for_timeout(1500)
    print("1 动画采样:", samples, "| 终值:", pg.locator(".kpi .value").first.inner_text())

    # 2 轮播:每隔 6 秒读一次当前高亮的标签
    pg.wait_for_selector(".dot.on")
    seen = []
    for _ in range(4):
        seen.append(pg.locator(".dot.on").first.inner_text()); pg.wait_for_timeout(5500)
    print("2 轮播序列:", seen)

    # 3 点击联动:点击品类柱状图里的第 2 根柱子
    bars = pg.locator(".st-key-card_cat .bars .point path")
    print("3 柱子数量:", bars.count())
    before = pg.locator(".kpi .value").nth(1).inner_text()
    bars.nth(1).scroll_into_view_if_needed(); pg.wait_for_timeout(500)
    bb = bars.nth(1).bounding_box(); pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2); pg.wait_for_timeout(4000)
    chip = pg.locator(".chip")
    print("3 联动提示:", chip.first.inner_text() if chip.count() else "无(联动失败)",
          "| 订单数:", before, "->", pg.locator(".kpi .value").nth(1).inner_text())
    pg.screenshot(path=SHOTS + "test_linkage.png", full_page=False)

    # 4 清除联动
    if chip.count():
        pg.get_by_role("button", name="清除联动").click(); pg.wait_for_timeout(3000)
        print("4 清除后订单数:", pg.locator(".kpi .value").nth(1).inner_text(), "| chip:", pg.locator(".chip").count())

    # 5 侧边栏筛选:品类选"服饰鞋包"
    pg.locator("[data-testid='stSidebar'] [data-testid='stMultiSelect']").first.click()
    pg.get_by_role("option", name="服饰鞋包").click(); pg.wait_for_timeout(4000)
    print("5 筛选服饰鞋包后订单数:", pg.locator(".kpi .value").nth(1).inner_text(),
          "| 标题:", pg.locator(".dash-title p").inner_text())
    b.close()
