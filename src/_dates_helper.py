import re
def set_range(pg, start_month, end_month, end_day):
    """通过日历点选:起点 = start_month 1 号,终点 = end_month end_day 号。"""
    pg.locator("[data-testid='stSidebar'] [data-testid='stDateInputField']").first.click(); pg.wait_for_timeout(800)
    pg.get_by_text("一月", exact=True).first.click(); pg.get_by_role("option", name=start_month).click(); pg.wait_for_timeout(600)
    pg.locator("td[role=gridcell]:visible").filter(has_text=re.compile(r"^1$")).first.click(); pg.wait_for_timeout(800)
    pg.get_by_text(start_month, exact=True).first.click(); pg.get_by_role("option", name=end_month).click(); pg.wait_for_timeout(600)
    pg.locator("td[role=gridcell]:visible").filter(has_text=re.compile(rf"^{end_day}$")).first.click(); pg.wait_for_timeout(3500)
