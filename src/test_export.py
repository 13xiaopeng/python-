"""扩展4/5 验证:历史对比、数据钻取、排序、Excel/CSV/PNG/报告包下载。"""
import io, zipfile, os
from playwright.sync_api import sync_playwright
from _dates_helper import set_range
OUT = "E:/pytest/data/_dl/"; os.makedirs(OUT, exist_ok=True)

def pick(pg, label, option):
    cb = pg.locator("[data-testid='stSelectbox']").filter(has_text=label).get_by_role("combobox")
    cb.scroll_into_view_if_needed(); pg.wait_for_timeout(500); cb.click(); pg.wait_for_timeout(900)
    pg.get_by_role("option", name=option, exact=True).click(); pg.wait_for_timeout(3000)

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 2400}, accept_downloads=True)
    pg.goto("http://localhost:8501"); pg.wait_for_selector(".kpi .value", timeout=30000); pg.wait_for_timeout(3000)

    # 1 历史对比:把时间范围改为 2025-07-01 ~ 2025-12-31
    set_range(pg, "七月", "九月", 30)
    print("1 标题:", pg.locator(".dash-title p").inner_text()[:60])
    cap = pg.get_by_text("本期 ").first
    print("1 对比说明:", cap.inner_text()[:90] if cap.count() else "无(仍提示超范围)")
    print("1 info 提示数:", pg.locator("[data-testid='stAlert']").count())

    # 2 钻取:第 1 层选 数码家电
    pick(pg, "第 1 层", "数码家电")
    print("2 钻取说明:", pg.get_by_text("当前钻取范围").first.inner_text())

    # 3 排序:改成 实付金额 升序
    pick(pg, "排序依据", "实付金额")
    pg.get_by_text("升序").first.click(); pg.wait_for_timeout(3000)
    print("3 排序说明:", pg.get_by_text("条(符合条件共").first.inner_text())

    # 4 下载
    def dl(btn_name, fn):
        with pg.expect_download(timeout=90000) as d:
            pg.get_by_role("button", name=btn_name).first.click() if False else pg.get_by_text(btn_name, exact=False).first.click()
        path = OUT + fn; d.value.save_as(path); print("4", btn_name, "->", d.value.suggested_filename, os.path.getsize(path), "bytes"); return path
    x = dl("Excel 数据汇总", "x.xlsx"); c = dl("CSV 明细", "c.csv"); g = dl("下载所选图表 PNG", "g.png")
    pg.get_by_text("一键生成完整报告包").first.click()
    pg.get_by_text("下载报告包").first.wait_for(timeout=120000)
    z = dl("下载报告包", "r.zip")
    print("4 zip 内容:", zipfile.ZipFile(z).namelist())
    b.close()
