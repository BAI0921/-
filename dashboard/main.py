import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler
from streamlit_geolocation import streamlit_geolocation
from streamlit_autorefresh import st_autorefresh
import warnings
import requests
import random
import time
from urllib.parse import quote
import math

warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 图片地址配置
ALIYUN_BG1 = "https://bairuobing.oss-cn-hangzhou.aliyuncs.com/static/daxinganling_bg.png"
ALIYUN_BG2 = "https://bairuobing.oss-cn-hangzhou.aliyuncs.com/static/weather_bg.png"
ALIYUN_STATIC = "https://bairuobing.oss-cn-hangzhou.aliyuncs.com/static/"

CAROUSEL_IMGS = [
    ALIYUN_STATIC + "img1.png",
    ALIYUN_STATIC + "img2.png",
    ALIYUN_STATIC + "img3.png"
]

# 节能小贴士
ENERGY_TIPS = [
    "💡 空调调高1℃，每年可减少碳排放约20kg",
    "🔌 电器不用时拔掉插头，待机状态也耗电",
    "🚰 洗澡水收集起来冲厕所，节水又减碳",
    "🚶 短距离出行选择步行或骑行，零碳排放",
    "♻️ 购物自带布袋，减少塑料袋使用",
    "🥩 每周一天素食，一年可减碳约100kg",
    "🌿 使用节能灯泡，比普通灯泡省电75%",
    "📦 快递纸箱重复利用，减少树木砍伐"
]


# 背景样式函数
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


# 全局状态初始化
if 'agreed_carbon' not in st.session_state:
    st.session_state.agreed_carbon = False
if 'weather_history' not in st.session_state:
    st.session_state.weather_history = []
if 'city' not in st.session_state:
    st.session_state.city = "南通"
if 'carousel_idx' not in st.session_state:
    st.session_state.carousel_idx = 0
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = 0
if 'show_daily' not in st.session_state:
    st.session_state.show_daily = False
if 'show_hourly' not in st.session_state:
    st.session_state.show_hourly = False
if 'show_aqi' not in st.session_state:
    st.session_state.show_aqi = False

# ==================== 心知天气 V3 配置 ====================
SENIVERSE_KEY = "SyBQ06H2yR2RIEJn3"
# ========================================================

NOW_URL = "https://api.seniverse.com/v3/weather/now.json"
DAILY_URL = "https://api.seniverse.com/v3/weather/daily.json"
AQI_URL = "https://api.seniverse.com/v3/air/now.json"
HOURLY_URL = "https://api.seniverse.com/v3/weather/hourly.json"


def get_weather_now(city):
    """只获取实时天气"""
    params = {"key": SENIVERSE_KEY, "location": city, "language": "zh-Hans", "unit": "c"}
    try:
        r = requests.get(NOW_URL, params=params, timeout=8)
        data = r.json()
        if data.get("results"):
            now = data["results"][0]["now"]
            loc = data["results"][0]["location"]
            return {
                "name": loc["name"],
                "text": now["text"],
                "temp": float(now["temperature"]),
                "humidity": int(now["humidity"]),
                "wind_speed": float(now["wind_speed"]),
                "wind_dir": now.get("wind_direction", "北风")
            }
    except Exception as e:
        st.error(f"请求失败: {e}")
        return None
    return None


def get_weather_daily(city):
    """获取3天预报（按需加载）"""
    params = {"key": SENIVERSE_KEY, "location": city, "language": "zh-Hans", "unit": "c", "start": 0, "days": 3}
    try:
        r = requests.get(DAILY_URL, params=params, timeout=8)
        data = r.json()
        if data.get("results"):
            return data["results"][0]["daily"]
    except:
        return None
    return None


def get_weather_aqi(city):
    """获取空气质量（按需加载）"""
    params = {"key": SENIVERSE_KEY, "location": city, "language": "zh-Hans"}
    try:
        r = requests.get(AQI_URL, params=params, timeout=8)
        data = r.json()
        if data.get("results"):
            aqi = data["results"][0]["air"]["city"]
            return {
                "aqi": int(aqi.get("aqi", 0)),
                "quality": aqi.get("quality", ""),
                "pm25": int(aqi.get("pm25", 0))
            }
    except:
        return None
    return None


def get_weather_hourly(city):
    """获取逐小时预报（按需加载）"""
    params = {"key": SENIVERSE_KEY, "location": city, "language": "zh-Hans", "unit": "c", "start": 0, "hours": 24}
    try:
        r = requests.get(HOURLY_URL, params=params, timeout=8)
        data = r.json()
        if data.get("results"):
            return data["results"][0]["hourly"]
    except:
        return None
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


# 侧边栏菜单
with st.sidebar:
    st.title("🌍 大兴安岭环境监测系统")
    menu = st.radio("请选择功能", ["大兴安岭气温分析", "实时天气数据", "🌲 碳足迹碳中和计算"])

# 主标题
st.title("📊 大兴安岭环境监测平台")

# 大兴安岭气温分析页面
if menu == "大兴安岭气温分析":
    set_background(ALIYUN_BG1, is_green=True)
    st.info(f"🌲 **今日·大兴安岭**\n\n{get_daily_fact()}")

    with st.expander("💚 节能小贴士"):
        tip = random.choice(ENERGY_TIPS)
        st.info(tip)

    st.divider()
    st.subheader("📷 大兴安岭生态介绍")

    refresh_count = st_autorefresh(interval=4000, key="carousel_autorefresh", limit=None, debounce=True)
    st.session_state.carousel_idx = refresh_count % len(CAROUSEL_IMGS)
    current_idx = st.session_state.carousel_idx

    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        st.image(CAROUSEL_IMGS[current_idx], use_container_width=True,
                 caption=f"📸 大兴安岭生态风光 ({current_idx + 1}/{len(CAROUSEL_IMGS)})")
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
        with btn_col1:
            if st.button("◀ 上一张", use_container_width=True):
                st.session_state.carousel_idx = (current_idx - 1) % len(CAROUSEL_IMGS)
                st.rerun()
        with btn_col2:
            if st.button("▶ 下一张", use_container_width=True):
                st.session_state.carousel_idx = (current_idx + 1) % len(CAROUSEL_IMGS)
                st.rerun()
    st.caption("🔄 每4秒自动切换图片")
    st.divider()

    st.header("🌡 大兴安岭气温数据分析")
    sub_menu = st.selectbox(
        "选择分析类型",
        ["2013-2017年气温统计分析", "分年气温时空变化图", "通量与多变量分析"]
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

# 碳足迹碳中和计算页面
elif menu == "🌲 碳足迹碳中和计算":
    set_background(ALIYUN_BG1, is_green=True)
    st.header("♻️ 生活缴费一键算碳")

    with st.expander("💚 节能小贴士", expanded=True):
        for tip in ENERGY_TIPS[:4]:
            st.write(tip)
    st.divider()

    if 'elec_bill' not in st.session_state: st.session_state.elec_bill = 0
    if 'gas_bill' not in st.session_state: st.session_state.gas_bill = 0
    if 'water_bill' not in st.session_state: st.session_state.water_bill = 0
    if 'heat_bill' not in st.session_state: st.session_state.heat_bill = 0

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🏠 单人租房档"):
            st.session_state.elec_bill = 80
            st.session_state.gas_bill = 30
            st.session_state.water_bill = 20
            st.session_state.heat_bill = 0
            st.rerun()
    with c2:
        if st.button("👨‍👩‍👧 三口家常档"):
            st.session_state.elec_bill = 160
            st.session_state.gas_bill = 55
            st.session_state.water_bill = 35
            st.session_state.heat_bill = 260
            st.rerun()
    with c3:
        if st.button("🏡 多人大户型档"):
            st.session_state.elec_bill = 260
            st.session_state.gas_bill = 80
            st.session_state.water_bill = 50
            st.session_state.heat_bill = 420
            st.rerun()

    e = st.number_input("💡 电费 (元)", 0, value=st.session_state.elec_bill)
    g = st.number_input("🔥 燃气费 (元)", 0, value=st.session_state.gas_bill)
    w = st.number_input("🚰 水费 (元)", 0, value=st.session_state.water_bill)
    h = st.number_input("🏠 暖气费 (元)", 0, value=st.session_state.heat_bill)

    ce, cg, cw, ch, total = calculate_from_bill(e, g, w, h)
    trees = forest_offset(total)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ 月度总碳排放", f"**{total} kg CO₂**")
    with col2:
        if total > 0:
            st.metric("🌲 需要种植树木", f"{trees} 棵落叶松")

    if total > 0:
        st.success(f"🌲 种植 {trees} 棵落叶松即可碳中和！")
        if total > 500:
            st.warning("💡 您的碳排放较高，建议：减少空调使用、选择节能家电、多用公共交通")

# 实时天气页面
elif menu == "实时天气数据":
    set_background(ALIYUN_BG2, is_green=False)
    st.header("🌤 实时天气查询（节能版）")

    # 城市选择
    st.subheader(f"📍 当前城市：{st.session_state.city}")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("南通"):
            st.session_state.city = "南通"
            st.session_state.weather_data = None
            st.session_state.show_daily = False
            st.session_state.show_hourly = False
            st.session_state.show_aqi = False
            st.rerun()
    with col2:
        if st.button("南京"):
            st.session_state.city = "南京"
            st.session_state.weather_data = None
            st.session_state.show_daily = False
            st.session_state.show_hourly = False
            st.session_state.show_aqi = False
            st.rerun()
    with col3:
        if st.button("苏州"):
            st.session_state.city = "苏州"
            st.session_state.weather_data = None
            st.session_state.show_daily = False
            st.session_state.show_hourly = False
            st.session_state.show_aqi = False
            st.rerun()
    with col4:
        if st.button("无锡"):
            st.session_state.city = "无锡"
            st.session_state.weather_data = None
            st.session_state.show_daily = False
            st.session_state.show_hourly = False
            st.session_state.show_aqi = False
            st.rerun()
    with col5:
        if st.button("泰州"):
            st.session_state.city = "泰州"
            st.session_state.weather_data = None
            st.session_state.show_daily = False
            st.session_state.show_hourly = False
            st.session_state.show_aqi = False
            st.rerun()
    with col6:
        if st.button("北京"):
            st.session_state.city = "北京"
            st.session_state.weather_data = None
            st.session_state.show_daily = False
            st.session_state.show_hourly = False
            st.session_state.show_aqi = False
            st.rerun()

    # 手动输入
    with st.form(key="city_form"):
        input_city = st.text_input("输入城市名称", placeholder="北京、上海、广州...")
        submit = st.form_submit_button("查询天气")
        if submit and input_city.strip():
            st.session_state.city = input_city.strip()
            st.session_state.weather_data = None
            st.session_state.show_daily = False
            st.session_state.show_hourly = False
            st.session_state.show_aqi = False
            st.rerun()

    st.divider()

    # 只获取实时天气（每次只发1个请求）
    current_time = time.time()

    # 限制请求频率：至少间隔2秒
    if st.session_state.weather_data is None or current_time - st.session_state.last_request_time > 10:
        with st.spinner(f"获取 {st.session_state.city} 天气..."):
            weather = get_weather_now(st.session_state.city)
            if weather:
                st.session_state.weather_data = weather
                st.session_state.last_request_time = current_time
            else:
                st.error(f"无法获取 {st.session_state.city} 的天气信息")

    # 显示实时天气
    if st.session_state.weather_data:
        w = st.session_state.weather_data
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏙️ 城市", w["name"])
        col2.metric("🌤️ 天气", w["text"])
        col3.metric("🌡️ 温度", f"{w['temp']}℃")
        col4.metric("💧 湿度", f"{w['humidity']}%")
        st.caption(f"🌬️ 风向：{w['wind_dir']} | 风速：{w['wind_speed']} km/h")

        st.divider()

        # 生活建议
        st.subheader("💡 生活建议")
        tip1, tip2, tip3 = st.columns(3)
        with tip1:
            st.info(get_clothing_suggestion(w['temp']))
        with tip2:
            st.info(get_sunscreen_suggestion(w['text']))
        with tip3:
            st.info(get_outdoor_suggestion(w['text'], w['wind_speed'], w['temp']))

        st.divider()

        # ========== 按需加载的模块 ==========
        st.subheader("📊 更多天气数据（点击加载）")

        # 空气质量按钮
        if not st.session_state.show_aqi:
            if st.button("🌫️ 加载空气质量"):
                st.session_state.show_aqi = True
                st.rerun()
        else:
            with st.spinner("加载空气质量..."):
                aqi = get_weather_aqi(st.session_state.city)
                if aqi:
                    a1, a2, a3 = st.columns(3)
                    a1.metric("AQI", aqi["aqi"])
                    a2.metric("等级", aqi["quality"])
                    a3.metric("PM2.5", f"{aqi['pm25']} μg/m³")
                else:
                    st.info("该城市暂不支持空气质量数据")

        # 3天预报按钮
        if not st.session_state.show_daily:
            if st.button("📅 加载3天预报"):
                st.session_state.show_daily = True
                st.rerun()
        else:
            with st.spinner("加载3天预报..."):
                daily = get_weather_daily(st.session_state.city)
                if daily:
                    cols = st.columns(3)
                    for i, d in enumerate(daily[:3]):
                        with cols[i]:
                            st.markdown(f"""
                            <div style='text-align:center; padding:10px; background:#f0f2f6; border-radius:12px;'>
                            <b>{d['date'][5:]}</b><br>
                            <span style='font-size:32px'>{get_weather_icon(d['text_day'])}</span><br>
                            {d['text_day']}<br>
                            🌡️ {d['low']}°C ~ {d['high']}°C
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("无法获取预报数据")

        # 逐小时预报按钮
        if not st.session_state.show_hourly:
            if st.button("⏰ 加载24小时预报"):
                st.session_state.show_hourly = True
                st.rerun()
        else:
            with st.spinner("加载逐小时预报..."):
                hourly = get_weather_hourly(st.session_state.city)
                if hourly:
                    hours_to_show = st.slider("显示小时数", 6, 24, 12)
                    hour_data = hourly[:hours_to_show]
                    hours = [h['time'][11:16] for h in hour_data]
                    temps = [int(h['temperature']) for h in hour_data]

                    fig, ax = plt.subplots(figsize=(12, 4))
                    ax.plot(hours, temps, marker='o', linewidth=2, color='#FF6B6B')
                    ax.fill_between(hours, temps, alpha=0.2, color='#FF6B6B')
                    ax.set_xlabel('时间')
                    ax.set_ylabel('温度 (℃)')
                    ax.set_title(f'{st.session_state.city} 温度趋势')
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)
                else:
                    st.info("无法获取逐小时数据")

        st.divider()

        # 大兴安岭联动
        st.subheader("🌲 大兴安岭生态联动")
        for tip in link_to_daxinganling(w['temp'], 70, w['wind_dir']):
            st.success(tip)