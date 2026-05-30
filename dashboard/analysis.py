# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ---------------------- 页面配置 ----------------------
st.set_page_config(page_title="温度趋势分析", layout="wide")
st.title("🌡 2017年大兴安岭站温度变化趋势")

# ---------------------- 1. 读取数据 ----------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_filename = "2017年大兴安岭站气象30分钟数据.csv"
csv_path = os.path.join(script_dir, csv_filename)

try:
    df = pd.read_csv(
        csv_path,
        encoding="utf-8-sig",
        skiprows=[1],
        low_memory=False
    )
    st.success("✅ 数据加载成功")
except:
    st.error("❌ 未找到CSV文件，请放在同目录下")
    st.stop()

# ---------------------- 2. 时间处理 ----------------------
for col in ["年","月","日","时","分","秒"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["完整时间"] = pd.to_datetime(
    {
        "year": df["年"],
        "month": df["月"],
        "day": df["日"],
        "hour": df["时"],
        "minute": df["分"],
        "second": df["秒"]
    }, errors="coerce"
)

# ---------------------- 3. 温度异常过滤 ----------------------
temp_col = "近地面空气温度"
df[temp_col] = pd.to_numeric(df[temp_col], errors="coerce")
df = df.dropna(subset=["完整时间", temp_col])
df = df[(df[temp_col] >= -45) & (df[temp_col] <= 45)]

# ---------------------- 4. 统计值 ----------------------
max_temp = df[temp_col].max()
min_temp = df[temp_col].min()
avg_temp = df[temp_col].mean()
max_time = df.loc[df[temp_col].idxmax(), "完整时间"]
min_time = df.loc[df[temp_col].idxmin(), "完整时间"]

# ---------------------- 5. 7天平滑 ----------------------
df["温度平滑"] = df[temp_col].rolling(window=48*7, min_periods=1).mean()

# ---------------------- 6. 显示统计卡片 ----------------------
st.subheader("📊 2017年温度统计")
col1, col2, col3 = st.columns(3)
col1.metric("最高温度", f"{max_temp:.2f} ℃", f"出现于 {max_time.strftime('%Y-%m-%d %H:%M')}")
col2.metric("最低温度", f"{min_temp:.2f} ℃", f"出现于 {min_time.strftime('%Y-%m-%d %H:%M')}")
col3.metric("全年平均温度", f"{avg_temp:.2f} ℃")

# ---------------------- 7. 画图（中文正常） ----------------------
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(16, 7))
# 原始温度
ax.plot(df["完整时间"], df[temp_col], color="#72A0C1",
        linewidth=0.6, alpha=0.6, label="30分钟原始温度")
# 平滑线
ax.plot(df["完整时间"], df["温度平滑"], color="#D9534F",
        linewidth=1.8, label="7天平滑趋势")

# 极值标注
ax.scatter(max_time, max_temp, color="red", s=60, zorder=5)
ax.annotate(f'最高温 {max_temp:.1f}℃',
             xy=(max_time, max_temp), xytext=(15,15),
             textcoords='offset points', color='red', fontsize=11)

ax.scatter(min_time, min_temp, color="#0072B2", s=60, zorder=5)
ax.annotate(f'最低温 {min_temp:.1f}℃',
             xy=(min_time, min_temp), xytext=(15,-20),
             textcoords='offset points', color='#0072B2', fontsize=11)

# 平均温虚线
ax.axhline(y=avg_temp, color="green", linestyle="--",
           alpha=0.7, label=f'全年平均 {avg_temp:.1f}℃')

ax.set_title("2017年大兴安岭站近地面空气温度变化趋势", fontsize=16, pad=20)
ax.set_xlabel("时间", fontsize=13)
ax.set_ylabel("温度 (℃)", fontsize=13)
ax.grid(True, alpha=0.35, linestyle="--")
ax.legend(loc="upper right", fontsize=11)
plt.xticks(rotation=45)
plt.tight_layout()

# ---------------------- 8. Streamlit显示图表 ----------------------
st.subheader("📈 温度趋势图")
st.pyplot(fig)

# 可选：保存图片
plt.savefig("2017温度趋势_完美版.png", dpi=300, bbox_inches="tight")
st.download_button("📥 下载高清图", open("2017温度趋势_完美版.png", "rb"),
                   file_name="2017温度趋势_完美版.png", mime="image/png")

st.success("🎉 所有分析完成！")