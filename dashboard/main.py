import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler
import warnings
import requests
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# --------------------------
# 心知天气配置（填你自己的key）
# --------------------------
SENIVERSE_KEY = "SyBQ06H2yR2RIEJn3"  # ← 换成你自己的
NOW_URL = "https://api.seniverse.com/v3/weather/now.json"

def seniverse_now(city):
    params = {
        "key": SENIVERSE_KEY,
        "location": city,
        "language": "zh-Hans",
        "unit": "c"
    }
    try:
        r = requests.get(NOW_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("results"):
            now = data["results"][0]["now"]
            loc = data["results"][0]["location"]
            return {
                "name": loc["name"],
                "text": now["text"],
                "temp": now["temperature"],
                "humidity": now["humidity"],
                "wind": now["wind_speed"]
            }
    except Exception as e:
        st.error(f"请求失败：{e}")
    return None

# --------------------------
# 侧边栏
# --------------------------
with st.sidebar:
    st.title("🌍 大兴安岭环境监测系统")
    menu = st.radio(
        "请选择功能",
        ["大兴安岭气温分析", "实时天气数据"]
    )

# --------------------------
# 主页面
# --------------------------
st.title("📊 大兴安岭环境监测平台")

# ==========================
# 1. 大兴安岭气温分析
# ==========================
if menu == "大兴安岭气温分析":
    st.header("🌡 大兴安岭气温数据分析")
    sub_menu = st.selectbox(
        "选择分析类型",
        [
            "2013-2017年气温统计分析",
            "分年气温时空变化图",
            "通量与多变量分析"
        ]
    )

    if sub_menu == "2013-2017年气温统计分析":
        st.subheader("📈 2013-2017年大兴安岭气温对比与趋势")
        st.image("./2013-2017年大兴安岭气温对比图.png")

    elif sub_menu == "分年气温时空变化图":
        st.subheader("🌍 分年气温时空变化图")
        year = st.selectbox("选择年份", [2013,2014,2015,2016,2017])
        if year == 2013:
            st.image("./2013年大兴安岭气温变化图.png")
        elif year == 2014:
            st.image("./2014年大兴安岭气温变化图.png")
        elif year == 2015:
            st.image("./2015年大兴安岭气温变化图.png")
        elif year == 2016:
            st.image("./2016年大兴安岭气温变化图.png")
        elif year == 2017:
            st.image("./2017年大兴安岭气温变化图.png")

    elif sub_menu == "通量与多变量分析":
        st.subheader("🔍 通量数据与多变量分析")
        tab1, tab2, tab3, tab4 = st.tabs([
            "通量数据变化", "变量相关性", "因子载荷矩阵", "主成分分析"
        ])
        with tab1:
            st.image("./2017年大兴安岭站通量数据变化图.png")
        with tab2:
            st.image("./correlation_heatmap.png")
        with tab3:
            st.image("./factor_loadings_heatmap.png")
        with tab4:
            st.image("./factor_scores_timeseries.png")
            st.image("./scree_plot.png")

# ==========================
# 2. 实时天气数据（心知天气全球查询）
# ==========================
elif menu == "实时天气数据":
    st.header("🌤 全球实时天气查询（心知天气）")
    city = st.text_input("输入城市（中文/拼音/英文）", "北京")
    if st.button("查询天气"):
        with st.spinner("正在获取数据..."):
            w = seniverse_now(city)
        if w:
            st.subheader(f"{w['name']} 实时天气")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("天气状况", w["text"])
            col2.metric("温度", f"{w['temp']} ℃")
            col3.metric("湿度", f"{w['humidity']} %")
            col4.metric("风速", f"{w['wind']} m/s")
        else:
            st.warning("未找到该城市或接口返回异常")