import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler
from streamlit_geolocation import streamlit_geolocation
import warnings
import requests
import random
import time
from urllib.parse import quote
import math

warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ====================== 阿里云图片配置 ======================
ALIYUN_BG1 = "https://bairuobing.oss-cn-hangzhou.aliyuncs.com/static/daxinganling_bg.png"
ALIYUN_BG2 = "https://bairuobing.oss-cn-hangzhou.aliyuncs.com/static/weather_bg.png"
ALIYUN_STATIC = "https://bairuobing.oss-cn-hangzhou.aliyuncs.com/static/"

CAROUSEL_IMGS = [
    ALIYUN_STATIC + "img1.png",
    ALIYUN_STATIC + "img2.png",
    ALIYUN_STATIC + "img3.png"
]


# ===========================================================

def set_background(img_url, is_green=False):
    safe_url = quote(img_url, safe=':/')
    green_css = ""
    if is_green:
        green_css = """
        html, body, [data-testid="stAppViewContainer"], .stMarkdown, .stText, 
        h1, h2, h3, h4, h5, h6, p, div, span, li, .metric-text {
            color: #00CC66 !important;
            font-weight: 500 !important;
        }
        """
    st.markdown(f"""
    <style>
    {green_css}
    [data-testid="stAppViewContainer"] {{
        background-image: url("{safe_url}");
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
        min-height:100vh !important;
    }}
    [data-testid="stHeader"]{{background:transparent !important;}}
    .block-container {{background-color: rgba(0,0,0,0.05) !important;}}
    </style>
    """, unsafe_allow_html=True)


# ========== 初始化 session_state ==========
if 'agreed_carbon' not in st.session_state:
    st.session_state.agreed_carbon = False
if 'weather_history' not in st.session_state:
    st.session_state.weather_history = []
if 'city' not in st.session_state:
    st.session_state.city = "南通"

# --------------------------
# 心知天气配置
# --------------------------
SENIVERSE_KEY = "SyBQ06H2yR2RIEJn3"
NOW_URL = "https://api.seniverse.com/v3/weather/now.json"
DAILY_URL = "https://api.seniverse.com/v3/weather/daily.json"
AQI_URL = "https://api.seniverse.com/v3/air/now.json"


def seniverse_now(city):
    params = {"key": SENIVERSE_KEY, "location": city, "language": "zh-Hans", "unit": "c"}
    try:
        r = requests.get(NOW_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("results"):
            now = data["results"][0]["now"]
            loc = data["results"][0]["location"]
            return {
                "name": loc["name"], "text": now["text"], "temp": float(now["temperature"]),
                "humidity": int(now["humidity"]), "wind": float(now["wind_speed"]),
                "wind_dir": now.get("wind_direction", "北风")
            }
    except:
        return None


def seniverse_daily(city, days=3):
    params = {"key": SENIVERSE_KEY, "location": city, "language": "zh-Hans", "unit": "c", "start": 0, "days": days}
    try:
        r = requests.get(DAILY_URL, params=params, timeout=10)
        data = r.json()
        if data.get("results"):
            return data["results"][0]["daily"]
    except:
        return None


def seniverse_aqi(city):
    params = {"key": SENIVERSE_KEY, "location": city, "language": "zh-Hans"}
    try:
        r = requests.get(AQI_URL, params=params, timeout=10)
        data = r.json()
        if data.get("results"):
            aqi = data["results"][0]["air"]["city"]
            return {"aqi": int(aqi.get("aqi", 0)), "quality": aqi.get("quality", ""), "pm25": int(aqi.get("pm25", 0))}
    except:
        return None


def get_weather_icon(text):
    icon_map = {"晴": "☀️", "多云": "⛅", "阴": "☁️", "小雨": "🌧️", "中雨": "🌧️", "大雨": "🌧️", "雷阵雨": "⛈️",
                "雪": "❄️"}
    for k in icon_map:
        if k in text:
            return icon_map[k]
    return "🌤️"


def get_clothing_suggestion(temp):
    if temp >= 30:
        return "👕 清凉短袖"
    elif 25 <= temp < 30:
        return "👕 短袖+薄长裤"
    elif 15 <= temp < 25:
        return "👕 长袖T恤+薄外套"
    elif 5 <= temp < 15:
        return "🧥 厚卫衣/毛衣"
    else:
        return "🧥 羽绒服/厚棉衣"


def get_sunscreen_suggestion(weather_text):
    if any(i in weather_text for i in ["晴", "多云"]):
        return "☀️ 建议涂抹防晒、戴帽子"
    elif "阴" in weather_text:
        return "☀️ 紫外线较弱"
    else:
        return "☀️ 无需特别防晒"


def get_outdoor_suggestion(weather_text, wind, temp):
    if "雨" in weather_text:
        return "🏃 不建议户外运动"
    elif wind > 10:
        return "🏃 风力较大，建议室内活动"
    elif temp > 35:
        return "🏃 气温过高，易中暑"
    elif temp < 0:
        return "🏃 气温过低，注意保暖"
    else:
        return "🏃 天气适宜，适合户外运动"


def calculate_from_bill(electricity_bill=0, gas_bill=0, water_bill=0, heating_bill=0):
    kwh = electricity_bill / 0.56 if 0.56 > 0 else 0
    gas_m3 = gas_bill / 3.5 if 3.5 > 0 else 0
    heat_kwh = heating_bill / 0.32 if 0.32 > 0 else 0
    carbon_electricity = kwh * 0.58
    carbon_gas = gas_m3 * 2.1
    carbon_heating = heat_kwh * 0.65
    carbon_water = water_bill * 0.15
    total = carbon_electricity + carbon_gas + carbon_heating + carbon_water
    return round(carbon_electricity, 2), round(carbon_gas, 2), round(carbon_water, 2), round(carbon_heating, 2), round(
        total, 2)


def forest_offset(total_carbon):
    return round(total_carbon / 12, 1)


def get_daily_fact():
    facts = [
        "🌲 大兴安岭森林面积约 2500 万公顷，相当于 3 个北京市的面积",
        "❄️ 大兴安岭历史最低温达 -52.3℃",
        "🐅 大兴安岭是东北虎、原麝、紫貂等珍稀动物的栖息地",
        "💧 大兴安岭是嫩江、额尔古纳河的发源地，被称为'东北水塔'",
        "🌍 大兴安岭森林每年吸收的 CO₂ 约 2.5 亿吨"
    ]
    return random.choice(facts)


def link_to_daxinganling(temp, aqi, wind_dir):
    tips = []
    if any(k in wind_dir for k in ["北", "西北", "东北"]):
        tips.append("🍃 风来自大兴安岭方向 → 林区洁净空气正在滋养你所在的城市！")
    else:
        tips.append("💨 风不经过大兴安岭 → 但林区依然守护着东北生态安全")
    return tips


# --------------------------
# 侧边栏
# --------------------------
with st.sidebar:
    st.title("🌍 大兴安岭环境监测系统")
    menu = st.radio("请选择功能", ["大兴安岭气温分析", "实时天气数据"])

# --------------------------
# 主页面
# --------------------------
st.title("📊 大兴安岭环境监测平台")

# ==========================
# 1. 大兴安岭气温分析
# ==========================
if menu == "大兴安岭气温分析":
    set_background(ALIYUN_BG1, is_green=True)
    st.info(f"🌲 **今日·大兴安岭**\n\n{get_daily_fact()}")
    st.divider()

    # ====================== ✅ 真正自动轮播（4秒切换，100%动） ======================
    st.subheader("📷 大兴安岭生态介绍")
    img_js_array = ",".join([f'"{img}"' for img in CAROUSEL_IMGS])

    st.markdown(f"""
    <div style="width:100%; text-align:center;">
        <img id="autoCarousel" src="{CAROUSEL_IMGS[0]}" style="width:100%; border-radius:12px;">
    </div>

    <script>
        const carouselImages = [{img_js_array}];
        let current = 0;
        function changeImg(){{
            current = (current + 1) % carouselImages.length;
            document.getElementById("autoCarousel").src = carouselImages[current];
        }}
        setInterval(changeImg, 4000);
    </script>
    """, unsafe_allow_html=True)

    st.caption("🔄 每4秒自动轮播中")
    st.divider()
    # ==============================================================================

    st.header("🌡 大兴安岭气温数据分析")
    sub_menu = st.selectbox(
        "选择分析类型",
        ["2013-2017年气温统计分析", "分年气温时空变化图", "通量与多变量分析", "🌲 生活缴费碳中和计算（新版）"]
    )


    def show_image(f):
        st.image(ALIYUN_STATIC + f)


    if sub_menu == "2013-2017年气温统计分析":
        st.subheader("📈 2013-2017年大兴安岭气温对比与趋势")
        show_image("2013-2017年大兴安岭气温对比图.png")

    elif sub_menu == "分年气温时空变化图":
        year = st.selectbox("选择年份", [2013, 2014, 2015, 2016, 2017])
        show_image(f"{year}年大兴安岭气温变化图.png")

    elif sub_menu == "通量与多变量分析":
        t1, t2, t3, t4 = st.tabs(["通量数据变化", "变量相关性", "因子载荷矩阵", "主成分分析"])
        with t1:
            show_image("2017年大兴安岭站通量数据变化图.png")
        with t2:
            show_image("correlation_heatmap.png")
        with t3:
            show_image("factor_loadings_heatmap.png")
        with t4:
            show_image("factor_scores_timeseries.png")
            show_image("scree_plot.png")

    elif sub_menu == "🌲 生活缴费碳中和计算（新版）":
        st.subheader("♻️ 生活缴费一键算碳")
        if 'elec_bill' not in st.session_state: st.session_state.elec_bill = 0
        if 'gas_bill' not in st.session_state: st.session_state.gas_bill = 0
        if 'water_bill' not in st.session_state: st.session_state.water_bill = 0
        if 'heat_bill' not in st.session_state: st.session_state.heat_bill = 0

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🏠 单人租房档"):
                st.session_state.elec_bill = 80;
                st.session_state.gas_bill = 30;
                st.session_state.water_bill = 20;
                st.session_state.heat_bill = 0;
                st.rerun()
        with c2:
            if st.button("👨‍👩‍👧 三口家常档"):
                st.session_state.elec_bill = 160;
                st.session_state.gas_bill = 55;
                st.session_state.water_bill = 35;
                st.session_state.heat_bill = 260;
                st.rerun()
        with c3:
            if st.button("🏡 多人大户型档"):
                st.session_state.elec_bill = 260;
                st.session_state.gas_bill = 80;
                st.session_state.water_bill = 50;
                st.session_state.heat_bill = 420;
                st.rerun()

        e = st.number_input("💡 电费", 0, value=st.session_state.elec_bill)
        g = st.number_input("🔥 燃气费", 0, value=st.session_state.gas_bill)
        w = st.number_input("🚰 水费", 0, value=st.session_state.water_bill)
        h = st.number_input("🏠 暖气费", 0, value=st.session_state.heat_bill)
        ce, cg, cw, ch, total = calculate_from_bill(e, g, w, h)
        trees = forest_offset(total)
        st.metric("✅ 月度总碳排放", f"**{total} kg CO₂**")
        if total > 0:
            st.success(f"🌲 需要种植 {trees} 棵落叶松即可碳中和！")

# ==========================
# 2. 实时天气数据
# ==========================
elif menu == "实时天气数据":
    set_background(ALIYUN_BG2, is_green=False)
    st.header("🌤 全球实时天气查询")


    def wgs84_to_gcj02(lng, lat):
        PI = math.pi
        a = 6378245.0
        ee = 0.006693421622965943

        def transformLat(x, y):
            ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
            ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
            return ret

        def transformLng(x, y):
            ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
            ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
            return ret

        dLat = transformLat(lng - 105.0, lat - 35.0)
        dLng = transformLng(lng - 105.0, lat - 35.0)
        radLat = lat / 180.0 * PI
        magic = math.sin(radLat)
        magic = 1 - ee * magic * magic
        sqrtMagic = math.sqrt(magic)
        dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * PI)
        dLng = (dLng * 180.0) / (a / sqrtMagic * math.cos(radLat) * PI)
        return lng + dLng, lat + dLat


    if 'ip_location_done' not in st.session_state:
        st.session_state.ip_location_done = False
    if not st.session_state.ip_location_done:
        location = streamlit_geolocation()
        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat and lon:
            gcj_lon, gcj_lat = wgs84_to_gcj02(lon, lat)
            amap_key = "e73c79c1fdce8187e310ba247a163ae5"
            res = requests.get(
                f"https://restapi.amap.com/v3/geocode/regeo?key={amap_key}&location={gcj_lon},{gcj_lat}&radius=300").json()
            if res["status"] == "1":
                auto_city = res["regeocode"]["addressComponent"]["city"].replace("市", "")
                st.session_state.city = auto_city
        st.session_state.ip_location_done = True

    st.subheader(f"📍当前查询城市：{st.session_state.city}")
    st.divider()

    r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
    with r1c1:
        if st.button("南通"): st.session_state.city = "南通";st.rerun()
    with r1c2:
        if st.button("南京"): st.session_state.city = "南京";st.rerun()
    with r1c3:
        if st.button("苏州"): st.session_state.city = "苏州";st.rerun()
    with r1c4:
        if st.button("无锡"): st.session_state.city = "无锡";st.rerun()
    with r1c5:
        if st.button("泰州"): st.session_state.city = "泰州";st.rerun()

    input_city = st.text_input("✍手动输入城市")
    if input_city.strip() != "":
        st.session_state.city = input_city.strip()
        st.rerun()

    with st.spinner(f"获取 {st.session_state.city} 天气..."):
        wc = seniverse_now(st.session_state.city)
        daily = seniverse_daily(st.session_state.city, 3)
        aqi_data = seniverse_aqi(st.session_state.city)

    if wc:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏙 城市", wc["name"])
        col2.metric("🌤 天气", wc["text"])
        col3.metric("🌡 温度", f"{wc['temp']}℃")
        col4.metric("💧 湿度", f"{wc['humidity']}%")

        aqi_num = aqi_data["aqi"] if aqi_data else 70
        st.subheader("🌫 空气质量 AQI")
        if aqi_data:
            ca1, ca2, ca3 = st.columns(3)
            ca1.metric("AQI", aqi_data["aqi"])
            ca2.metric("等级", aqi_data["quality"])
            ca3.metric("PM2.5", aqi_data["pm25"])

        st.subheader("📅 未来3天预报")
        if daily:
            cols = st.columns(3)
            for i, d in enumerate(daily):
                with cols[i]:
                    st.markdown(f"""
                    <div style='text-align:center; padding:10px; background:#f6f6f6; border-radius:12px;'>
                    {d['date'][-5:]}<br>
                    <span style='font-size:30px'>{get_weather_icon(d['text_day'])}</span><br>
                    {d['text_day']}<br>
                    {d['low']}~{d['high']}℃
                    </div>
                    """, unsafe_allow_html=True)

        st.subheader("🌲 大兴安岭生态联动")
        for t in link_to_daxinganling(wc["temp"], aqi_num, wc["wind_dir"]):
            st.success(t)