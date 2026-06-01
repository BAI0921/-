import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler
import warnings
import requests
from streamlit_geolocation import streamlit_geolocation
import base64

warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# --------------------------
# 图片转base64（必须这样才能显示！）
# --------------------------
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


# --------------------------
# 心知天气配置
# --------------------------
SENIVERSE_KEY = "SyBQ06H2yR2RIEJn3"
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
                "temp": float(now["temperature"]),
                "humidity": int(now["humidity"]),
                "wind": float(now["wind_speed"])
            }
    except Exception as e:
        st.error(f"请求失败：{e}")
    return None


# --------------------------
# 智能建议生成函数
# --------------------------
def get_clothing_suggestion(temp):
    if temp >= 30:
        return "👕 建议穿着清凉透气的短袖、短裤，选择浅色衣物更凉快"
    elif 25 <= temp < 30:
        return "👕 适合短袖+薄长裤，早晚可备一件薄外套"
    elif 15 <= temp < 25:
        return "👕 建议穿着长袖T恤+薄外套，搭配牛仔裤"
    elif 5 <= temp < 15:
        return "🧥 建议穿着厚卫衣/毛衣+外套，注意保暖"
    else:
        return "🧥 建议穿着羽绒服/厚棉衣，搭配围巾手套，做好防寒"


def get_sunscreen_suggestion(weather_text):
    sunny_words = ["晴", "多云"]
    if any(word in weather_text for word in sunny_words):
        return "☀️ 紫外线较强，建议出门涂抹防晒霜、戴帽子和太阳镜"
    elif "阴" in weather_text:
        return "☀️ 紫外线较弱，可根据情况决定是否防晒，敏感肌建议基础防护"
    else:
        return "☀️ 紫外线较弱，无需特别防晒，雨天记得带伞"


def get_outdoor_suggestion(weather_text, wind, temp):
    if "雨" in weather_text or "雷" in weather_text:
        return "🏃 不建议户外运动，雨天路滑且易感冒，可选择室内活动"
    elif wind > 10:
        return "🏃 风力较大，不适合跑步、骑行等户外活动，建议选择室内运动"
    elif temp > 35:
        return "🏃 气温过高，易中暑，建议早晚凉爽时段再进行户外活动"
    elif temp < 0:
        return "🏃 气温过低，建议做好保暖再进行短时间户外活动"
    else:
        return "🏃 天气适宜，非常适合户外运动，记得及时补充水分"


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
# 1. 大兴安岭气温分析界面
# ==========================
if menu == "大兴安岭气温分析":
    img_base64 = get_img_as_base64("daxinganling_bg.jpg")

    page_bg = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        top:0; left:0;
        width:100%; height:100%;
        background-image: inherit;
        background-size: cover;
        background-position: center;
        filter: blur(6px);
        opacity: 0.7;
        z-index: -1;
    }}
    .stMarkdown, .stHeader, .stSubheader, .stImage, .stSelectbox, .stTabs {{
        background-color: rgba(255,255,255,0.85);
        padding: 1rem;
        border-radius: 0.5rem;
    }}
    </style>
    """
    st.markdown(page_bg, unsafe_allow_html=True)

    st.markdown("""
在全球变暖的持续驱动下，大兴安岭生态系统正经历着从缓慢适应到剧烈转折的深刻演变。2017年以前，区域整体处于缓慢升温、偏冷湿的状态，特别是在2011至2015年间，生态系统长期适应稳定，气候的微小波动并未打破原有格局，呈现出落叶松占优、冻土稳定、湿地发育良好且耐寒物种稳定的低扰动特征。然而，2017年后区域气候进入加速暖干化与极端高温干旱频发阶段，并在2020至2024年间迎来关键拐点，气候改变从“小幅扰动”彻底转变为结构性冲击。气温的持续攀升首先加速了冻土的消融，进而引发湿地大面积萎缩，并推动原生针叶林逐步被北侵的阔叶林取代。这种生境的剧烈改变不仅造成生物物候错位、珍稀寒带物种衰退和生物多样性降低，还导致森林灾害频发。与此同时，土壤退化与区域碳汇功能的减弱，伴随着地质灾害、火灾及病虫害风险的全面上升，标志着整个寒温带生态系统正面临不可逆的结构性改变与持续攀升的生态风险。
""")

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
        year = st.selectbox("选择年份", [2013, 2014, 2015, 2016, 2017])
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
# 2. 实时天气数据界面（仅删除空框，保留生活建议）
# ==========================
elif menu == "实时天气数据":
    img_base64 = get_img_as_base64("weather_bg.jpg")

    page_bg = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        top:0; left:0;
        width:100%; height:100%;
        background-image: inherit;
        background-size: cover;
        background-position: center;
        filter: blur(5px);
        opacity: 0.5;
        background-color: rgba(0,0,0,0.3);
        z-index: -1;
    }}
    .stMetric, .stTextInput {{
        background-color: rgba(255,255,255,0.95);
        padding: 0.8rem;
        border-radius: 0.6rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .stMarkdown, .stHeader, .stSubheader {{
        color: #000000 !important;
        font-weight: 600 !important;
    }}
    </style>
    """
    st.markdown(page_bg, unsafe_allow_html=True)

    st.header("🌤 全球实时天气查询")

    # 状态变量：默认城市=南通
    if "city" not in st.session_state:
        st.session_state["city"] = "南通"

    st.subheader("📍 当前位置天气（默认南通，可GPS定位）")

    # 1. GPS定位按钮
    loc = streamlit_geolocation()
    lat = loc.get("latitude")
    lon = loc.get("longitude")

    # 2. 如果拿到经纬度 → 用经纬度查天气
    if lat and lon:
        with st.spinner("正在获取你当前位置天气..."):
            w = seniverse_now(f"{lon:.4f},{lat:.4f}")
        if w:
            st.session_state["city"] = w["name"]
        else:
            st.warning("定位天气失败，使用南通")
            st.session_state["city"] = "南通"

    # 3. 显示当前城市天气（带图标排版）
    with st.spinner(f"正在获取 {st.session_state['city']} 天气..."):
        w_current = seniverse_now(st.session_state["city"])
    if w_current:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏙️ 城市", w_current["name"])
        with col2:
            st.metric("🌤️ 天气", w_current["text"])
        with col3:
            st.metric("🌡️ 温度", f"{w_current['temp']} ℃")
        with col4:
            st.metric("💧 湿度", f"{w_current['humidity']} %")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("💨 风速", f"{w_current['wind']} m/s")

        # 保留生活建议部分
        st.divider()
        st.subheader("💡 今日生活建议")
        clothing = get_clothing_suggestion(w_current["temp"])
        sunscreen = get_sunscreen_suggestion(w_current["text"])
        outdoor = get_outdoor_suggestion(w_current["text"], w_current["wind"], w_current["temp"])

        st.info(clothing)
        st.info(sunscreen)
        st.info(outdoor)

    # 4. 查询其他城市天气（删除了你圈出的空框）
    st.divider()
    st.subheader("🔍 查询其他城市天气")
    city_input = st.text_input("输入城市名（如：北京、上海）", "")
    if city_input:
        with st.spinner(f"正在获取 {city_input} 天气..."):
            w_other = seniverse_now(city_input)
        if w_other:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏙️ 城市", w_other["name"])
            with col2:
                st.metric("🌤️ 天气", w_other["text"])
            with col3:
                st.metric("🌡️ 温度", f"{w_other['temp']} ℃")
            with col4:
                st.metric("💧 湿度", f"{w_other['humidity']} %")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("💨 风速", f"{w_other['wind']} m/s")

            # 其他城市的生活建议也保留
            st.divider()
            st.subheader("💡 今日生活建议")
            clothing = get_clothing_suggestion(w_other["temp"])
            sunscreen = get_sunscreen_suggestion(w_other["text"])
            outdoor = get_outdoor_suggestion(w_other["text"], w_other["wind"], w_other["temp"])

            st.info(clothing)
            st.info(sunscreen)
            st.info(outdoor)
        else:
            st.warning(f"未找到 {city_input} 的天气")