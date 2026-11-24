"""公共模块:配色主题、数据加载、样式(CSS)、KPI 卡片 HTML。"""
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "orders_clean.csv"

# 全年销售目标:模拟假设(数据里没有真实目标),用于进度仪表盘。可在此修改。
ANNUAL_TARGET = 2500 * 1e4

LIGHT = dict(name="light", primary="#2563EB", cyan="#06B6D4", orange="#F59E0B", purple="#8B5CF6",
             bg="#F3F6FB", card="#FFFFFF", text="#1E293B", muted="#64748B", border="#E2E8F0",
             grid="#E8EDF5", soft="#93C5FD", good="#16A34A", bad="#DC2626")
DARK = dict(name="dark", primary="#3B82F6", cyan="#22D3EE", orange="#FBBF24", purple="#A78BFA",
            bg="#0B1220", card="#111B2E", text="#E2E8F0", muted="#94A3B8", border="#1F2D45",
            grid="#1F2D45", soft="#1E3A5F", good="#4ADE80", bad="#F87171")
PALETTE = ["#2563EB", "#06B6D4", "#8B5CF6", "#F59E0B", "#10B981", "#EC4899"]

WEEKDAYS = list("一二三四五六日")


def current_theme() -> dict:
    """根据 session_state['dark'] 返回当前主题配色(亮色为默认)。"""
    return DARK if st.session_state.get("dark", False) else LIGHT


@st.cache_data
def load() -> pd.DataFrame:
    return pd.read_csv(DATA, parse_dates=["order_time"])


def css(T: dict) -> str:
    return f"""
<style>
.block-container {{ padding-top: 3.5rem; max-width: 1500px; }}
@keyframes fadeUp {{ from {{ opacity:0; transform:translateY(16px); }} to {{ opacity:1; transform:none; }} }}
.dash-title {{ background: linear-gradient(90deg,{T['primary']},{T['cyan']}); color:#fff; padding:18px 26px;
  border-radius:14px; margin-bottom:14px; animation: fadeUp .6s ease both; }}
.dash-title h1 {{ color:#fff; font-size:1.7rem; margin:0; padding:0; }}
.dash-title p {{ margin:4px 0 0; opacity:.92; font-size:.9rem; }}
.kpi-row {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; }}
.kpi {{ background:{T['card']}; border:1px solid {T['border']}; border-left:5px solid {T['primary']};
  border-radius:12px; padding:16px 18px; box-shadow:0 1px 3px rgba(15,23,42,.06);
  animation: fadeUp .6s ease both; transition: transform .2s, box-shadow .2s; }}
.kpi:nth-child(2) {{ animation-delay:.08s; }} .kpi:nth-child(3) {{ animation-delay:.16s; }}
.kpi:nth-child(4) {{ animation-delay:.24s; }}
.kpi:hover {{ transform:translateY(-3px); box-shadow:0 8px 18px rgba(37,99,235,.16); }}
.kpi .label {{ color:{T['muted']}; font-size:.85rem; }}
.kpi .value {{ color:{T['text']}; font-size:1.9rem; font-weight:700; line-height:1.3; }}
.kpi .delta {{ font-size:.85rem; font-weight:600; color:{T['muted']}; }}
.kpi .up {{ color:{T['good']}; }} .kpi .down {{ color:{T['bad']}; }}
@keyframes blink {{ 0%,100% {{ box-shadow:0 0 0 0 rgba(220,38,38,.0); border-color:{T['bad']}; }}
  50% {{ box-shadow:0 0 14px 4px rgba(220,38,38,.55); border-color:transparent; }} }}
.kpi.warn {{ border-color:{T['orange']}; background:rgba(245,158,11,.10); }}
.kpi.warn .value {{ color:{T['orange']}; }}
.kpi.crit {{ background:rgba(220,38,38,.10); animation: blink 1.1s ease-in-out infinite; }}
.kpi.crit .value {{ color:{T['bad']}; }}
.alert {{ border-radius:10px; padding:9px 14px; margin:6px 0; font-size:.9rem; font-weight:600; }}
.alert.warn {{ background:rgba(245,158,11,.14); color:{T['orange']}; border:1px solid {T['orange']}; }}
.alert.crit {{ background:rgba(220,38,38,.14); color:{T['bad']}; border:1px solid {T['bad']}; animation: blink 1.1s infinite; }}
.alert.ok {{ background:rgba(22,163,74,.10); color:{T['good']}; border:1px solid {T['good']}; }}
.section {{ font-size:1.05rem; font-weight:700; color:{T['text']}; margin:20px 0 8px;
  padding-left:10px; border-left:4px solid {T['primary']}; }}
[class*="st-key-card"] {{ background:{T['card']}; border:1px solid {T['border']}; border-radius:12px;
  padding:6px 10px 12px; box-shadow:0 1px 3px rgba(15,23,42,.05); animation: fadeUp .7s ease both; }}
.dots {{ display:flex; gap:8px; flex-wrap:wrap; margin:2px 0 4px; }}
.dot {{ padding:3px 12px; border-radius:99px; font-size:.8rem; background:{T['bg']}; color:{T['muted']};
  border:1px solid {T['border']}; transition: all .3s; }}
.dot.on {{ background:{T['primary']}; color:#fff; border-color:{T['primary']}; }}
.chip {{ display:inline-block; padding:3px 12px; margin-right:8px; border-radius:99px; font-size:.82rem;
  background:#DBEAFE; color:{T['primary']}; font-weight:600; }}
.rank {{ width:100%; border-collapse:collapse; font-size:.9rem; }}
.rank td {{ padding:7px 6px; border-bottom:1px solid {T['border']}; color:{T['text']}; }}
.rank .no {{ width:34px; }}
.badge {{ display:inline-block; width:22px; height:22px; line-height:22px; text-align:center; border-radius:50%;
  font-size:.75rem; font-weight:700; background:{T['bg']}; color:{T['muted']}; }}
.badge.g1 {{ background:#F59E0B; color:#fff; }} .badge.g2 {{ background:#94A3B8; color:#fff; }}
.badge.g3 {{ background:#D97706; color:#fff; }}
.bar {{ height:8px; border-radius:4px; background:linear-gradient(90deg,{T['primary']},{T['cyan']}); }}
.bar-bg {{ background:{T['bg']}; border-radius:4px; width:100%; }}
.ext-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.ext {{ background:{T['bg']}; border-radius:10px; padding:10px 12px; }}
.ext .t {{ font-size:.78rem; color:{T['muted']}; }} .ext .v {{ font-size:1.05rem; font-weight:700; color:{T['text']}; }}
.ext .s {{ font-size:.78rem; color:{T['muted']}; }}
@media (max-width: 1100px) {{ .kpi-row {{ grid-template-columns:repeat(2,1fr); }} .kpi .value {{ font-size:1.6rem; }} }}
@media (max-width: 640px) {{ .kpi-row {{ grid-template-columns:1fr; }} .dash-title h1 {{ font-size:1.3rem; }}
  .block-container {{ padding-left:.8rem; padding-right:.8rem; }} .ext-grid {{ grid-template-columns:1fr; }} }}
</style>
"""


def dark_css(T: dict) -> str:
    """Streamlit 自带控件在暗色下的覆盖样式(亮色由 .streamlit/config.toml 负责)。"""
    return f"""
<style>
.stApp {{ background:{T['bg']}; color:{T['text']}; }}
[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stSidebar"] {{ background:{T['card']}; }}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp label,.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stWidgetLabel"] p {{ color:{T['text']} !important; }}
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"], .stDateInput input,
.stNumberInput input, [data-testid="stDateInputField"], [data-testid="stNumberInputContainer"],
[data-testid="stNumberInputContainer"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] div, [data-testid="stMultiSelect"] > div > div {{
  background-color:{T['bg']} !important; color:{T['text']} !important; border-color:{T['border']} !important; }}
.stApp input, .stApp [data-baseweb="select"] div, .stApp [data-testid="stDateInputField"] * {{
  color:{T['text']} !important; -webkit-text-fill-color:{T['text']} !important; opacity:1 !important; }}
.stApp input::placeholder {{ color:{T['muted']} !important; -webkit-text-fill-color:{T['muted']} !important; opacity:1 !important; }}
[data-testid="stSelectbox"] [role="group"], [data-testid="stSelectbox"] [role="group"] div {{
  background-color:{T['bg']} !important; border-color:{T['border']} !important; }}
[data-testid="stAlertContainer"] {{ background-color:rgba(59,130,246,.16) !important; }}
[data-testid="stAlertContainer"] * {{ color:{T['text']} !important; }}
[data-testid="stButtonGroup"] button {{ background-color:{T['card']} !important; border:1px solid {T['border']} !important; }}
[data-testid="stButtonGroup"] button * {{ color:{T['text']} !important; }}
[data-testid="stButtonGroup"] button[aria-checked="true"] {{ background-color:{T['primary']} !important; }}
[data-testid="stButtonGroup"] button[aria-checked="true"] * {{ color:#fff !important; }}
[data-baseweb="tag"], [data-baseweb="tag"] span {{ background-color:{T['primary']} !important; color:#fff !important; }}
[data-testid="stExpander"] details, [data-testid="stExpander"] summary {{ background:{T['card']} !important; }}
[data-baseweb="select"] span, [data-baseweb="select"] input {{ color:{T['text']} !important; }}
[data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="calendar"], [data-baseweb="menu"] {{
  background:{T['card']} !important; color:{T['text']} !important; }}
.stButton button, .stDownloadButton button {{ background:{T['card']}; color:{T['text']}; border:1px solid {T['border']}; }}
[data-testid="stDataFrame"] {{ filter: invert(0.9) hue-rotate(180deg); }}
[data-testid="stExpander"] {{ background:{T['card']}; border-color:{T['border']}; }}
[data-testid="stExpander"] summary p {{ color:{T['text']} !important; }}
[data-testid="stSegmentedControl"] button {{ color:{T['text']}; }}
</style>
"""


COUNT_JS = """
<script>
window.__kpi_ran = (window.__kpi_ran || 0) + 1;
try {
(function(){
  var tries = 0;
  function run(){
    var els = document.querySelectorAll('.kpi .value[data-target]');
    if (!els.length && 40 > tries++) { setTimeout(run, 50); return; }   // 等元素挂载后再执行
    els.forEach(function(el){
      if (el.dataset.done) return; el.dataset.done = 1;
      var t=+el.dataset.target, d=+(el.dataset.dec||0), pre=el.dataset.pre||'', suf=el.dataset.suf||'';
      var fmt=function(n){return n.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});};
      var s=performance.now(), dur=1000;
      (function step(now){
        var p=Math.min((now-s)/dur,1), e=1-Math.pow(1-p,3);
        el.textContent = pre + fmt(t*e) + suf;
        if (1 > p) requestAnimationFrame(step);
      })(s);
    });
  }
  run();
})();
} catch (e) { window.__kpi_err = String(e); }
</script>
"""


def kpi_card(label: str, target: float, dec: int = 0, pre: str = "", suf: str = "", delta: float | None = None,
             sub: str = "", color: str = "#2563EB", level: str = "") -> str:
    """KPI 卡片;数值由前端 JS 做滚动动画(HTML 里先写好终值,JS 不可用时也正确)。"""
    final = f"{pre}{target:,.{dec}f}{suf}"
    d = ""
    if delta is not None:
        cls, arrow = ("up", "▲") if delta >= 0 else ("down", "▼")
        d = f'<div class="delta {cls}">{arrow} {abs(delta):.1f}% 环比</div>'
    elif sub:
        d = f'<div class="delta">{sub}</div>'
    return (f'<div class="kpi {level}" style="border-left-color:{color}"><div class="label">{label}</div>'
            f'<div class="value" data-target="{target}" data-dec="{dec}" data-pre="{pre}" data-suf="{suf}">{final}</div>'
            f'{d}</div>')
