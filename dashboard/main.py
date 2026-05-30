# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import FactorAnalysis, PCA
import re
import os
import glob
from typing import Optional, Dict

# ---------------------- 页面配置 ----------------------
st.set_page_config(
    page_title="大兴安岭气象数据分析系统",
    page_icon="🌲",
    layout="wide"
)

# 初始化session_state
if 'page' not in st.session_state:
    st.session_state.page = '温度趋势分析'

# ---------------------- 侧边栏导航 ----------------------
st.sidebar.title("📊 导航菜单")
page = st.sidebar.radio(
    "请选择分析功能",
    ["🌡 温度趋势分析", "📈 多年对比分析", "🔬 因子分析"],
    index=0
)

# 更新session_state
st.session_state.page = page

# 全局字体设置（解决中文乱码）
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False


# ---------------------- 通用工具函数 ----------------------
def get_season(m: int) -> str:
    """根据月份判断季节"""
    if 3 <= m <= 5:
        return "春季"
    elif 6 <= m <= 8:
        return "夏季"
    elif 9 <= m <= 11:
        return "秋季"
    else:
        return "冬季"


def find_csv_files():
    """查找当前目录下所有CSV文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(script_dir):
        script_dir = os.getcwd()

    csv_files = glob.glob(os.path.join(script_dir, "*.csv"))
    csv_files = [os.path.basename(f) for f in csv_files]

    return script_dir, csv_files


@st.cache_data
def load_single_year(file_path: str, year: int) -> Optional[pd.DataFrame]:
    """加载单一年份数据"""
    df = None

    # 尝试不同的编码
    encodings = ['utf-8-sig', 'gbk', 'gb2312', 'utf-8', 'latin1']

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, skiprows=[1], encoding=encoding)
            print(f"成功使用 {encoding} 编码读取文件")
            break
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
        except (IOError, OSError) as e:
            print(f"文件读取错误: {e}")
            return None

    if df is None:
        st.error(f"无法读取文件 {file_path}")
        return None

    try:
        # 查找年份列
        year_col = None
        for col in df.columns:
            if '年' in col:
                year_col = col
                break

        if year_col is None:
            st.warning(f"文件 {file_path} 中未找到年份列")
            return None

        df = df[df[year_col] == year]
        if len(df) == 0:
            st.warning(f"文件中没有 {year} 年的数据")
            return None

        # 查找时间相关列
        month_col = None
        day_col = None
        hour_col = None
        minute_col = None
        second_col = None

        for col in df.columns:
            if '月' in col:
                month_col = col
            elif '日' in col:
                day_col = col
            elif '时' in col:
                hour_col = col
            elif '分' in col:
                minute_col = col
            elif '秒' in col:
                second_col = col

        # 拼接完整时间列
        if all([year_col, month_col, day_col, hour_col, minute_col, second_col]):
            df['时间'] = pd.to_datetime(
                df[year_col].astype(str) + '-' +
                df[month_col].astype(str) + '-' +
                df[day_col].astype(str) + ' ' +
                df[hour_col].astype(str) + ':' +
                df[minute_col].astype(str) + ':' +
                df[second_col].astype(str),
                errors='coerce'
            )
        else:
            st.warning(f"文件 {file_path} 中缺少必要的时间列")
            return None

        # 匹配温度字段
        temp_col = None
        for col in df.columns:
            if '温度' in col or '气温' in col:
                temp_col = col
                break

        if temp_col is None:
            st.warning(f"文件 {file_path} 中未找到温度列")
            return None

        df['温度'] = pd.to_numeric(df[temp_col], errors='coerce')
        df = df.dropna(subset=['时间', '温度'])
        df = df[(df['温度'] >= -45) & (df['温度'] <= 45)]

        if len(df) == 0:
            st.warning(f"{year} 年数据清洗后无有效记录")
            return None

        return df
    except (KeyError, ValueError, TypeError) as e:
        st.error(f"数据处理失败: {e}")
        return None


@st.cache_data
def load_all_years() -> Dict[int, pd.DataFrame]:
    """批量加载2013-2017数据"""
    script_dir, csv_files = find_csv_files()
    years = [2013, 2014, 2015, 2016, 2017]
    data_dict = {}

    for year in years:
        file_path = None
        for f in csv_files:
            if str(year) in f:
                file_path = os.path.join(script_dir, f)
                break
        if file_path:
            df = load_single_year(file_path, year)
            if df is not None and len(df) > 0:
                data_dict[year] = df

    return data_dict


# ---------------------- 页面1：温度趋势分析 ----------------------
def page_temperature_trend():
    """温度趋势分析页面"""
    st.title("🌡 2017年大兴安岭站温度变化趋势")
    script_dir, csv_files = find_csv_files()

    # 查找2017年文件
    file_path = None
    for f in csv_files:
        if '2017' in f:
            file_path = os.path.join(script_dir, f)
            break

    if file_path is None:
        st.error("❌ 未找到2017年数据文件！")
        st.info("请确保目录下有包含'2017'的CSV文件")
        st.write("当前目录下的CSV文件：", csv_files)
        return

    with st.spinner("加载数据中..."):
        df = load_single_year(file_path, 2017)

    if df is None or len(df) == 0:
        st.error("❌ 无法加载2017年数据！")
        return

    st.success(f"✅ 数据加载成功，共 {len(df)} 条有效记录")

    max_temp = df['温度'].max()
    min_temp = df['温度'].min()
    avg_temp = df['温度'].mean()
    max_time = df.loc[df['温度'].idxmax(), '时间']
    min_time = df.loc[df['温度'].idxmin(), '时间']

    st.subheader("📊 2017年温度统计")
    col1, col2, col3 = st.columns(3)
    col1.metric("最高温度", f"{max_temp:.2f} ℃",
                f"出现于 {max_time.strftime('%Y-%m-%d %H:%M')}")
    col2.metric("最低温度", f"{min_temp:.2f} ℃",
                f"出现于 {min_time.strftime('%Y-%m-%d %H:%M')}")
    col3.metric("全年平均温度", f"{avg_temp:.2f} ℃")

    # 7日滑动平均
    df['温度平滑'] = df['温度'].rolling(window=336, min_periods=1).mean()

    st.subheader("📈 温度变化趋势图")
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df['时间'], df['温度'], color="#72A0C1", linewidth=0.6,
            alpha=0.6, label="30分钟原始温度")
    ax.plot(df['时间'], df['温度平滑'], color="#D9534F", linewidth=1.8,
            label="7天平滑趋势")

    ax.scatter(max_time, max_temp, color="red", s=60, zorder=5)
    ax.annotate(f'最高温 {max_temp:.1f}℃', xy=(max_time, max_temp),
                xytext=(15, 15), textcoords='offset points',
                color='red', fontsize=10)
    ax.scatter(min_time, min_temp, color="#0072B2", s=60, zorder=5)
    ax.annotate(f'最低温 {min_temp:.1f}℃', xy=(min_time, min_temp),
                xytext=(15, -20), textcoords='offset points',
                color='#0072B2', fontsize=10)
    ax.axhline(y=avg_temp, color="green", linestyle="--", alpha=0.7,
               label=f'全年平均 {avg_temp:.1f}℃')

    ax.set_title("2017年大兴安岭站近地面空气温度变化趋势", fontsize=14)
    ax.set_xlabel("时间")
    ax.set_ylabel("温度 (℃)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3, linestyle="--")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

    # 月均温柱状图
    st.subheader("📅 月平均温度统计")
    df['月份'] = df['时间'].dt.month
    monthly_avg = df.groupby('月份')['温度'].mean()
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    monthly_avg.plot(kind='bar', ax=ax2, color='#4682B4')
    ax2.set_title("2017年月平均温度")
    ax2.set_xlabel("月份")
    ax2.set_ylabel("温度 (℃)")
    ax2.set_xticklabels(['1月', '2月', '3月', '4月', '5月', '6月',
                         '7月', '8月', '9月', '10月', '11月', '12月'])
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig2)


# ---------------------- 页面2：多年对比分析 ----------------------
def page_yearly_comparison():
    """多年对比分析页面"""
    st.title("📊 2013-2017年大兴安岭气温对比分析")

    with st.spinner("加载多年数据中..."):
        data_dict = load_all_years()

    if len(data_dict) == 0:
        st.error("❌ 未找到任何年份的数据文件！")
        st.info("请确保目录下有2013-2017年的CSV文件，文件名需包含年份数字")
        script_dir, csv_files = find_csv_files()
        st.write("当前目录下的CSV文件：", csv_files)
        return

    st.success(f"✅ 成功加载 {len(data_dict)} 个年份的数据: {sorted(data_dict.keys())}")

    stats = []
    for year in sorted(data_dict.keys()):
        df = data_dict[year]
        stats.append({
            '年份': year,
            '最高温': df['温度'].max(),
            '最低温': df['温度'].min(),
            '平均温': df['温度'].mean(),
            '数据量': len(df)
        })
    stats_df = pd.DataFrame(stats)

    st.subheader("📋 各年份温度统计表")
    st.dataframe(stats_df, use_container_width=True)

    # 柱状对比图
    st.subheader("📊 温度对比柱状图")
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    x = range(len(stats_df))
    width = 0.25
    bars1 = ax1.bar([i - width for i in x], stats_df['最高温'],
                    width, label='最高温', color='red', alpha=0.7)
    bars2 = ax1.bar(x, stats_df['平均温'], width,
                    label='平均温', color='green', alpha=0.7)
    bars3 = ax1.bar([i + width for i in x], stats_df['最低温'],
                    width, label='最低温', color='blue', alpha=0.7)

    for bar in bars1:
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=9)
    for bar in bars3:
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 2,
                 f'{bar.get_height():.1f}', ha='center', va='top',
                 fontsize=9, color='white')

    ax1.set_xlabel('年份')
    ax1.set_ylabel('温度 (℃)')
    ax1.set_title('2013-2017年大兴安岭气温对比')
    ax1.set_xticks(x)
    ax1.set_xticklabels(stats_df['年份'])
    ax1.legend()
    ax1.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    st.pyplot(fig1)

    # 趋势折线图
    st.subheader("📈 温度变化趋势")
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.plot(stats_df['年份'], stats_df['最高温'], 'ro-',
             linewidth=2, markersize=8, label='最高温')
    ax2.plot(stats_df['年份'], stats_df['平均温'], 'go-',
             linewidth=2, markersize=8, label='平均温')
    ax2.plot(stats_df['年份'], stats_df['最低温'], 'bo-',
             linewidth=2, markersize=8, label='最低温')

    for _, row in stats_df.iterrows():
        ax2.annotate(f"{row['最高温']:.1f}", (row['年份'], row['最高温']),
                     xytext=(0, 10), textcoords='offset points', ha='center')
        ax2.annotate(f"{row['平均温']:.1f}", (row['年份'], row['平均温']),
                     xytext=(0, 10), textcoords='offset points', ha='center')
        ax2.annotate(f"{row['最低温']:.1f}", (row['年份'], row['最低温']),
                     xytext=(0, -15), textcoords='offset points', ha='center')

    ax2.set_xlabel('年份')
    ax2.set_ylabel('温度 (℃)')
    ax2.set_title('2013-2017年大兴安岭气温变化趋势')
    ax2.legend()
    ax2.grid(alpha=0.3)
    ax2.set_xticks(stats_df['年份'])
    plt.tight_layout()
    st.pyplot(fig2)


# ---------------------- 页面3：因子分析 ----------------------
def page_factor_analysis():
    """因子分析页面"""
    st.title("🔬 气象因素因子分析")
    script_dir, csv_files = find_csv_files()

    # 查找2017年文件
    file_path = None
    for f in csv_files:
        if '2017' in f:
            file_path = os.path.join(script_dir, f)
            break

    if file_path is None:
        st.error("❌ 未找到2017年数据文件！")
        return

    with st.spinner("加载数据中..."):
        try:
            df = None
            encodings = ['utf-8-sig', 'gbk', 'gb2312', 'utf-8']
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, skiprows=[1], encoding=encoding)
                    break
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue

            if df is None:
                st.error("无法读取CSV文件")
                return

            st.success(f"✅ 数据加载成功，原始行数：{len(df)}")
        except (IOError, OSError) as e:
            st.error(f"❌ 读取失败：{e}")
            return

    st.header("📋 数据预处理")
    exclude_cols = ['年', '月', '日', '时', '分', '秒']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    data = df[feature_cols].copy()

    # 清洗字符、转为数值
    for col in data.columns:
        data[col] = data[col].astype(str).apply(lambda x: re.sub(r'[^\d.-]', '', x))
        data[col] = pd.to_numeric(data[col], errors='coerce')

    # 删除缺失过高列
    missing_rate = data.isnull().sum() / len(data)
    cols_to_drop = missing_rate[missing_rate > 0.6].index.tolist()
    if cols_to_drop:
        st.warning(f"删除缺失率>60%的列：{cols_to_drop}")
        data = data.drop(columns=cols_to_drop)
    data = data.fillna(data.mean(numeric_only=True))
    st.write(f"清洗后：样本数 = {len(data)}，变量数 = {len(data.columns)}")

    if len(data) == 0:
        st.error("❌ 样本数为0，请检查数据！")
        return

    # 标准化
    st.header("📊 数据标准化")
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    st.success("✅ 标准化完成")

    # PCA判断因子数
    st.header("🔢 因子数量判断（特征值>1）")
    pca = PCA()
    pca.fit(data_scaled)
    eigenvalues = pca.explained_variance_
    n_factors = sum(eigenvalues > 1)
    st.write(f"前10个特征值：{[round(x, 2) for x in eigenvalues[:10]]}")
    st.success(f"✅ 最终选择因子数：{n_factors}")

    # 碎石图
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(range(1, len(eigenvalues) + 1), eigenvalues, 'o-', color='#c91010')
    ax1.axhline(1, color='red', linestyle='--', label='特征值=1')
    ax1.set_title("碎石图")
    ax1.set_xlabel("因子编号")
    ax1.set_ylabel("特征值")
    ax1.legend()
    ax1.grid(alpha=0.3)
    st.pyplot(fig1)

    # 累积方差贡献率
    var_sum = pca.explained_variance_ratio_.cumsum()
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.bar(range(1, len(var_sum) + 1), pca.explained_variance_ratio_, color='#5499c7')
    ax2.plot(range(1, len(var_sum) + 1), var_sum, 'o-', color='#8B0000', label='累积贡献率')
    ax2.axhline(0.8, color='green', linestyle='--', label='80%阈值')
    ax2.legend()
    ax2.grid(alpha=0.3)
    st.pyplot(fig2)

    # 因子分析
    st.header(f"🔍 因子分析（{n_factors}个因子）")
    try:
        fa = FactorAnalysis(n_components=n_factors, random_state=42, max_iter=2000)
        fa.fit_transform(data_scaled)
        loadings = fa.components_.T
        st.success("✅ 因子分析完成")
    except (ValueError, np.linalg.LinAlgError) as e:
        st.error(f"因子分析出错：{e}")
        return

    # 载荷矩阵
    st.subheader("📋 因子载荷矩阵")
    loadings_df = pd.DataFrame(
        loadings.round(3),
        index=data.columns,
        columns=[f'因子{i + 1}' for i in range(n_factors)]
    )
    st.dataframe(loadings_df, use_container_width=True)

    # 热力图
    st.subheader("🔥 因子载荷热力图")
    fig3, ax3 = plt.subplots(figsize=(10, 8))
    im = ax3.imshow(loadings, cmap='RdBu', aspect='auto')
    plt.colorbar(im, ax=ax3)
    ax3.set_yticks(range(len(data.columns)))
    ax3.set_yticklabels(data.columns, fontsize=8)
    ax3.set_xticks(range(n_factors))
    ax3.set_xticklabels([f'因子{i + 1}' for i in range(n_factors)])
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
    st.success("🎉 因子分析全部完成！")


# ---------------------- 页面路由 ----------------------
if st.session_state.page == "🌡 温度趋势分析":
    page_temperature_trend()
elif st.session_state.page == "📈 多年对比分析":
    page_yearly_comparison()
elif st.session_state.page == "🔬 因子分析":
    page_factor_analysis()

# 侧边栏底部说明
st.sidebar.markdown("---")
st.sidebar.info(
    """
    📌 **数据说明**
    - 数据来源：大兴安岭站气象观测
    - 时间范围：2013-2017年
    - 数据频率：30分钟

    📂 **需要的文件**
    - 2013-2017年气象CSV文件
    - 文件需包含'年','月','日','时','分','秒','近地面空气温度'等列
    """
)
