"""任务2-1:生成电商销售模拟数据(2025 全年,约 2 万条订单)。

输出 data/orders_raw.csv。为了让"预处理"有意义,故意混入少量脏数据:
空值、重复订单、数量/金额异常值、非法日期。随机种子固定,结果可复现。
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 2025
N_ORDERS = 20000
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "orders_raw.csv"

# 品类 -> (商品名, 单价区间, 全年权重)
CATALOG = {
    "数码家电": (["智能手机", "蓝牙耳机", "平板电脑", "智能手表", "充电宝"], (99, 4999), 0.26),
    "服饰鞋包": (["羽绒服", "运动鞋", "连衣裙", "双肩包", "牛仔裤"], (59, 899), 0.22),
    "家居日用": (["四件套", "收纳箱", "电饭煲", "保温杯", "台灯"], (19, 599), 0.16),
    "美妆个护": (["面霜", "口红", "洗发水", "防晒霜", "香水"], (29, 799), 0.14),
    "食品生鲜": (["坚果礼盒", "咖啡豆", "零食大包", "水果礼盒", "茶叶"], (15, 299), 0.12),
    "运动户外": (["瑜伽垫", "跑步机", "帐篷", "羽毛球拍", "骑行头盔"], (39, 1999), 0.10),
}
PROVINCES = {  # 省份 -> 权重(大致按电商消费活跃度)
    "广东": 14, "浙江": 10, "江苏": 10, "上海": 7, "北京": 7, "山东": 6, "四川": 6,
    "河南": 5, "湖北": 5, "福建": 4, "湖南": 4, "河北": 4, "安徽": 3, "陕西": 3,
    "重庆": 3, "广西": 3, "辽宁": 2, "云南": 2, "江西": 2,
}
CHANNELS = {"App": 0.50, "小程序": 0.30, "网页": 0.20}
STATUSES = {"已完成": 0.88, "已退款": 0.07, "已取消": 0.05}


def day_weights(days: pd.DatetimeIndex) -> np.ndarray:
    """日权重:平时平稳,618/双11/双12/春节前有大促高峰,周末略高。"""
    w = np.ones(len(days))
    w *= np.where(days.day_of_week >= 5, 1.15, 1.0)
    w *= 1 + 0.25 * (days.month - 1) / 11  # 全年缓慢增长
    for center, height, width in [("2025-06-18", 3.0, 3), ("2025-11-11", 4.5, 3),
                                  ("2025-12-12", 2.0, 2), ("2025-01-20", 1.6, 5)]:
        d = (days - pd.Timestamp(center)).days.to_numpy()
        w *= 1 + height * np.exp(-(d / width) ** 2)
    return w / w.sum()


def main() -> None:
    rng = np.random.default_rng(SEED)
    days = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    day = rng.choice(days, size=N_ORDERS, p=day_weights(days))
    # 一天内按"晚间高峰"采样小时
    hour_p = np.array([1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 7, 7, 6, 6, 6, 6, 7, 8, 9, 10, 10, 7, 3], float)
    hour = rng.choice(24, size=N_ORDERS, p=hour_p / hour_p.sum())
    ts = pd.to_datetime(day) + pd.to_timedelta(hour, "h") \
        + pd.to_timedelta(rng.integers(0, 3600, N_ORDERS), "s")

    cats = list(CATALOG)
    cat = rng.choice(cats, size=N_ORDERS, p=[CATALOG[c][2] for c in cats])
    product, price = [], []
    for c in cat:
        names, (lo, hi), _ = CATALOG[c]
        product.append(rng.choice(names))
        # 对数正态让价格偏低价位更常见
        p = lo + (hi - lo) * float(np.clip(rng.lognormal(-1.2, 0.8), 0, 1))
        price.append(round(p, 2))
    prov = list(PROVINCES)
    province = rng.choice(prov, size=N_ORDERS, p=np.array(list(PROVINCES.values())) / sum(PROVINCES.values()))
    channel = rng.choice(list(CHANNELS), size=N_ORDERS, p=list(CHANNELS.values()))
    status = rng.choice(list(STATUSES), size=N_ORDERS, p=list(STATUSES.values()))
    qty = rng.choice([1, 2, 3, 4, 5], size=N_ORDERS, p=[0.62, 0.22, 0.09, 0.05, 0.02])
    discount = np.round(rng.choice([1.0, 0.95, 0.9, 0.85, 0.8], size=N_ORDERS, p=[0.45, 0.2, 0.2, 0.1, 0.05]), 2)
    user = rng.integers(1, 6001, N_ORDERS)

    df = pd.DataFrame({
        "order_id": [f"E{2025}{i:06d}" for i in range(1, N_ORDERS + 1)],
        "order_time": ts,
        "category": cat,
        "product": product,
        "province": province,
        "channel": channel,
        "quantity": qty,
        "unit_price": price,
        "discount": discount,
        "status": status,
        "user_id": [f"U{u:05d}" for u in user],
    })
    df["pay_amount"] = (df["quantity"] * df["unit_price"] * df["discount"]).round(2)
    df = df.sort_values("order_time").reset_index(drop=True)
    df["order_time"] = df["order_time"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # ---- 注入脏数据 ----
    n = len(df)
    for col, k in [("province", 90), ("channel", 60), ("unit_price", 70), ("category", 40)]:
        df.loc[rng.choice(n, k, replace=False), col] = np.nan           # 空值
    df.loc[rng.choice(n, 25, replace=False), "quantity"] = rng.choice([0, -1, 999], 25)  # 非法数量
    df.loc[rng.choice(n, 20, replace=False), "pay_amount"] *= 50        # 金额异常放大
    df.loc[rng.choice(n, 15, replace=False), "order_time"] = "2025-13-45 99:99:99"  # 非法日期
    df = pd.concat([df, df.sample(80, random_state=SEED)], ignore_index=True)  # 重复订单
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"已生成 {len(df)} 行 -> {OUT}")


if __name__ == "__main__":
    main()
