import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import dates as mdates  # noqa
import os

# ====================== 全局设置 ======================
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

colors = {
    "春季": "#2ECC71",
    "夏季": "#E74C3C",
    "秋季": "#F39C12",
    "冬季": "#3498DB"
}


def get_season(m):
    """根据月份返回季节"""
    if 3 <= m <= 5:
        return "春季"
    elif 6 <= m <= 8:
        return "夏季"
    elif 9 <= m <= 11:
        return "秋季"
    else:
        return "冬季"


def read_and_process(file_path, year):
    """读取并处理单年数据"""
    print(f"\n处理 {year} 年数据...")
    print(f"文件: {file_path}")

    # 读取CSV，跳过第2行（单位行）
    df = pd.read_csv(file_path, skiprows=[1], encoding='utf-8')

    # 检查是否有'年'列
    if '年' not in df.columns:
        print(f"  错误：{year}年文件没有'年'列")
        return None

    # 筛选指定年份
    df = df[df['年'] == year]
    if len(df) == 0:
        print(f"  错误：{year}年文件中没有{year}年的数据")
        return None

    # 构建时间列
    df['时间'] = pd.to_datetime(
        df['年'].astype(str) + '-' +
        df['月'].astype(str) + '-' +
        df['日'].astype(str) + ' ' +
        df['时'].astype(str) + ':' +
        df['分'].astype(str) + ':' +
        df['秒'].astype(str),
        errors='coerce'
    )

    # 选择温度列（优先使用近地面空气温度）
    temp_col = '近地面空气温度' if '近地面空气温度' in df.columns else None
    if temp_col is None:
        for col in df.columns:
            if '温度' in col:
                temp_col = col
                break

    if temp_col is None:
        print(f"  错误：{year}年文件找不到温度列")
        return None

    print(f"  使用温度列: {temp_col}")

    df['温度'] = pd.to_numeric(df[temp_col], errors='coerce')
    df = df.dropna(subset=['时间', '温度'])

    if len(df) == 0:
        print(f"  错误：{year}年没有有效温度数据")
        return None

    # 计算每日极值
    df['日期'] = df['时间'].dt.date
    daily = df.groupby('日期').agg(
        最高气温=('温度', 'max'),
        最低气温=('温度', 'min')
    ).reset_index()

    daily['日期'] = pd.to_datetime(daily['日期'])
    daily['月份'] = daily['日期'].dt.month
    daily['季节'] = daily['月份'].apply(get_season)

    # 月平均温度
    monthly_avg = df.groupby(df['时间'].dt.to_period('M')).agg(月均温=('温度', 'mean'))
    monthly_avg['日期'] = monthly_avg.index.to_timestamp()

    # 统计极值
    max_t = daily.loc[daily['最高气温'].idxmax()]
    min_t = daily.loc[daily['最低气温'].idxmin()]

    stats = {
        'year': year,
        'df': df,
        'daily': daily,
        'monthly_avg': monthly_avg,
        'max_temp': max_t['最高气温'],
        'max_date': max_t['日期'],
        'min_temp': min_t['最低气温'],
        'min_date': min_t['日期'],
        'avg_temp': df['温度'].mean(),
        'data_count': len(df)
    }

    return stats


def plot_single_year(stats, output_dir):
    """绘制单年气温图"""
    year = stats['year']
    daily = stats['daily']
    monthly_avg = stats['monthly_avg']
    max_temp = stats['max_temp']
    max_date = stats['max_date']
    min_temp = stats['min_temp']
    min_date = stats['min_date']

    fig, ax = plt.subplots(figsize=(16, 8), dpi=100)

    # 绘制气温曲线
    for season, data in daily.groupby("季节"):
        ax.plot(data["日期"], data["最高气温"],
                c=colors[season], lw=2, label=f"{season}最高温")
        ax.plot(data["日期"], data["最低气温"],
                c=colors[season], linestyle="--", lw=2, label=f"{season}最低温")

    # 标注极值点
    ax.annotate(
        f"最高 {max_temp:.1f}℃",
        xy=(max_date, max_temp),
        xytext=(10, 10), textcoords='offset points',
        color="red", weight="bold", fontsize=10,
        arrowprops=dict(arrowstyle="->", color="red", lw=1.5)
    )

    ax.annotate(
        f"最低 {min_temp:.1f}℃",
        xy=(min_date, min_temp),
        xytext=(10, -15), textcoords='offset points',
        color="blue", weight="bold", fontsize=10,
        arrowprops=dict(arrowstyle="->", color="blue", lw=1.5)
    )

    # 添加月均温曲线
    ax.plot(monthly_avg["日期"], monthly_avg["月均温"],
            'k-', lw=2, alpha=0.6, label="月均温")

    # 图表美化
    ax.set_title(f"{year}年大兴安岭气温变化图", fontsize=16, weight="bold", pad=20)
    ax.set_xlabel("日期", fontsize=12)
    ax.set_ylabel("温度 (℃)", fontsize=12)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.grid(alpha=0.3, linestyle='--', linewidth=0.5)
    ax.legend(ncol=3, fontsize=9, loc='upper left')

    # 添加季节背景色
    for season, color in colors.items():
        season_data = daily[daily['季节'] == season]
        if not season_data.empty:
            start = season_data['日期'].iloc[0]
            end = season_data['日期'].iloc[-1]
            ax.axvspan(start, end, alpha=0.08, color=color)

    plt.tight_layout()

    # 保存图片
    output_path = os.path.join(output_dir, f"{year}年大兴安岭气温变化图.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  图片已保存: {output_path}")


def plot_yearly_comparison(all_stats, output_dir):
    """绘制多年对比图"""
    if len(all_stats) == 0:
        return

    fig, axes = plt.subplots(2, 1, figsize=(16, 12), dpi=100)

    # 图1：多年最高温和最低温对比（柱状图）
    years = [s['year'] for s in all_stats]
    max_temps = [s['max_temp'] for s in all_stats]
    min_temps = [s['min_temp'] for s in all_stats]
    avg_temps = [s['avg_temp'] for s in all_stats]

    ax1 = axes[0]
    x = range(len(years))
    width = 0.25

    bars1 = ax1.bar([i - width for i in x], max_temps, width, label='最高温', color='red', alpha=0.7)
    bars2 = ax1.bar(x, avg_temps, width, label='平均温', color='green', alpha=0.7)
    bars3 = ax1.bar([i + width for i in x], min_temps, width, label='最低温', color='blue', alpha=0.7)

    # 在柱子上标注数值
    for bar in bars1:
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=9)
    for bar in bars3:
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 2,
                 f'{bar.get_height():.1f}', ha='center', va='top', fontsize=9, color='white')

    ax1.set_xlabel('年份', fontsize=12)
    ax1.set_ylabel('温度 (℃)', fontsize=12)
    ax1.set_title('2013-2017年大兴安岭气温对比（最高/平均/最低）', fontsize=14, weight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(years)
    ax1.legend(loc='upper right')
    ax1.grid(alpha=0.3, axis='y')

    # 图2：多年气温变化趋势（折线图）
    ax2 = axes[1]
    ax2.plot(years, max_temps, 'ro-', linewidth=2, markersize=8, label='最高温')
    ax2.plot(years, avg_temps, 'go-', linewidth=2, markersize=8, label='平均温')
    ax2.plot(years, min_temps, 'bo-', linewidth=2, markersize=8, label='最低温')

    # 标注数值
    for i, (y, max_t, avg_t, min_t) in enumerate(zip(years, max_temps, avg_temps, min_temps)):
        ax2.annotate(f'{max_t:.1f}', (y, max_t), xytext=(0, 10), textcoords='offset points', ha='center')
        ax2.annotate(f'{avg_t:.1f}', (y, avg_t), xytext=(0, 10), textcoords='offset points', ha='center')
        ax2.annotate(f'{min_t:.1f}', (y, min_t), xytext=(0, -15), textcoords='offset points', ha='center')

    ax2.set_xlabel('年份', fontsize=12)
    ax2.set_ylabel('温度 (℃)', fontsize=12)
    ax2.set_title('2013-2017年大兴安岭气温变化趋势', fontsize=14, weight='bold')
    ax2.legend(loc='best')
    ax2.grid(alpha=0.3)
    ax2.set_xticks(years)

    plt.tight_layout()

    # 保存对比图
    output_path = os.path.join(output_dir, "2013-2017年大兴安岭气温对比图.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\n对比图已保存: {output_path}")


def print_statistics(all_stats):
    """打印统计信息"""
    print("\n" + "=" * 80)
    print("2013-2017年大兴安岭气温统计汇总")
    print("=" * 80)

    # 创建DataFrame显示统计结果
    stats_df = pd.DataFrame([{
        '年份': s['year'],
        '最高温(℃)': round(s['max_temp'], 1),
        '最高温日期': s['max_date'].strftime('%Y-%m-%d'),
        '最低温(℃)': round(s['min_temp'], 1),
        '最低温日期': s['min_date'].strftime('%Y-%m-%d'),
        '年均温(℃)': round(s['avg_temp'], 1),
        '数据量(条)': s['data_count']
    } for s in all_stats])

    print(stats_df.to_string(index=False))

    # 找出极端年份
    max_year = stats_df.loc[stats_df['最高温(℃)'].idxmax(), '年份']
    min_year = stats_df.loc[stats_df['最低温(℃)'].idxmin(), '年份']
    avg_max_year = stats_df.loc[stats_df['年均温(℃)'].idxmax(), '年份']
    avg_min_year = stats_df.loc[stats_df['年均温(℃)'].idxmin(), '年份']

    print("\n" + "=" * 80)
    print("极端年份统计")
    print("=" * 80)
    print(f"最高温极值年份: {max_year}年 ({stats_df['最高温(℃)'].max():.1f}℃)")
    print(f"最低温极值年份: {min_year}年 ({stats_df['最低温(℃)'].min():.1f}℃)")
    print(f"最暖年份: {avg_max_year}年 ({stats_df['年均温(℃)'].max():.1f}℃)")
    print(f"最冷年份: {avg_min_year}年 ({stats_df['年均温(℃)'].min():.1f}℃)")


# ====================== 主程序 ======================
def main():
    # 切换到脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"工作目录: {os.getcwd()}")

    # 查找所有CSV文件
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    print(f"\n找到的CSV文件: {csv_files}")

    # 处理2013-2017年数据
    years = [2013, 2014, 2015, 2016, 2017]
    all_stats = []

    for year in years:
        # 查找对应年份的文件
        file_path = None
        for f in csv_files:
            if str(year) in f and '气象' in f:
                file_path = f
                break

        if file_path is None:
            # 尝试不含'气象'关键词的
            for f in csv_files:
                if str(year) in f:
                    file_path = f
                    break

        if file_path is None:
            print(f"\n警告：找不到{year}年的数据文件，跳过")
            continue

        # 处理数据
        stats = read_and_process(file_path, year)
        if stats is not None:
            all_stats.append(stats)
            # 绘制单年图
            plot_single_year(stats, script_dir)

    if len(all_stats) == 0:
        print("\n错误：没有成功处理任何年份的数据！")
        return

    # 绘制多年对比图
    plot_yearly_comparison(all_stats, script_dir)

    # 打印统计信息
    print_statistics(all_stats)

    print("\n" + "=" * 80)
    print("全部完成！生成的图片:")
    print("  - 各年份单独的气温变化图 (5张)")
    print("  - 2013-2017年气温对比图 (1张)")
    print("=" * 80)


if __name__ == "__main__":
    main()
