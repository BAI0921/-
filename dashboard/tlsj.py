import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 查看可用的样式（可选，用于调试）
# print("可用的样式:", plt.style.available)

# 使用默认样式，不指定特定样式
# 或者使用以下任一可用样式：
# plt.style.use('default')
# plt.style.use('ggplot')
# plt.style.use('seaborn-v0_8')  # 如果seaborn已安装

# 读取数据
file_path = r'C:\111\csv_output通量数据\2017年大兴安岭通量30分钟数据.csv'
df = pd.read_csv(file_path, header=0, skiprows=[1], encoding='utf-8-sig')

# 创建时间列
df['datetime'] = pd.to_datetime(df[['年', '月', '日', '时', '分']].rename(
    columns={'年': 'year', '月': 'month', '日': 'day', '时': 'hour', '分': 'minute'}
))

# 处理NAN值
df = df.replace('NAN', np.nan)

# 将数值列转换为浮点数
flux_cols = ['NEE', 'RE', 'GPP', 'LE', 'Hs']
for col in flux_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 创建多个子图
fig, axes = plt.subplots(3, 2, figsize=(16, 12))
fig.suptitle('2017年大兴安岭站通量数据变化趋势', fontsize=16, fontweight='bold')

# 1. NEE (净生态系统交换量)
ax1 = axes[0, 0]
ax1.plot(df['datetime'], df['NEE'], 'b-', linewidth=0.8, alpha=0.7)
ax1.set_xlabel('日期', fontsize=10)
ax1.set_ylabel('NEE (mg CO₂ m⁻² s⁻¹)', fontsize=10)
ax1.set_title('NEE - 净生态系统交换量（碳通量）', fontsize=12)
ax1.grid(True, alpha=0.3)

# 2. RE (生态系统呼吸)
ax2 = axes[0, 1]
ax2.plot(df['datetime'], df['RE'], 'r-', linewidth=0.8, alpha=0.7)
ax2.set_xlabel('日期', fontsize=10)
ax2.set_ylabel('RE (mg CO₂ m⁻² s⁻¹)', fontsize=10)
ax2.set_title('RE - 生态系统呼吸（碳通量）', fontsize=12)
ax2.grid(True, alpha=0.3)

# 3. GPP (总初级生产力)
ax3 = axes[1, 0]
ax3.plot(df['datetime'], df['GPP'], 'g-', linewidth=0.8, alpha=0.7)
ax3.set_xlabel('日期', fontsize=10)
ax3.set_ylabel('GPP (mg CO₂ m⁻² s⁻¹)', fontsize=10)
ax3.set_title('GPP - 总初级生产力（碳通量）', fontsize=12)
ax3.grid(True, alpha=0.3)

# 4. LE (潜热通量)
ax4 = axes[1, 1]
ax4.plot(df['datetime'], df['LE'], 'm-', linewidth=0.8, alpha=0.7)
ax4.set_xlabel('日期', fontsize=10)
ax4.set_ylabel('LE (W m⁻²)', fontsize=10)
ax4.set_title('LE - 潜热通量（能量通量）', fontsize=12)
ax4.grid(True, alpha=0.3)

# 5. Hs (显热通量)
ax5 = axes[2, 0]
ax5.plot(df['datetime'], df['Hs'], 'c-', linewidth=0.8, alpha=0.7)
ax5.set_xlabel('日期', fontsize=10)
ax5.set_ylabel('Hs (W m⁻²)', fontsize=10)
ax5.set_title('Hs - 显热通量（能量通量）', fontsize=12)
ax5.grid(True, alpha=0.3)

# 6. 碳通量对比图
ax6 = axes[2, 1]
ax6.plot(df['datetime'], df['NEE'], 'b-', linewidth=0.6, alpha=0.6, label='NEE (净交换)')
ax6.plot(df['datetime'], df['RE'], 'r-', linewidth=0.6, alpha=0.6, label='RE (呼吸)')
ax6.plot(df['datetime'], df['GPP'], 'g-', linewidth=0.6, alpha=0.6, label='GPP (总生产)')
ax6.set_xlabel('日期', fontsize=10)
ax6.set_ylabel('碳通量 (mg CO₂ m⁻² s⁻¹)', fontsize=10)
ax6.set_title('碳通量对比 (NEE, RE, GPP)', fontsize=12)
ax6.legend(loc='upper right', fontsize=9)
ax6.grid(True, alpha=0.3)

# 调整布局
plt.tight_layout()
plt.subplots_adjust(top=0.95)

# 保存图片
plt.savefig('2017年大兴安岭站通量数据变化图.png', dpi=300, bbox_inches='tight')
plt.show()

# 打印基本统计信息
print("=" * 60)
print("通量数据统计信息")
print("=" * 60)
print(f"数据时间范围: {df['datetime'].min()} 至 {df['datetime'].max()}")
print(f"总数据点数: {len(df)}")
print("\n各通量变量统计信息:")
for col in flux_cols:
    print(f"\n{col}:")
    print(f"  有效数据点数: {df[col].count()}")
    print(f"  平均值: {df[col].mean():.4f}")
    print(f"  标准差: {df[col].std():.4f}")
    print(f"  最小值: {df[col].min():.4f}")
    print(f"  最大值: {df[col].max():.4f}")