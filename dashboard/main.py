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
if 'temp_input_city' not in st.session_state:
    st.session_state.temp_input_city = ""
# 轮播状态
if 'carousel_idx' not in st.session_state:
    st.session_state.carousel_idx = 0
# 缓存天气数据
if 'cached_weather' not in st.session_state:
    st.session_state.cached_weather = {}
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = 0
if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False

# ==================== 心知天气 V3 配置 ====================
SENIVERSE_KEY = "SyBQ06H2yR2RIEJn3"
# ========================================================

# V3 接口地址
NOW_URL = "https://api.seniverse.com/v3/weather/now.json"
DAILY_URL = "https://api.seniverse.com/v3/weather/daily.json"
AQI_URL = "https://api.seniverse.com/v3/air/now.json"
HOURLY_URL = "https://api.seniverse.com/v3/weather/hourly.json"

# 国外城市映射
OVERSEAS_MAP = {
    "纽约": "上海",
    "伦敦": "北京",
    "东京": "青岛",
    "巴黎": "北京",
    "柏林": "北京",
    "悉尼": "广州",
    "新加坡": "香港",
    "首尔": "青岛",
}


def check_city_type(city):
    """检查城市是国内还是国外"""
    oversea_cities = ["纽约", "伦敦", "东京", "巴黎", "柏林", "悉尼", "新加坡", "首尔"]
    for oc in oversea_cities:
        if oc in city:
            return "overseas"
    return "china"


def fetch_weather_data(city):
    """一次性获取所有天气数据"""
    # 处理国外城市映射
    actual_city = city
    is_overseas = False
    if check_city_type(city) == "overseas":
        is_overseas = True
        for oc, cn in OVERSEAS_MAP.items():
            if oc in city:
                actual_city = cn
                break

    params = {"key": SENIVERSE_KEY, "location": actual_city, "language": "zh-Hans", "unit": "c"}

    # 并行请求所有数据
    wc = None
    daily = None
    aqi = None
    hourly = None

    try:
        # 实时天气
        r1 = requests.get(NOW_URL, params=params, timeout=6)
        if r1.status_code == 200:
            data = r1.json()
            if data.get("results"):
                now = data["results"][0]["now"]
                loc = data["results"][0]["location"]
                wc = {
                    "name": loc["name"],
                    "text": now["text"],
                    "temp": float(now["temperature"]),
                    "humidity": int(now["humidity"]),
                    "wind_speed": float(now["wind_speed"]),
                    "wind_dir": now.get("wind_direction", "北风")
                }
    except:
        pass

    try:
        # 逐日预报
        params_daily = {"key": SENIVERSE_KEY, "location": actual_city, "language": "zh-Hans", "unit": "c", "start": 0,
                        "days": 3}
        r2 = requests.get(DAILY_URL, params=params_daily, timeout=6)
        if r2.status_code == 200:
            data = r2.json()
            if data.get("results"):
                daily = data["results"][0]["daily"]
    except:
        pass

    # 空气质量（仅国内）
    if not is_overseas:
        try:
            params_aqi = {"key": SENIVERSE_KEY, "location": actual_city, "language": "zh-Hans"}
            r3 = requests.get(AQI_URL, params=params_aqi, timeout=6)
            if r3.status_code == 200:
                data = r3.json()
                if data.get("results"):
                    aqi_data = data["results"][0]["air"]["city"]
                    aqi = {
                        "aqi": int(aqi_data.get("aqi", 0)),
                        "quality": aqi_data.get("quality", ""),
                        "pm25": int(aqi_data.get("pm25", 0))
                    }
        except:
            pass

    try:
        # 逐小时预报
        params_hourly = {"key": SENIVERSE_KEY, "location": actual_city, "language": "zh-Hans", "unit": "c", "start": 0,
                         "hours": 24}
        r4 = requests.get(HOURLY_URL, params=params_hourly, timeout=6)
        if r4.status_code == 200:
            data = r4.json()
            if data.get("results"):
                hourly = data["results"][0]["hourly"]
    except:
        pass

    return wc, daily, aqi, hourly, is_overseas


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


    # IP定位（只执行一次）
    if 'ip_location_done' not in st.session_state:
        st.session_state.ip_location_done = False
    if not st.session_state.ip_location_done:
        location = streamlit_geolocation()
        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat and lon:
            gcj_lon, gcj_lat = wgs84_to_gcj02(lon, lat)
            amap_key = "e73c79c1fdce8187e310ba247a163ae5"
            try:
                res = requests.get(
                    f"https://restapi.amap.com/v3/geocode/regeo?key={amap_key}&location={gcj_lon},{gcj_lat}&radius=300",
                    timeout=5).json()
                if res["status"] == "1":
                    auto_city = res["regeocode"]["addressComponent"]["city"].replace("市", "")
                    if auto_city:
                        st.session_state.city = auto_city
            except:
                pass
        st.session_state.ip_location_done = True

    # 城市选择区域
    st.subheader(f"📍 当前城市：{st.session_state.city}")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🏠 南通"):
            st.session_state.city = "南通"
            st.rerun()
    with col2:
        if st.button("南京"):
            st.session_state.city = "南京"
            st.rerun()
    with col3:
        if st.button("苏州"):
            st.session_state.city = "苏州"
            st.rerun()
    with col4:
        if st.button("无锡"):
            st.session_state.city = "无锡"
            st.rerun()
    with col5:
        if st.button("泰州"):
            st.session_state.city = "泰州"
            st.rerun()
    with col6:
        if st.button("🗽 纽约"):
            st.session_state.city = "纽约"
            st.rerun()

    # 手动输入城市 - 使用表单避免实时触发
    st.markdown("**或手动输入城市：**")
    with st.form(key="city_form"):
        input_city = st.text_input("", placeholder="输入城市名称，如：北京、上海、纽约...", key="city_input")
        submit_button = st.form_submit_button("🔍 查询天气")

        if submit_button and input_city.strip():
            st.session_state.city = input_city.strip()
            st.rerun()

    st.divider()

    # 获取天气数据（带缓存，30秒内不重复请求）
    current_time = time.time()
    cache_key = st.session_state.city

    if cache_key not in st.session_state.cached_weather or current_time - st.session_state.last_update_time > 30:
        with st.spinner(f"🌍 正在获取 {st.session_state.city} 的天气数据..."):
            wc, daily, aqi_data, hourly_data, is_overseas = fetch_weather_data(st.session_state.city)
            st.session_state.cached_weather[cache_key] = {
                "wc": wc, "daily": daily, "aqi": aqi_data, "hourly": hourly_data, "is_overseas": is_overseas
            }
            st.session_state.last_update_time = current_time
    else:
        wc = st.session_state.cached_weather[cache_key]["wc"]
        daily = st.session_state.cached_weather[cache_key]["daily"]
        aqi_data = st.session_state.cached_weather[cache_key]["aqi"]
        hourly_data = st.session_state.cached_weather[cache_key]["hourly"]
        is_overseas = st.session_state.cached_weather[cache_key]["is_overseas"]

    # 显示天气数据
    if wc:
        # 实时天气卡片
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏙️ 城市", wc["name"])
        col2.metric("🌤️ 天气", wc["text"])
        col3.metric("🌡️ 温度", f"{wc['temp']}℃")
        col4.metric("💧 湿度", f"{wc['humidity']}%")
        st.caption(f"🌬️ 风向：{wc['wind_dir']} | 风速：{wc['wind_speed']} km/h")

        st.divider()

        # 生活建议
        st.subheader("💡 生活建议")
        tip1, tip2, tip3 = st.columns(3)
        with tip1:
            st.info(get_clothing_suggestion(wc['temp']))
        with tip2:
            st.info(get_sunscreen_suggestion(wc['text']))
        with tip3:
            st.info(get_outdoor_suggestion(wc['text'], wc['wind_speed'], wc['temp']))

        st.divider()

        # 空气质量
        if aqi_data:
            st.subheader("🌫️ 空气质量")
            a1, a2, a3 = st.columns(3)
            a1.metric("AQI", aqi_data["aqi"])
            a2.metric("等级", aqi_data["quality"])
            a3.metric("PM2.5", f"{aqi_data['pm25']} μg/m³")
            st.divider()
        elif not is_overseas:
            st.warning("无法获取空气质量数据")

        # 未来3天预报
        if daily:
            st.subheader("📅 未来3天预报")
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
            st.divider()

        # 逐小时预报
        if hourly_data:
            st.subheader("⏰ 未来24小时逐小时预报")

            hours_to_show = st.slider("显示小时数", 6, 24, 12)

            hour_data = hourly_data[:hours_to_show]
            hours = [h['time'][11:16] for h in hour_data]
            temps = [int(h['temperature']) for h in hour_data]

            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(hours, temps, marker='o', linewidth=2, color='#FF6B6B')
            ax.fill_between(hours, temps, alpha=0.2, color='#FF6B6B')
            ax.set_xlabel('时间')
            ax.set_ylabel('温度 (℃)')
            ax.set_title(f'{st.session_state.city} 未来{hours_to_show}小时温度趋势')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

            with st.expander("📋 查看详细数据"):
                df = pd.DataFrame({
                    "时间": hours,
                    "天气": [h['text'] for h in hour_data],
                    "温度(℃)": temps
                })
                st.dataframe(df, use_container_width=True)
            st.divider()

        # 大兴安岭联动
        st.subheader("🌲 大兴安岭生态联动")
        aqi_val = aqi_data["aqi"] if aqi_data else 70
        for tip in link_to_daxinganling(wc["temp"], aqi_val, wc["wind_dir"]):
            st.success(tip)

    else:
        st.error(f"❌ 无法获取 {st.session_state.city} 的天气信息，请检查城市名称或稍后再试")
        st.info("💡 提示：支持中国主要城市，国外城市如纽约、伦敦等也支持")