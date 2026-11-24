"""任务2-2:数据预处理。读取 data/orders_raw.csv,输出 data/orders_clean.csv / .xlsx,
并把每一步剔除了多少行写入 data/preprocess_report.txt(供实验报告引用)。
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "orders_raw.csv"
CLEAN_CSV = ROOT / "data" / "orders_clean.csv"
CLEAN_XLSX = ROOT / "data" / "orders_clean.xlsx"
REPORT = ROOT / "data" / "preprocess_report.txt"


def main() -> None:
    df = pd.read_csv(RAW, encoding="utf-8-sig")
    log = [f"原始数据:{len(df)} 行,{df.shape[1]} 列"]

    def step(name: str, mask_keep: pd.Series) -> None:
        nonlocal df
        removed = int((~mask_keep).sum())
        df = df[mask_keep].copy()
        log.append(f"{name}:剔除 {removed} 行,剩余 {len(df)} 行")

    # 1 重复订单(同一订单号只留一条)
    step("去除重复订单", ~df.duplicated(subset="order_id", keep="first"))
    # 2 空值
    key_cols = ["category", "province", "channel", "unit_price"]
    log.append("空值统计(清洗前):" + ", ".join(f"{c}={int(df[c].isna().sum())}" for c in key_cols))
    step("剔除关键字段空值", df[key_cols].notna().all(axis=1))
    # 3 非法日期
    df["order_time"] = pd.to_datetime(df["order_time"], errors="coerce")
    step("剔除非法日期", df["order_time"].notna())
    # 4 非法数量(必须为 1~10 的正整数)
    step("剔除非法数量", df["quantity"].between(1, 10))
    # 5 金额异常值:实付金额必须等于 数量×单价×折扣(IQR 会误删真实大额订单,故不用)
    expected = (df["quantity"] * df["unit_price"] * df["discount"]).round(2)
    step("剔除金额与单价×数量×折扣不一致的订单", (df["pay_amount"] - expected).abs() < 0.05)

    # 衍生维度
    df["date"] = df["order_time"].dt.date.astype(str)
    df["month"] = df["order_time"].dt.strftime("%Y-%m")
    df["weekday"] = df["order_time"].dt.day_of_week.map(dict(enumerate("一二三四五六日")))
    df["hour"] = df["order_time"].dt.hour
    df = df.sort_values("order_time").reset_index(drop=True)

    df.to_csv(CLEAN_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(CLEAN_XLSX, index=False)
    log.append(f"清洗完成:{len(df)} 行,时间 {df['order_time'].min()} ~ {df['order_time'].max()}")
    log.append("三类维度:时间(date/month/weekday/hour)、分类(category/province/channel/status)、数值(quantity/unit_price/pay_amount)")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main()
