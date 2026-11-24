"""扩展2:数据预警与异常监控。

默认阈值为【演示用的模拟假设】(手册未给出阈值),依据是本数据集的实际分布:
退款率约 7%,取消率约 5%。用户可在侧边栏实时调整。
"""
import pandas as pd
import streamlit as st

# 指标 -> (名称, 警告线, 严重线, 方向, 单位)。方向 "high"=越高越糟, "low"=越低越糟
DEFAULTS = {
    "refund": dict(name="退款率", warn=7.5, crit=9.0, direction="high", unit="%"),
    "cancel": dict(name="取消率", warn=5.5, crit=7.0, direction="high", unit="%"),
    "mom": dict(name="销售额月环比", warn=-15.0, crit=-30.0, direction="low", unit="%"),
    # 实时模块:每分钟订单数(模拟流平时约 40 单/分钟,高峰可到 110+)
    "rt": dict(name="近1分钟订单数", warn=80.0, crit=110.0, direction="high", unit="单"),
}


def settings_ui() -> dict:
    """侧边栏的阈值设置面板,返回当前阈值。"""
    th = {}
    with st.sidebar.expander("🚨 预警阈值(演示假设,可调)"):
        st.caption("默认值是依据本数据分布设的**模拟假设**,不是真实业务标准。")
        st.toggle("启用预警", value=True, key="alerts_on")
        for k, d in DEFAULTS.items():
            c1, c2 = st.columns(2)
            w = c1.number_input(f"{d['name']} 警告", value=d["warn"], step=0.5, key=f"w_{k}")
            c = c2.number_input(f"{d['name']} 严重", value=d["crit"], step=0.5, key=f"c_{k}")
            th[k] = dict(d, warn=w, crit=c)
    return th


def level_of(value: float | None, d: dict) -> str:
    if value is None or pd.isna(value):
        return ""
    if d["direction"] == "high":
        return "crit" if value >= d["crit"] else "warn" if value >= d["warn"] else ""
    return "crit" if value <= d["crit"] else "warn" if value <= d["warn"] else ""


def evaluate(values: dict, th: dict) -> list[dict]:
    """values: {"refund": 7.1, "cancel": 5.1, "mom": -26.2}。返回触发的预警列表(严重在前)。"""
    out = []
    if not st.session_state.get("alerts_on", True):
        return out
    for k, v in values.items():
        d = th[k]
        lv = level_of(v, d)
        if lv:
            line = d["crit"] if lv == "crit" else d["warn"]
            cmp_ = "≥" if d["direction"] == "high" else "≤"
            out.append(dict(key=k, level=lv, title=f"{d['name']}{'严重异常' if lv == 'crit' else '偏离警戒'}",
                            msg=f"{d['name']}当前 {v:+.1f}{d['unit']}" if k == "mom" else
                                f"{d['name']}当前 {v:.1f}{d['unit']}",
                            rule=f"{'严重' if lv == 'crit' else '警告'}线 {cmp_} {line:g}{d['unit']}"))
    return sorted(out, key=lambda a: a["level"] != "crit")


def banner(alerts: list[dict]) -> None:
    """页面顶部预警横幅。"""
    if not st.session_state.get("alerts_on", True):
        return
    if not alerts:
        st.markdown('<div class="alert ok">✅ 所有监控指标均在正常范围内</div>', unsafe_allow_html=True)
        return
    for a in alerts:
        icon = "🔴" if a["level"] == "crit" else "🟠"
        st.markdown(f'<div class="alert {a["level"]}">{icon} {a["title"]}:{a["msg"]}({a["rule"]})</div>',
                    unsafe_allow_html=True)


@st.dialog("⚠️ 数据预警提醒")
def _popup(alerts: list[dict], sig: tuple) -> None:
    for a in alerts:
        icon = "🔴" if a["level"] == "crit" else "🟠"
        st.markdown(f"**{icon} {a['title']}**  \n{a['msg']}({a['rule']})")
    if st.button("我知道了", type="primary"):
        st.session_state.acked = sig
        st.rerun()


def notify(alerts: list[dict]) -> None:
    """弹窗(出现严重预警时)+ 右下角 toast(出现警告时);同一组预警每个会话只提醒一次。"""
    if not alerts:
        return
    sig = tuple((a["key"], a["level"]) for a in alerts)
    if st.session_state.get("acked") == sig or st.session_state.get("toasted") == sig:
        return
    if any(a["level"] == "crit" for a in alerts):
        _popup(alerts, sig)
    else:
        for a in alerts:
            st.toast(f"{a['title']}:{a['msg']}", icon="🟠")
        st.session_state.toasted = sig
