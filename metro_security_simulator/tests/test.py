"""
深度诊断脚本 - 查找PA1时间异常的根本原因

现象：
- PW1基本时间正确：15.5s ✅
- PW1单服务器约束正确：每步1人 ✅
- 但PA1总时间只有26.79s ❌（应该是144s）

可能原因：
1. 附加时间计算有问题（step_G）
2. 时间累加逻辑有问题
3. 乘客对象的时间字段被覆盖
"""

import sys
import os
import pandas as pd

# 添加src到路径
project_root = r'C:\Users\chang\PycharmProjects\metro_security_simulator'
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import SystemParameters
from src.transit_time import compute_t_PW1_basic

params = SystemParameters()

print("=" * 70)
print("深度诊断：PA1时间异常分析")
print("=" * 70)

# 读取Group5的乘客数据
passenger_file = os.path.join(project_root, 'outputs', 'data',
                              'Group5_Situation5_passengers.csv')

if not os.path.exists(passenger_file):
    print(f"\n❌ 文件不存在: {passenger_file}")
    print("请先运行 python main.py")
    sys.exit(1)

df = pd.read_csv(passenger_file)

# 分析PA1乘客
pa1 = df[df['ptype'] == 'PA1'].copy()

print(f"\n1. PA1乘客统计:")
print(f"   总数: {len(pa1)}")
print(f"   平均总时间: {pa1['t_total'].mean():.2f}s")

print(f"\n2. PA1时间组成分析:")
print(f"   SA1基本时间平均: {pa1['t_SA1_basic'].mean():.2f}s")
print(f"   SA1附加时间平均: {pa1['t_SA1_add'].mean():.2f}s")
print(f"   PW基本时间平均: {pa1['t_PW_basic'].mean():.2f}s")
print(f"   PW附加时间平均: {pa1['t_SA2_add'].mean():.2f}s")
print(f"   SA3基本时间平均: {pa1['t_SA3_basic'].mean():.2f}s")
print(f"   SA3附加时间平均: {pa1['t_SA3_add'].mean():.2f}s")

# 验证PW基本时间
t_pw1_expected = compute_t_PW1_basic(params)
t_pw1_actual = pa1['t_PW_basic'].mean()

print(f"\n3. 🔴 关键检查：PW1基本时间")
print(f"   期望值: {t_pw1_expected:.2f}s")
print(f"   实际值: {t_pw1_actual:.2f}s")
print(f"   状态: {'✅ 正确' if abs(t_pw1_actual - t_pw1_expected) < 0.1 else '❌ 错误'}")

if abs(t_pw1_actual - t_pw1_expected) >= 0.1:
    print(f"\n   ⚠️ 警告：PW基本时间不正确！")
    print(f"   这说明compute_t_PW1_basic()的值没有被正确使用")

# 检查各部分时间占比
print(f"\n4. 时间占比分析:")
total_avg = pa1['t_total'].mean()
print(f"   SA1基本: {pa1['t_SA1_basic'].mean() / total_avg * 100:.1f}%")
print(f"   SA1附加: {pa1['t_SA1_add'].mean() / total_avg * 100:.1f}%")
print(f"   PW基本:  {pa1['t_PW_basic'].mean() / total_avg * 100:.1f}%")
print(f"   PW附加:  {pa1['t_SA2_add'].mean() / total_avg * 100:.1f}%")
print(f"   SA3基本: {pa1['t_SA3_basic'].mean() / total_avg * 100:.1f}%")
print(f"   SA3附加: {pa1['t_SA3_add'].mean() / total_avg * 100:.1f}%")

# 检查PW附加时间（排队时间）
print(f"\n5. 🔴 关键检查：PW附加时间（排队时间）")
print(f"   最小值: {pa1['t_SA2_add'].min():.2f}s")
print(f"   平均值: {pa1['t_SA2_add'].mean():.2f}s")
print(f"   最大值: {pa1['t_SA2_add'].max():.2f}s")

if pa1['t_SA2_add'].mean() < 10:
    print(f"   ❌ 错误！排队时间太短")
    print(f"   单服务器约束下，应该有大量排队")
    print(f"   Group5预期排队时间应该约128s")

# 检查SA1附加时间
print(f"\n6. SA1附加时间检查:")
print(f"   最小值: {pa1['t_SA1_add'].min():.2f}s")
print(f"   平均值: {pa1['t_SA1_add'].mean():.2f}s")
print(f"   最大值: {pa1['t_SA1_add'].max():.2f}s")

# 抽样检查前10个PA1
print(f"\n7. 前10个PA1详细数据:")
print(pa1.head(10)[['index', 't_SA1_basic', 't_SA1_add', 't_PW_basic',
                    't_SA2_add', 't_SA3_basic', 't_SA3_add', 't_total']].to_string(index=False))

# 抽样检查后10个PA1
print(f"\n8. 后10个PA1详细数据:")
print(pa1.tail(10)[['index', 't_SA1_basic', 't_SA1_add', 't_PW_basic',
                    't_SA2_add', 't_SA3_basic', 't_SA3_add', 't_total']].to_string(index=False))

# 时间序列分析
timeseries_file = os.path.join(project_root, 'outputs', 'data',
                               'Group5_Situation5_timeseries.csv')

if os.path.exists(timeseries_file):
    ts = pd.read_csv(timeseries_file)

    print(f"\n9. 时间序列分析:")
    print(f"   总步数: {len(ts)}")
    print(f"   仿真时间: {ts['T'].max():.1f}s")

    # PW1队列长度分析
    print(f"\n10. PW1队列长度:")
    print(f"   峰值: {ts['D_PW1'].max()}")
    print(f"   平均: {ts['D_PW1'].mean():.1f}")

    if ts['D_PW1'].max() < 50:
        print(f"   ❌ 错误！PW1队列太短")
        print(f"   单服务器约束下，应该有大量排队")

# 总结
print(f"\n" + "=" * 70)
print("诊断总结:")
print("=" * 70)

issues = []

if abs(t_pw1_actual - t_pw1_expected) >= 0.1:
    issues.append("PW1基本时间未被正确使用")

if pa1['t_SA2_add'].mean() < 10:
    issues.append("PW附加时间（排队）太短")

if len(issues) == 0:
    print("⚠️ 所有时间字段看起来都正常，但总时间仍然太短")
    print("可能的原因：")
    print("  1. 时间累加公式错误")
    print("  2. 某个字段被覆盖")
    print("  3. 仿真逻辑有其他问题")
else:
    print("🔴 发现以下问题:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

print("=" * 70)

