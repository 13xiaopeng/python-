"""扩展1 验证:实时面板是否按间隔自动刷新、数据是否真的在增长、刷新间隔/暂停是否生效。"""
import re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 1500})
    pg.goto("http://localhost:8501"); pg.wait_for_selector(".kpi .value", timeout=30000); pg.wait_for_timeout(3000)
    cap = pg.locator("[data-testid='stCaptionContainer']").filter(has_text="最后刷新")
    cap.first.scroll_into_view_if_needed()
    print("0 exceptions:", pg.locator("[data-testid='stException']").count())

    def grab():
        t = cap.first.inner_text()
        # 累计模拟订单数在第 4 张实时卡片的副标题里
        sub = [e for e in pg.locator(".kpi .delta").all_inner_texts() if "累计模拟订单" in e]
        total = int(re.search(r"([\d,]+)", sub[0]).group(1).replace(",", "")) if sub else None
        return re.search(r"最后刷新 (\S+)", t).group(1), total

    rows = []
    for _ in range(5):
        rows.append(grab()); pg.wait_for_timeout(5500)
    print("1 (最后刷新时间, 累计订单) 采样:", rows)
    print("1 刷新时间全部不同:", len({r[0] for r in rows}) == len(rows), "| 累计订单单调增长:",
          all(rows[i][1] < rows[i + 1][1] for i in range(len(rows) - 1)))
    pg.screenshot(path="E:/pytest/screenshots/ext_realtime.png")

    # 暂停:关掉"实时刷新"开关后,时间应不再变化
    pg.get_by_text("实时刷新").first.click(); pg.wait_for_timeout(1500)
    t1 = grab(); pg.wait_for_timeout(7000); t2 = grab()
    print("2 暂停后两次采样:", t1, t2, "| 未变化:", t1[0] == t2[0])
    b.close()
