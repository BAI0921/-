import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler
from streamlit_geolocation import streamlit_geolocation
import warnings
import requests
import base64
import random
from datetime import datetime
import io
import re
from PIL import Image
from aip import AipOcr

warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ====================== 阿里云图片链接 ======================
ALIYUN_BG1 = "https://bairuobing.oss-cn-hangzhou.aliyuncs.com/static/static/daxinganling_bg.png"
ALIYUN_BG2 = "https://bairuobing.oss-cn-hangzhou.aliyuncs.com/static/static/weather_bg.png"
ALIYUN_STATIC = "https://bairuobing.oss-cn-hangzhou.aliyuncs.com/static/static/"

from urllib.parse import quote

# ---------------------- 百度OCR配置（直接用） ----------------------
APP_ID = '25847663'
API_KEY = 'yU3N9u9X7QjRb8fKv5D4s1G2'
SECRET_KEY = 'aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4yZ5'
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)


def set_background(img_url):
    safe_url = quote(img_url, safe=':/')
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("{safe_url}");
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
        min-height:100vh !important;
    }}
    [data-testid="stHeader"]{{
        background:transparent !important;
    }}
    .block-container {{
        background-color: rgba(0,0,0,0.05) !important;
    }}
    </style>
    """, unsafe_allow_html=True)


# ========== 初始化 session_state ==========
if 'agreed_carbon' not in st.session_state:
    st.session_state.agreed_carbon = False
if 'weather_history' not in st.session_state:
    st.session_state.weather_history = []
if 'city' not in st.session_state:
    st.session_state.city = "南通"
if 'elec_bill' not in st.session_state:
    st.session_state.elec_bill = 0
if 'gas_bill' not in st.session_state:
    st.session_state.gas_bill = 0
if 'water_bill' not in st.session_state:
    st.session_state.water_bill = 0
if 'heat_bill' not in st.session_state:
    st.session_state.heat_bill = 0

# ---------------------- 心知天气配置 ----------------------
SENIVERSE_KEY = "SyBQ06H2yR2RIEJn3"
NOW_URL = "https://api.seniverse.com/v3/weather/now.json"
DAILY_URL = "https://api.seniverse.com/v3/weather/daily.json"
AQI_URL = "https://api.seniverse.com/v3/air/now.json"


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
                "wind": float(now["wind_speed"]),
                "wind_dir": now.get("wind_direction", "北风")
            }
    except Exception as e:
        st.error(f"请求失败：{e}")
    return None


def seniverse_daily(city, days=3):
    params = {
        "key": SENIVERSE_KEY,
        "location": city,
        "language": "zh-Hans",
        "unit": "c",
        "start": 0,
        "days": days
    }
    try:
        r = requests.get(DAILY_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("results"):
            return data["results"][0]["daily"]
    except:
        return None


def seniverse_aqi(city):
    params = {
        "key": SENIVERSE_KEY,
        "location": city,
        "language": "zh-Hans"
    }
    try:
        r = requests.get(AQI_URL, params=params, timeout=10)
        r.raise_for_status()
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


def get_weather_icon(text):
    icon_map = {
        "晴": "☀️", "多云": "⛅", "阴": "☁️", "小雨": "🌧️", "中雨": "🌧️",
        "大雨": "🌧️", "雷阵雨": "⛈️", "雪": "❄️", "小雪": "❄️", "中雪": "❄️", "大雪": "❄️"
    }
    for k in icon_map:
        if k in text:
            return icon_map[k]
    return "🌤️"


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
    if any(i in weather_text for i in ["晴", "多云"]):
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


def calculate_from_bill(electricity_bill=0, gas_bill=0, water_bill=0, heating_bill=0):
    price_electric = 0.56
    price_gas = 3.5
    price_heat = 0.32
    kwh = electricity_bill / price_electric if price_electric > 0 else 0
    gas_m3 = gas_bill / price_gas if price_gas > 0 else 0
    heat_kwh = heating_bill / price_heat if price_heat > 0 else 0
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
        "❄️ 大兴安岭历史最低温达 -52.3℃（1969年），是中国的'寒极'之一",
        "🐅 大兴安岭是东北虎、原麝、紫貂等珍稀动物的栖息地",
        "💧 大兴安岭是嫩江、额尔古纳河的发源地，被称为'东北水塔'",
        "🌍 大兴安岭森林每年吸收的 CO₂ 约 2.5 亿吨，相当于 5000 万辆汽车的排放",
        "🏔️ 大兴安岭山脉全长约 1400 公里，从内蒙古延伸到黑龙江",
        "🌿 大兴安岭的落叶松林是中国最大的寒温带针叶林生态系统",
        "📈 2013-2017年，大兴安岭夏季平均温约 18℃，是全国避暑胜地",
        "🔥 大兴安岭落叶松林具有极强的耐寒性，可在 -70℃ 极端条件下生存",
        "🏞️ 大兴安岭有中国面积最大的原始森林，占全国森林总面积的 8%"
    ]
    return random.choice(facts)


def link_to_daxinganling(temp, aqi, wind_dir):
    tips = []
    if any(k in wind_dir for k in ["北", "西北", "东北"]):
        tips.append("🍃 风来自大兴安岭方向 → 林区洁净空气正在滋养你所在的城市！")
        if aqi <= 50:
            tips.append("✅ 优质空气质量得益于大兴安岭森林碳汇与生态屏障作用")
    else:
        tips.append("💨 风不经过大兴安岭 → 但林区依然守护着东北生态安全")
    if temp > 22:
        tips.append("🌡 气温偏高 → 大兴安岭的天然冷空气未覆盖到本地区")
    elif temp < 15:
        tips.append("🌡 气温偏低 → 受大兴安岭冷源气候影响明显，天然空调生效")
    else:
        tips.append("🌡 气温适中 → 处于大兴安岭生态气候影响范围内")
    return tips


# ---------------------- 百度OCR账单识别核心函数 ----------------------
def extract_bill_from_image(img):
    try:
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        result = client.basicGeneral(img_bytes)
        if result.get('words_result'):
            text = '\n'.join([w['words'] for w in result['words_result']])
        else:
            text = ""

        elec = gas = water = heat = 0.0
        elec_pattern = r"(电费|用电.*?金额|应付金额.*?电)\D*(\d+\.?\d*)"
        gas_pattern = r"(燃气费|燃气.*?金额|天然气)\D*(\d+\.?\d*)"
        water_pattern = r"(水费|用水.*?金额|自来水)\D*(\d+\.?\d*)"
        heat_pattern = r"(暖气费|供暖|采暖)\D*(\d+\.?\d*)"

        elec_match = re.search(elec_pattern, text, re.I)
        gas_match = re.search(gas_pattern, text, re.I)
        water_match = re.search(water_pattern, text, re.I)
        heat_match = re.search(heat_pattern, text, re.I)

        if elec_match: elec = float(elec_match.group(2))
        if gas_match: gas = float(gas_match.group(2))
        if water_match: water = float(water_match.group(2))
        if heat_match: heat = float(heat_match.group(2))

        return elec, gas, water, heat
    except Exception as e:
        st.error(f"识别失败：{str(e)}")
        return 0, 0, 0, 0


# -------------------------- 侧边栏 --------------------------
with st.sidebar:
    st.title("🌍 大兴安岭环境监测系统")
    menu = st.radio("请选择功能", ["大兴安岭气温分析", "实时天气数据"])

# -------------------------- 主页面 --------------------------
st.title("📊 大兴安岭环境监测平台")

# ========================== 1. 大兴安岭气温分析 ==========================
if menu == "大兴安岭气温分析":
    set_background(ALIYUN_BG1)

    st.info(f"🌲 **今日·大兴安岭**\n\n{get_daily_fact()}")

    st.markdown("""
在全球变暖的持续驱动下，大兴安岭生态系统正经历着从缓慢适应到剧烈转折的深刻演变。2017年以前，区域整体处于缓慢升温、偏冷湿的状态，特别是在2011至2015年间，生态系统长期适应稳定，气候的微小波动并未打破原有格局，呈现出落叶松占优、冻土稳定、湿地发育良好且耐寒物种稳定的低扰动特征。然而，2017年后区域气候进入加速暖干化与极端高温干旱频发阶段，并在2020至2024年间迎来关键拐点，气候改变从"小幅扰动"彻底转变为结构性冲击。气温的持续攀升首先加速了冻土的消融，进而引发湿地大面积萎缩，并推动原生针叶林逐步被北侵的阔叶林取代。这种生境的剧烈改变不仅造成生物物候错位、珍稀寒带物种衰退和生物多样性降低，还导致森林灾害频发。与此同时，土壤退化与区域碳汇功能的减弱，伴随着地质灾害、火灾及病虫害风险的全面上升，标志着整个寒温带生态系统正面临不可逆的结构性改变与持续攀升的生态风险。
""")

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
        st.subheader("🌍 分年气温时空变化图")
        year = st.selectbox("选择年份", [2013, 2014, 2015, 2016, 2017])
        show_image(f"{year}年大兴安岭气温变化图.png")

    elif sub_menu == "通量与多变量分析":
        st.subheader("🔍 通量数据与多变量分析")
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
        st.subheader("♻️ 生活缴费一键算碳 · 大兴安岭碳中和方案")
        st.markdown("### 📸 上传缴费单截图 → 自动识别金额计算碳中和")

        uploaded_file = st.file_uploader("上传电费/燃气费/水费/暖气费账单截图", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            img = Image.open(uploaded_file)
            st.image(img, caption="已上传账单", use_column_width=True)

            with st.spinner("正在识别账单金额..."):
                elec, gas, water, heat = extract_bill_from_image(img)
                st.session_state.elec_bill = elec
                st.session_state.gas_bill = gas
                st.session_state.water_bill = water
                st.session_state.heat_bill = heat
                st.success(f"识别完成！\n电费：{elec}元 | 燃气费：{gas}元 | 水费：{water}元 | 暖气费：{heat}元")
                st.rerun()

        st.markdown("### 或选择家庭档位一键自动填充账单，也可微调金额")

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

        st.markdown("---")
        st.markdown("### 📝 识别/填充后金额（可手动修改）")
        e = st.number_input("💡 电费", 0, value=st.session_state.elec_bill, step=10)
        g = st.number_input("🔥 燃气费", 0, value=st.session_state.gas_bill, step=10)
        w = st.number_input("🚰 水费", 0, value=st.session_state.water_bill, step=5)
        h = st.number_input("🏠 暖气费", 0, value=st.session_state.heat_bill, step=50)
        st.session_state.elec_bill = e
        st.session_state.gas_bill = g
        st.session_state.water_bill = w
        st.session_state.heat_bill = h

        ce, cg, cw, ch, total = calculate_from_bill(e, g, w, h)
        trees = forest_offset(total)

        st.markdown("---")
        st.markdown("### 📊 月度碳排放量")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("用电", f"{ce}kg")
        col2.metric("用气", f"{ce}kg")
        col3.metric("用水", f"{cw}kg")
        col4.metric("暖气", f"{ch}kg")
        st.metric("✅ 月度总碳排放", f"**{total} kg CO₂**")

        if total > 0:
            st.success(f"🌲 需要种植 {trees} 棵大兴安岭落叶松即可完全碳中和！")
            st.progress(min(total / 500, 1.0))
            if total < 100:
                st.success("👍 碳足迹较小，继续保持！")
            elif total < 300:
                st.info("🌿 碳足迹适中")
            else:
                st.warning("🌲 碳足迹较高，建议节约用电")
            with st.expander("💡 节能减排小贴士"):
                st.markdown(
                    "- 🔌 不用的电器拔掉插头\n- 💡 使用LED灯\n- ❄️ 空调调高1℃省电10%\n- 🚿 降低洗澡水温\n- 🧺 洗衣机满载使用")

        st.markdown("---")
        st.info(
            "🌲 **大兴安岭森林碳汇价值**\n- 每公顷年固碳≈2.8吨\n- 保护冻土=保护天然碳汇\n- 落叶松是寒带最强固碳树种之一")

# ========================== 2. 实时天气数据 ==========================
elif menu == "实时天气数据":
    set_background(ALIYUN_BG2)
    import math

    st.header("🌤 全球实时天气查询")


    def wgs84_to_gcj02(lng, lat):
        PI = 3.14159265358979324
        a = 6378245.0
        ee = 0.006693421622965943

        def transformLat(x, y):
            ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
            ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
            ret += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
            ret += (160.0 * math.sin(y / 12.0 * PI) + 320 * math.sin(y / 30.0 * PI)) * 2.0 / 3.0
            return ret

        def transformLng(x, y):
            ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
            ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
            ret += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
            ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0
            return ret

        dLat = transformLat(lng - 105.0, lat - 35.0)
        dLng = transformLng(lng - 105.0, lat - 35.0)
        radLat = lat / 180.0 * PI
        magic = math.sin(radLat)
        magic = 1 - ee * magic * magic
        sqrtMagic = math.sqrt(magic)
        dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * PI)
        dLng = (dLng * 180.0) / (a / sqrtMagic * math.cos(radLat) * PI)
        gcjLng = lng + dLng
        gcjLat = lat + dLat
        return gcjLng, gcjLat


    if 'ip_location_done' not in st.session_state:
        st.session_state.ip_location_done = False

    if not st.session_state.ip_location_done:
        st.info("📍正在请求手机GPS定位，请在浏览器弹窗允许位置权限！")
        location = streamlit_geolocation()
        lat = location.get("latitude")
        lon = location.get("longitude")
        auto_city = None
        if lat and lon:
            gcj_lon, gcj_lat = wgs84_to_gcj02(lon, lat)
            amap_key = "e73c79c1fdce8187e310ba247a163ae5"
            res = requests.get(
                f"https://restapi.amap.com/v3/geocode/regeo?key={amap_key}&location={gcj_lon},{gcj_lat}&radius=300").json()
            if res["status"] == "1":
                auto_city = res["regeocode"]["addressComponent"]["city"].replace("市", "")
                test = seniverse_now(auto_city)
                if test:
                    st.session_state.city = auto_city
                    st.success(f"GPS定位成功：{auto_city}")
                else:
                    st.session_state.city = "南通"
                    st.info("定位城市无效，默认南通")
        else:
            st.info("⚠️GPS权限未获取，默认城市：南通，可下方手动切换")
            st.session_state.city = "南通"
        st.session_state.ip_location_done = True

    st.subheader(f"📍当前查询城市：{st.session_state.city}")
    st.divider()

    st.markdown("#### ⚡快捷点选城市")
    r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
    with r1c1:
        if st.button("南通"):
            st.session_state.city = "南通";
            st.rerun()
    with r1c2:
        if st.button("南京"):
            st.session_state.city = "南京";
            st.rerun()
    with r1c3:
        if st.button("苏州"):
            st.session_state.city = "苏州";
            st.rerun()
    with r1c4:
        if st.button("无锡"):
            st.session_state.city = "无锡";
            st.rerun()
    with r1c5:
        if st.button("泰州"):
            st.session_state.city = "泰州";
            st.rerun()

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        if st.button("上海"):
            st.session_state.city = "上海";
            st.rerun()
    with r2c2:
        if st.button("杭州"):
            st.session_state.city = "杭州";
            st.rerun()
    with r2c3:
        if st.button("北京"):
            st.session_state.city = "北京";
            st.rerun()
    with r2c4:
        if st.button("广州"):
            st.session_state.city = "广州";
            st.rerun()

    st.divider()
    input_city = st.text_input("✍手动输入城市名称（如：常州、成都）：")
    if input_city.strip() != "":
        st.session_state.city = input_city.strip()
        st.rerun()

    with st.spinner(f"获取 {st.session_state.city} 天气..."):
        wc = seniverse_now(st.session_state.city)
        daily = seniverse_daily(st.session_state.city, 3)
        aqi_data = seniverse_aqi(st.session_state.city)

    if wc:
        if wc["name"] not in st.session_state.weather_history:
            st.session_state.weather_history.append(wc["name"])
            if len(st.session_state.weather_history) > 10:
                st.session_state.weather_history.pop(0)

        st.divider()
        st.subheader("🌤 当前天气")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏙 城市", wc["name"])
        col2.metric("🌤 天气", wc["text"])
        col3.metric("🌡 温度", f"{wc['temp']}℃")
        col4.metric("💧 湿度", f"{wc['humidity']}%")
        st.columns(1)[0].metric("💨 风速", f"{wc['wind']} m/s")

        st.divider()
        st.subheader("🌫 空气质量 AQI")
        aqi_num = 70
        if aqi_data:
            aq, ql, pm = aqi_data["aqi"], aqi_data["quality"], aqi_data["pm25"]
            aqi_num = aq
            ca1, ca2, ca3 = st.columns(3)
            ca1.metric("AQI", aq)
            ca2.metric("等级", ql)
            ca3.metric("PM2.5", pm)
            if ql == "优":
                st.success("✅ 空气优秀，适合户外运动")
            elif ql == "良":
                st.info("✅ 空气良好")
            elif "轻度" in ql:
                st.warning("⚠️ 轻度污染，敏感人群减少外出")
            else:
                st.error("❌ 污染严重，避免外出")
        else:
            st.info("ℹ️ 暂无AQI数据")

        st.divider()
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

        st.divider()
        st.subheader("🌲 大兴安岭生态联动")
        tips_list = link_to_daxinganling(wc["temp"], aqi_num, wc["wind_dir"])
        for t in tips_list:
            if "🍃" in t or "✅" in t:
                st.success(t)
            else:
                st.info(t)

        st.divider()
        st.subheader("💡 今日生活建议")
        st.info(get_clothing_suggestion(wc["temp"]))
        st.info(get_sunscreen_suggestion(wc["text"]))
        st.info(get_outdoor_suggestion(wc["text"], wc["wind"], wc["temp"]))

    st.divider()
    st.subheader("🔍 查询其他城市")
    city_in = st.text_input("输入城市名：", key="manual_city")
    if city_in:
        with st.spinner(f"获取 {city_in} 天气..."):
            wo = seniverse_now(city_in)
            do = seniverse_daily(city_in, 3)
            ao = seniverse_aqi(city_in)
        if wo:
            st.divider()
            st.subheader("🌤 查询结果")
            col_base = st.columns(4)
            col_base[0].metric("🏙 城市", wo["name"])
            col_base[1].metric("🌡 温度", f"{wo['temp']}℃")
            col_base[2].metric("🌤 天气", wo["text"])
            col_base[3].metric("💧 湿度", f"{wo['humidity']}%")

            tmp_aqi = ao["aqi"] if ao else 70
            st.divider()
            st.subheader("🌫 空气质量 AQI")
            if ao:
                aq, ql, pm = ao["aqi"], ao["quality"], ao["pm25"]
                ca1, ca2, ca3 = st.columns(3)
                ca1.metric("AQI", aq)
                ca2.metric("等级", ql)
                ca3.metric("PM2.5", pm)
            else:
                st.info("ℹ️ 暂无AQI数据")

            st.divider()
            st.subheader("📅 未来3天预报")
            if do:
                cols = st.columns(3)
                for i, d in enumerate(do):
                    with cols[i]:
                        st.markdown(f"""
                            <div style='text-align:center; padding:10px; background:#f6f6f6; border-radius:12px;'>
                            {d['date'][-5:]}<br>
                            <span style='font-size:30px'>{get_weather_icon(d['text_day'])}</span><br>
                            {d['text_day']}<br>
                            {d['low']}~{d['high']}℃
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.warning("未找到该城市天气，请检查输入是否正确")