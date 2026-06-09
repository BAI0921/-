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
import hashlib
import hmac
import base64

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

# ==================== 心知天气 V4 配置 ====================
# 🔑 请在这里填入你的公钥和私钥（从心知天气控制台获取）
SENIVERSE_PUBLIC_KEY = "PUof6N-OT07myjnhE"  # 例如: PKwiV7auWJE3iBJ8d
SENIVERSE_PRIVATE_KEY = "SyBQ06H2yR2RIEJn3"  # 例如: SMEieQjde1C9eXnbE
# ========================================================

V4_BASE_URL = "https://api.seniverse.com/v4/"


def generate_v4_sig(params, private_key):
    """生成心知天气 V4 接口签名"""
    sorted_keys = sorted(params.keys())
    string_to_sign = "&".join([f"{k}={params[k]}" for k in sorted_keys])
    signature_bytes = hmac.new(
        private_key.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha1
    ).digest()
    sig_base64 = base64.b64encode(signature_bytes).decode('utf-8')
    return quote(sig_base64, safe='')


def seniverse_v4_request(fields, location, start_time=None, hours=None):
    """
    通用 V4 接口请求函数
    fields: 请求的数据类型，如 "weather_now", "weather_daily_3d", "weather_hourly_1h", "air_now"
    location: 城市名或经纬度（经纬度格式 "纬度:经度"）
    """
    # 构建请求参数
    params = {
        "public_key": SENIVERSE_PUBLIC_KEY,
        "ts": int(time.time()),
        "ttl": 300,
        "locations": location,
        "fields": fields
    }

    # 添加可选参数
    if start_time:
        params["start_time"] = start_time
    if hours:
        params["hours"] = hours

    # 生成签名
    sig = generate_v4_sig(params, SENIVERSE_PRIVATE_KEY)
    params["sig"] = sig

    try:
        r = requests.get(V4_BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("results") and len(data["results"]) > 0:
            return data["results"][0]
    except Exception as e:
        st.error(f"V4接口请求失败: {e}")
        return None
    return None


def seniverse_v4_now(city):
    """获取实时天气（V4版本）"""
    result = seniverse_v4_request("weather_now", city)
    if result and result.get("now"):
        now = result["now"]
        loc = result["location"]
        return {
            "name": loc.get("name", city),
            "text": now.get("text", ""),
            "temp": float(now.get("temperature", 0)),
            "humidity": int(now.get("humidity", 0)),
            "wind_speed": float(now.get("wind_speed", 0)),
            "wind_dir": now.get("wind_direction", "北风")
        }
    return None


def seniverse_v4_daily(city, days=3):
    """获取逐日天气预报（V4版本）"""
    fields_map = {3: "weather_daily_3d", 7: "weather_daily_7d", 15: "weather_daily_15d"}
    fields = fields_map.get(days, "weather_daily_3d")
    result = seniverse_v4_request(fields, city)
    if result and result.get("daily"):
        return result["daily"]
    return None


def seniverse_v4_hourly(city, hours=24):
    """获取逐小时天气预报（V4版本，未来24-48小时）"""
    result = seniverse_v4_request("weather_hourly_1h", city, hours=min(hours, 48))
    if result and result.get("hourly"):
        return result["hourly"]
    return None


def seniverse_v4_aqi(city):
    """获取空气质量（V4版本）"""
    result = seniverse_v4_request("air_now", city)
    if result and result.get("air"):
        air = result["air"]
        city_air = air.get("city", air)
        return {
            "aqi": int(city_air.get("aqi", 0)),
            "quality": city_air.get("quality", ""),
            "pm25": int(city_air.get("pm25", 0)),
            "pm10": int(city_air.get("pm10", 0))
        }
    return None


# 为了兼容老代码，保留原函数名（使用V4实现）
def seniverse_now(city):
    return seniverse_v4_now(city)


def seniverse_daily(city, days=3):
    return seniverse_v4_daily(city, days)


def seniverse_aqi(city):
    return seniverse_v4_aqi(city)


def seniverse_hourly(city, hours=24):
    return seniverse_v4_hourly(city, hours)


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
    menu = st.radio("请选择功能", ["大兴安岭气温分析", "实时天气数据"])

# 主标题
st.title("📊 大兴安岭环境监测平台")

# 大兴安岭气温分析页面
if menu == "大兴安岭气温分析":
    set_background(ALIYUN_BG1, is_green=True)
    st.info(f"🌲 **今日·大兴安岭**\n\n{get_daily_fact()}")
    st.divider()

    st.subheader("📷 大兴安岭生态介绍")

    # 使用 streamlit-autorefresh 实现自动轮播（每4秒刷新一次）
    refresh_count = st_autorefresh(interval=4000, key="carousel_autorefresh", limit=None, debounce=True)

    # 用 refresh_count 驱动轮播索引（每次刷新自动切换到下一张）
    st.session_state.carousel_idx = refresh_count % len(CAROUSEL_IMGS)
    current_idx = st.session_state.carousel_idx

    # 显示当前图片和切换按钮
    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        st.image(CAROUSEL_IMGS[current_idx], use_container_width=True,
                 caption=f"📸 大兴安岭生态风光 ({current_idx + 1}/{len(CAROUSEL_IMGS)})")

        # 手动切换按钮
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

    # 数据分析模块
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

        e = st.number_input("💡 电费", 0, value=st.session_state.elec_bill)
        g = st.number_input("🔥 燃气费", 0, value=st.session_state.gas_bill)
        w = st.number_input("🚰 水费", 0, value=st.session_state.water_bill)
        h = st.number_input("🏠 暖气费", 0, value=st.session_state.heat_bill)
        ce, cg, cw, ch, total = calculate_from_bill(e, g, w, h)
        trees = forest_offset(total)
        st.metric("✅ 月度总碳排放", f"**{total} kg CO₂**")
        if total > 0:
            st.success(f"🌲 需要种植 {trees} 棵落叶松即可碳中和！")

# 实时天气页面
elif menu == "实时天气数据":
    set_background(ALIYUN_BG2, is_green=False)
    st.header("🌤 全球实时天气查询（心知天气V4高精度版）")


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
        if st.button("南通"): st.session_state.city = "南通"; st.rerun()
    with r1c2:
        if st.button("南京"): st.session_state.city = "南京"; st.rerun()
    with r1c3:
        if st.button("苏州"): st.session_state.city = "苏州"; st.rerun()
    with r1c4:
        if st.button("无锡"): st.session_state.city = "无锡"; st.rerun()
    with r1c5:
        if st.button("泰州"): st.session_state.city = "泰州"; st.rerun()

    input_city = st.text_input("✍手动输入城市")
    if input_city.strip() != "":
        st.session_state.city = input_city.strip()
        st.rerun()

    with st.spinner(f"获取 {st.session_state.city} 天气..."):
        wc = seniverse_now(st.session_state.city)
        daily = seniverse_daily(st.session_state.city, 3)
        aqi_data = seniverse_aqi(st.session_state.city)
        hourly_data = seniverse_hourly(st.session_state.city, 24)

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

        # 新增：逐小时天气预报（V4专属功能）
        if hourly_data:
            st.subheader("⏰ 未来24小时逐小时预报")

            # 让用户选择显示多少小时
            hours_to_show = st.slider("显示未来多少小时", 6, 24, 12)

            # 提取数据
            hour_data = hourly_data[:hours_to_show]
            hours = [h['time'][11:16] for h in hour_data]  # 提取 HH:MM
            temps = [int(h['temperature']) for h in hour_data]
            weather_texts = [h['text'] for h in hour_data]

            # 绘制温度变化曲线
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(hours, temps, marker='o', linewidth=2, color='#FF6B6B')
            ax.fill_between(hours, temps, alpha=0.2, color='#FF6B6B')
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('温度 (℃)', fontsize=12)
            ax.set_title(f'{st.session_state.city} 未来{hours_to_show}小时温度变化趋势', fontsize=14)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            st.pyplot(fig)

            # 显示表格形式（折叠）
            with st.expander("📋 查看详细逐小时数据表格"):
                hourly_df = pd.DataFrame({
                    "时间": hours,
                    "天气": weather_texts,
                    "温度(℃)": temps
                })
                st.dataframe(hourly_df, use_container_width=True)

        st.subheader("🌲 大兴安岭生态联动")
        for t in link_to_daxinganling(wc["temp"], aqi_num, wc["wind_dir"]):
            st.success(t)