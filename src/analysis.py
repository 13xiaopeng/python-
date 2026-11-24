"""扩展4:数据统计分析 —— 由代码从当前数据(受筛选器影响)自动算出结论,不写死任何数字。"""
import pandas as pd

MIN_N = 50  # 订单数少于此值的分组不参与"最高/最低"比较,避免小样本误导


def _wan(v: float) -> str:
    return f"¥{v / 1e4:,.1f}万"


def findings(v: pd.DataFrame) -> dict[str, list[str]]:
    """返回 {"规律": [...], "优势": [...], "问题": [...]}。数据太少时对应条目会被跳过。"""
    out: dict[str, list[str]] = {"规律": [], "优势": [], "问题": []}
    if len(v) < MIN_N:
        out["问题"].append(f"当前筛选条件下订单只有 {len(v)} 条,样本太少,不做统计结论。")
        return out
    total = v["pay_amount"].sum()

    # ---------- 规律 ----------
    m = v.groupby("month")["pay_amount"].sum()
    if len(m) >= 3:
        top3 = m.nlargest(3)
        out["规律"].append(f"销售额最高的月份是 {top3.index[0]}({_wan(top3.iloc[0])},占统计期 {top3.iloc[0] / total * 100:.1f}%);"
                         f"前三名 {'、'.join(top3.index)} 合计占 {top3.sum() / total * 100:.1f}%。")
    d = v.groupby("date")["pay_amount"].sum()
    if len(d) >= 7 and d.median() > 0:
        r = d.max() / d.median()
        out["规律"].append(f"单日销售额峰值出现在 {d.idxmax()}({_wan(d.max())}),是日销售额中位数的 {r:.1f} 倍"
                         f"{',呈现明显的促销型尖峰' if r >= 3 else ''}。")
    dd = v.assign(we=v["order_time"].dt.day_of_week >= 5).groupby("we").agg(s=("pay_amount", "sum"), n=("date", "nunique"))
    if len(dd) == 2 and (dd["n"] > 0).all():
        avg = dd["s"] / dd["n"]
        diff = (avg[True] / avg[False] - 1) * 100
        out["规律"].append(f"周末日均销售额 {_wan(avg[True])},工作日日均 {_wan(avg[False])},周末{'高' if diff >= 0 else '低'} {abs(diff):.1f}%。")
    h = v.groupby(v["order_time"].dt.hour).size()
    top_h = h.nlargest(3)
    out["规律"].append(f"下单最集中的时段是 {'、'.join(f'{x}时' for x in sorted(top_h.index))}," f"这三个小时的订单占全天 {top_h.sum() / h.sum() * 100:.1f}%。")

    # ---------- 优势 ----------
    c = v.groupby("category").agg(s=("pay_amount", "sum"), n=("order_id", "count"))
    if len(c):
        out["优势"].append(f"销售额最高的品类是「{c['s'].idxmax()}」,贡献 {_wan(c['s'].max())},占 {c['s'].max() / total * 100:.1f}%。")
        cc = c[c["n"] >= MIN_N]
        if len(cc) > 1:
            price = cc["s"] / cc["n"]
            out["优势"].append(f"客单价最高的品类是「{price.idxmax()}」(¥{price.max():,.0f}),最低的是「{price.idxmin()}」(¥{price.min():,.0f})。")
    ch = v.groupby("channel")["pay_amount"].sum()
    if len(ch):
        out["优势"].append(f"渠道方面「{ch.idxmax()}」贡献最大,占 {ch.max() / total * 100:.1f}%。")
    pv = v.groupby("province")["pay_amount"].sum().sort_values(ascending=False)
    if len(pv) >= 5:
        out["优势"].append(f"销售额前五的省份是 {'、'.join(pv.index[:5])},合计占 {pv.iloc[:5].sum() / total * 100:.1f}%,其中「{pv.index[0]}」居首({_wan(pv.iloc[0])})。")

    # ---------- 问题 ----------
    if len(c) >= 2 and c["s"].max() / total >= 0.5:
        out["问题"].append(f"品类集中度偏高:「{c['s'].idxmax()}」一个品类就占了 {c['s'].max() / total * 100:.1f}% 的销售额,对单一品类依赖较大。")
    refund = (v["status"] == "已退款").mean() * 100
    cancel = (v["status"] == "已取消").mean() * 100
    out["问题"].append(f"整体退款率 {refund:.1f}%、取消率 {cancel:.1f}%,合计约 {refund + cancel:.1f}% 的订单没有完成交易。")
    rr = v.assign(rf=v["status"] == "已退款").groupby("category").agg(rate=("rf", "mean"), n=("rf", "size"))
    rr = rr[rr["n"] >= MIN_N]
    if len(rr) > 1:
        out["问题"].append(f"退款率最高的品类是「{rr['rate'].idxmax()}」({rr['rate'].max() * 100:.1f}%),最低的是「{rr['rate'].idxmin()}」({rr['rate'].min() * 100:.1f}%),"
                         f"相差 {(rr['rate'].max() - rr['rate'].min()) * 100:.1f} 个百分点。")
    if len(m) >= 2 and m.iloc[-2] > 0:
        g = (m.iloc[-1] / m.iloc[-2] - 1) * 100
        if g < 0:
            out["问题"].append(f"最近一个月({m.index[-1]})销售额较上月{'下降' if g < 0 else '增长'} {abs(g):.1f}%,"
                             f"需要结合促销节奏判断是否属于大促后的正常回落。")
    if len(m) >= 3:
        out["问题"].append(f"销售额最低的月份是 {m.idxmin()}({_wan(m.min())}),只有最高月份的 {m.min() / m.max() * 100:.1f}%,淡旺季落差明显。")
    return out
