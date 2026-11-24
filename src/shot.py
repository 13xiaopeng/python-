"""截图工具:用本机 Chrome 打开看板,等待渲染完成后整页截图。
用法: python src/shot.py <输出文件> [宽] [url] [wait_ms] [视口高度]
"""
import sys
from playwright.sync_api import sync_playwright

out = sys.argv[1]
width = int(sys.argv[2]) if len(sys.argv) > 2 else 1440
url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8501"
wait = int(sys.argv[4]) if len(sys.argv) > 4 else 6000
height = int(sys.argv[5]) if len(sys.argv) > 5 else 2200

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": width, "height": height})
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(url)
    pg.wait_for_selector("[data-testid='stMain']", timeout=30000)
    pg.wait_for_timeout(wait)
    exc = pg.locator("[data-testid='stException']").count()
    print("exceptions on page:", exc, "| console errors:", len(errs))
    pg.screenshot(path=out, full_page=True)
    b.close()
