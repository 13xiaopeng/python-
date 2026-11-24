"""扩展2/5 验证:预警(横幅、变色、弹窗、闪烁)与暗色主题切换。"""
from playwright.sync_api import sync_playwright
S = "E:/pytest/screenshots/"
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 1500})
    pg.goto("http://localhost:8501"); pg.wait_for_selector(".kpi .value", timeout=30000); pg.wait_for_timeout(2500)
    print("1 exceptions:", pg.locator("[data-testid='stException']").count())
    print("1 横幅:", [t.strip() for t in pg.locator(".alert").all_inner_texts()])
    print("1 卡片 class:", pg.evaluate("[...document.querySelectorAll('.kpi')].map(e=>e.className)"))
    pg.screenshot(path=S + "ext_alert_light.png")

    # 暗色
    pg.get_by_text("暗色模式").first.click(); pg.wait_for_timeout(3500)
    print("2 暗色 exceptions:", pg.locator("[data-testid='stException']").count(),
          "| 背景:", pg.evaluate("getComputedStyle(document.querySelector('.stApp')).backgroundColor"))
    pg.screenshot(path=S + "ext_dark.png", full_page=False)

    # 把退款率严重线调成 5 -> 触发严重预警弹窗
    pg.get_by_text("预警阈值").first.click(); pg.wait_for_timeout(500)
    box = pg.get_by_label("退款率 严重"); box.fill("5"); box.press("Enter"); pg.wait_for_timeout(3500)
    print("3 弹窗数:", pg.locator("[role='dialog']").count(),
          "| 弹窗文字:", pg.locator("[role='dialog']").first.inner_text()[:80].replace("\n", " ") if pg.locator("[role='dialog']").count() else "无")
    print("3 卡片 class:", pg.evaluate("[...document.querySelectorAll('.kpi')].map(e=>e.className)"))
    pg.screenshot(path=S + "ext_alert_crit_dialog.png")
    if pg.locator("[role='dialog']").count():
        pg.get_by_role("button", name="我知道了").click(); pg.wait_for_timeout(2500)
        print("4 点击『我知道了』后弹窗数:", pg.locator("[role='dialog']").count())
        pg.screenshot(path=S + "ext_alert_crit_after.png")
    b.close()
