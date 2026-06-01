import streamlit as st
import requests
import warnings

warnings.filterwarnings('ignore')

# --------------------------
# 心知天气（你原来的密钥）
# --------------------------
SENIVERSE_KEY = "SyBQ06H2yR2RIEJn3"
NOW_URL = "https://api.seniverse.com/v3/weather/now.json"


def get_weather(city):
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
        st.error(f"出错：{e}")
    return None


# --------------------------
# 获取当前IP定位城市（自动定位）
# --------------------------
def get_current_city():
    try:
        ip_api = "http://ip-api.com/json/?lang=zh-CN"
        data = requests.get(ip_api, timeout=10).json()
        return data["city"]
    except:
        return "北京"


# --------------------------
# 页面
# --------------------------
st.set_page_config(page_title="实时天气", page_icon="🌤", layout="centered")
st.title("🌤 实时天气查询（自动定位+手动查询）")

# ======================
# 1. 自动显示当前城市
# ======================
st.subheader("📍 当前所在地天气")
current_city = get_current_city()

with st.spinner("正在获取你当前的天气..."):
    current_w = get_weather(current_city)

if current_w:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("城市", current_w["name"])
    col2.metric("天气", current_w["text"])
    col3.metric("温度", f"{current_w['temp']} ℃")
    col4.metric("湿度", f"{current_w['humidity']} %")
    st.metric("风速", f"{current_w['wind']} m/s")
else:
    st.warning("无法获取当前位置天气")

# ======================
# 2. 手动查询其他城市
# ======================
st.divider()
st.subheader("🔍 查询其他城市天气")

city = st.text_input("输入要查询的城市：", placeholder="例如：上海、哈尔滨、广州")
if st.button("开始查询"):
    if city.strip() != "":
        with st.spinner("正在查询..."):
            w = get_weather(city)
        if w:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("城市", w["name"])
            col2.metric("天气", w["text"])
            col3.metric("温度", f"{w['temp']} ℃")
            col3.metric("湿度", f"{w['humidity']} %")
            st.metric("风速", f"{w['wind']} m/s")
        else:
            st.error("查询失败，请输入正确城市名")
