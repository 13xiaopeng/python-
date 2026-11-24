"""大屏截图:python src/shot_big.py <输出> <宽> <高>"""
import sys
from playwright.sync_api import sync_playwright
out, w, h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": w, "height": h}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
    pg.goto("http://localhost:8501/bigscreen"); pg.wait_for_selector(".kpi .value", timeout=40000); pg.wait_for_timeout(7000)
    print("exceptions:", pg.locator("[data-testid='stException']").count(), "| js errors:", errs[:3],
          "| 粒子canvas:", pg.locator("#bs-particles").count(), "| 横向溢出:",
          pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"))
    pg.screenshot(path=out, full_page=False)
    b.close()
