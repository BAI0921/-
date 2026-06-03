import streamlit as st
import base64
from pathlib import Path

st.set_page_config(page_title="测试背景图", layout="wide")

# ===== 调试信息 =====
st.write("=== 开始测试 ===")

# 获取 static 目录
CURRENT_DIR = Path(__file__).parent
STATIC_DIR = CURRENT_DIR / "static"
st.write(f"static 目录路径：{STATIC_DIR}")
st.write(f"static 目录是否存在：{STATIC_DIR.exists()}")

# 检查背景图文件
bg_file = STATIC_DIR / "daxinganling_bg.png"
st.write(f"背景图文件路径：{bg_file}")
st.write(f"背景图文件是否存在：{bg_file.exists()}")

# 加载背景图
if bg_file.exists():
    with open(bg_file, "rb") as f:
        bg_data = base64.b64encode(f.read()).decode()
    st.write(f"base64 数据长度：{len(bg_data)}")

    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"]{{
        background-image: url("data:image/png;base64,{bg_data}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.success("✅ 背景图代码已注入！")
else:
    st.error("❌ 找不到背景图文件")

# 显示一些内容
st.title("测试页面")
st.write("如果背景图显示出来了，说明代码正常工作")

# 测试其他图片
test_img = STATIC_DIR / "weather_bg.png"
if test_img.exists():
    with open(test_img, "rb") as f:
        test_data = base64.b64encode(f.read()).decode()
    st.image(f"data:image/png;base64,{test_data}", caption="天气背景图测试")
else:
    st.warning("找不到 weather_bg.png")