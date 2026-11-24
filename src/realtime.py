"""扩展1:实时数据流。

数据源 = Python 动态生成:后台线程持续"下单",以随机间隔(泊松过程)产生新订单,并周期性出现订单高峰。
看板用 st.fragment(run_every=...) 定时拉取快照,实现秒级 / 分钟级自动刷新。
线程随 Streamlit 进程常驻(st.cache_resource),多个浏览器会话共享同一份数据流。
"""
import math
import random
import threading
import time
from collections import deque

import pandas as pd
import streamlit as st

import generate_data as gd

BASE_RATE = 0.7        # 平时每秒约 0.7 单
BURST_PERIOD = 90      # 每 90 秒出现一次订单高峰
BACKFILL_SEC = 300     # 启动时回填最近 5 分钟,避免图表一开始是空的


class OrderStream:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.orders: deque = deque(maxlen=5000)
        self.rng = random.Random(20251111)
        self.seq = 0
        self.started = time.time()
        self._backfill()
        threading.Thread(target=self._run, daemon=True, name="order-stream").start()

    @staticmethod
    def rate_at(t: float) -> float:
        """t 时刻的下单速率(单/秒):基础速率 × 周期性高峰。"""
        return BASE_RATE * (1 + 1.8 * max(0.0, math.sin(2 * math.pi * t / BURST_PERIOD)) ** 4)

    def _make(self, ts: float) -> dict:
        r = self.rng
        cats = list(gd.CATALOG)
        cat = r.choices(cats, weights=[gd.CATALOG[c][2] for c in cats])[0]
        names, (lo, hi), _ = gd.CATALOG[cat]
        price = round(lo + (hi - lo) * min(1.0, r.lognormvariate(-1.2, 0.8)), 2)
        qty = r.choices([1, 2, 3, 4, 5], weights=[62, 22, 9, 5, 2])[0]
        disc = r.choices([1.0, 0.95, 0.9, 0.85, 0.8], weights=[45, 20, 20, 10, 5])[0]
        self.seq += 1
        return dict(
            order_id=f"L{self.seq:07d}", order_time=pd.Timestamp.fromtimestamp(ts),  # 本地时间
            category=cat, product=r.choice(names),
            province=r.choices(list(gd.PROVINCES), weights=list(gd.PROVINCES.values()))[0],
            channel=r.choices(list(gd.CHANNELS), weights=list(gd.CHANNELS.values()))[0],
            quantity=qty, unit_price=price, discount=disc, pay_amount=round(qty * price * disc, 2),
            status=r.choices(list(gd.STATUSES), weights=[w * 100 for w in gd.STATUSES.values()])[0])

    def _backfill(self) -> None:
        now = time.time()
        t = now - BACKFILL_SEC
        while t < now:
            t += self.rng.expovariate(self.rate_at(t - self.started))
            if t < now:
                self.orders.append(self._make(t))

    def _run(self) -> None:
        while True:
            time.sleep(self.rng.expovariate(self.rate_at(time.time() - self.started)))
            order = self._make(time.time())
            with self.lock:
                self.orders.append(order)

    def snapshot(self) -> pd.DataFrame:
        with self.lock:
            rows = list(self.orders)
        return pd.DataFrame(rows)


@st.cache_resource
def get_stream() -> OrderStream:
    return OrderStream()
