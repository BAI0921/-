# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import FactorAnalysis, PCA
import re

# ---------------------- 页面配置 ----------------------
st.set_page_config(page_title="气象因素分析", layout="wide")
st.title("🌤 大兴安岭站气象数据 - 因子分析（修复版）")

# ---------------------- 1. 加载数据 ----------------------
st.header("1. 数据加载")
csv_file = "2017年大兴安岭站气象30分钟数据.csv"
df = None
try:
    df = pd.read_csv(csv_file, encoding='utf-8-sig', skiprows=[1])
    st.success(f"✅ 数据加载成功，原始行数：{len(df)}")
except Exception as e:
    st.error(f"❌ 读取失败：{e}")
    st.stop()

# ---------------------- 2. 数据预处理 ----------------------
st.header("2. 数据预处理")
exclude_cols = ['年', '月', '日', '时', '分', '秒']
feature_cols = [col for col in df.columns if col not in exclude_cols]
data = df[feature_cols].copy()

# 清洗所有变量：去掉单位符号（℃、mm、m3 m-3等），转数字
for col in data.columns:
    data[col] = data[col].astype(str).apply(lambda x: re.sub(r'[^\d\.-]', '', x))
    data[col] = pd.to_numeric(data[col], errors='coerce')

# 只删除缺失率超过60%的列
missing_rate = data.isnull().sum() / len(data)
cols_to_drop = missing_rate[missing_rate > 0.6].index.tolist()
if cols_to_drop:
    st.warning(f"删除缺失率>60%的列：{cols_to_drop}")
    data = data.drop(columns=cols_to_drop)

# 缺失值用均值填充
data = data.fillna(data.mean(numeric_only=True))

# 强制检查样本数
st.write(f"清洗后：样本数 = {len(data)}，变量数 = {len(data.columns)}")
if len(data) == 0:
    st.error("❌ 样本数为0，检查数据文件或清洗步骤！")
    st.stop()

# ---------------------- 3. 标准化 ----------------------
st.header("3. 数据标准化")
scaler = StandardScaler()
data_scaled = scaler.fit_transform(data)
st.success("✅ 标准化完成")

# ---------------------- 4. 确定因子数量 ----------------------
st.header("4. 因子数量判断（特征值>1）")
pca = PCA()
pca.fit(data_scaled)
eigenvalues = pca.explained_variance_
n_factors = sum(eigenvalues > 1)

st.write(f"前10个特征值：{[round(x, 2) for x in eigenvalues[:10]]}")
st.success(f"✅ 最终选择因子数：{n_factors}")

# 碎石图
fig1, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(range(1, len(eigenvalues)+1), eigenvalues, 'o-', color='#c91010')
ax1.axhline(1, color='red', linestyle='--', label='特征值=1')
ax1.set_title("碎石图")
ax1.set_xlabel("因子编号")
ax1.set_ylabel("特征值")
ax1.legend()
ax1.grid(alpha=0.3)
st.pyplot(fig1)

# 累积方差贡献率图
var_sum = pca.explained_variance_ratio_.cumsum()
fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.bar(range(1, len(var_sum)+1), pca.explained_variance_ratio_, color='#5499c7')
ax2.plot(range(1, len(var_sum)+1), var_sum, 'o-', color='darkred', label='累积贡献率')
ax2.axhline(0.8, color='green', linestyle='--', label='80%阈值')
ax2.legend()
ax2.grid(alpha=0.3)
st.pyplot(fig2)

# ---------------------- 5. 因子分析 ----------------------
st.header(f"5. 因子分析（{n_factors}个因子）")
loadings = None
try:
    fa = FactorAnalysis(n_components=n_factors, random_state=42, max_iter=2000)
    fa_scores = fa.fit_transform(data_scaled)
    loadings = fa.components_.T
    st.success("✅ 因子分析完成")
except Exception as e:
    st.error(f"因子分析出错：{e}")
    st.stop()

# 因子载荷矩阵
st.subheader("📋 因子载荷矩阵")
loadings_df = pd.DataFrame(
    loadings.round(3),
    index=data.columns,
    columns=[f'因子{i+1}' for i in range(n_factors)]
)
st.dataframe(loadings_df, use_container_width=True)

# 因子载荷热力图
st.subheader("🔥 因子载荷热力图")
fig3, ax3 = plt.subplots(figsize=(10, 8))
im = ax3.imshow(loadings, cmap='RdBu', aspect='auto')
plt.colorbar(im, ax=ax3)
ax3.set_yticks(range(len(data.columns)))
ax3.set_yticklabels(data.columns)
ax3.set_xticks(range(n_factors))
ax3.set_xticklabels([f'因子{i+1}' for i in range(n_factors)])
plt.tight_layout()
st.pyplot(fig3)

# 变量共同度
st.subheader("🎯 变量共同度")
communality = np.sum(loadings ** 2, axis=1)
comm_df = pd.DataFrame({
    '变量': data.columns,
    '共同度': communality.round(3)
}).sort_values('共同度', ascending=False)
st.dataframe(comm_df, use_container_width=True)

st.balloons()
st.success("🎉 因子分析全部完成，无报错！")

# （文件末尾已自动添加空行）
