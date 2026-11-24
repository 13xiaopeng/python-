"""电商销售数据看板 —— 入口(多页路由)。

运行:  streamlit run src/app.py
页面:  销售看板(dashboard.py)、数据大屏(bigscreen.py)
"""
import streamlit as st

st.set_page_config(page_title="电商销售数据看板", page_icon="📊", layout="wide")

pages = [st.Page("dashboard.py", title="销售看板", icon="📊", default=True)]
if __import__("pathlib").Path(__file__).with_name("bigscreen.py").exists():
    pages.append(st.Page("bigscreen.py", title="数据大屏", icon="🖥️"))
st.navigation(pages).run()
