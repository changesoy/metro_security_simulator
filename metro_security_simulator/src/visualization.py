"""
可视化模块：生成论文风格的图表
对应设计书：第7.1.2节动态演化曲线

主要功能：
- 绘制PW1排队长度曲线（对应论文Figure 4）
- 绘制PW2密度曲线（对应论文Figure 5）
- 绘制SA3密度曲线（对应论文Figure 6）
- 生成完整的对比报告
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import os
from typing import Optional, List

# 条件导入：支持两种运行方式
try:
    from src.data_structures import System
    from src.metrics import extract_time_series
except ModuleNotFoundError:
    from data_structures import System
    from metrics import extract_time_series

# 设置字体（使用标准英文字体避免上标符号问题）
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
mpl.rcParams['axes.unicode_minus'] = False


# ==================== 单图绘制函数 ====================

def plot_queue_length(system: System, save_path: Optional[str] = None,
                     show: bool = True, title_suffix: str = "") -> None:
    """绘制PW1排队长度曲线（对应论文Figure 4）

    Args:
        system: 系统对象（仿真完成后）
        save_path: 保存路径（如果提供）
        show: 是否显示图表
        title_suffix: 标题后缀（如"Group 1"）

    Note:
        - PW1是主要瓶颈
        - 排队长度反映安检设备处理能力
    """
    df = extract_time_series(system)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(df['T'], df['D_PW1'], linewidth=2, color='#1f77b4', label='PW1 Queue Length')

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Number of Passengers', fontsize=12)
    ax.set_title(f'PW1 Queue Length vs Time {title_suffix}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=11)

    # 添加峰值标注
    peak_idx = df['D_PW1'].idxmax()
    peak_val = df.loc[peak_idx, 'D_PW1']
    peak_time = df.loc[peak_idx, 'T']
    ax.plot(peak_time, peak_val, 'ro', markersize=8)
    ax.annotate(f'Peak: {peak_val:.0f}',
               xy=(peak_time, peak_val),
               xytext=(10, 10), textcoords='offset points',
               fontsize=10, color='red',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  图表已保存: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def plot_PW2_density(system: System, save_path: Optional[str] = None,
                    show: bool = True, title_suffix: str = "") -> None:
    """绘制PW2密度曲线（对应论文Figure 5）

    Args:
        system: 系统对象（仿真完成后）
        save_path: 保存路径（如果提供）
        show: 是否显示图表
        title_suffix: 标题后缀

    Note:
        - 密度影响行走速度
        - 体现快速通道的通畅程度
    """
    df = extract_time_series(system)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(df['T'], df['K_PW2'], linewidth=2, color='#ff7f0e', label='PW2 Density')

    # 添加阈值线
    ax.axhline(y=system.params.K_PW2_init, color='g', linestyle='--',
              linewidth=1.5, alpha=0.7, label=f'Threshold ({system.params.K_PW2_init} ped/m²)')
    ax.axhline(y=system.params.K_PW2_max, color='r', linestyle='--',
              linewidth=1.5, alpha=0.7, label=f'Max ({system.params.K_PW2_max} ped/m²)')

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Density (ped/m²)', fontsize=12)
    ax.set_title(f'PW2 Density vs Time {title_suffix}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=11)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  图表已保存: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def plot_SA3_density(system: System, save_path: Optional[str] = None,
                    show: bool = True, title_suffix: str = "") -> None:
    """绘制SA3密度曲线（对应论文Figure 6）

    Args:
        system: 系统对象（仿真完成后）
        save_path: 保存路径（如果提供）
        show: 是否显示图表
        title_suffix: 标题后缀

    Note:
        - SA3是检票前汇集区
        - 密度反映闸机前的拥堵程度
    """
    df = extract_time_series(system)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(df['T'], df['K_SA3'], linewidth=2, color='#2ca02c', label='SA3 Density')

    # 添加阈值线
    ax.axhline(y=system.params.K_SA3_init, color='g', linestyle='--',
              linewidth=1.5, alpha=0.7, label=f'Threshold ({system.params.K_SA3_init} ped/m²)')
    ax.axhline(y=system.params.K_SA3_max, color='r', linestyle='--',
              linewidth=1.5, alpha=0.7, label=f'Max ({system.params.K_SA3_max} ped/m²)')

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Density (ped/m²)', fontsize=12)
    ax.set_title(f'SA3 Density vs Time {title_suffix}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=11)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  图表已保存: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


# ==================== 综合绘图函数 ====================

def plot_all_metrics(system: System, group_name: str = "Experiment",
                    save_dir: Optional[str] = None, show: bool = True) -> None:
    """绘制所有关键指标（3张图）

    Args:
        system: 系统对象（仿真完成后）
        group_name: 实验组名称
        save_dir: 保存目录（如果提供）
        show: 是否显示图表

    Note:
        生成3张图：
        1. PW1排队长度
        2. PW2密度
        3. SA3密度
    """
    print(f"\n生成 {group_name} 的可视化结果...")

    # 创建保存目录
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 图1：PW1排队长度
    save_path_1 = os.path.join(save_dir, f'{group_name}_PW1_queue.png') if save_dir else None
    plot_queue_length(system, save_path=save_path_1, show=show, title_suffix=f"({group_name})")

    # 图2：PW2密度
    save_path_2 = os.path.join(save_dir, f'{group_name}_PW2_density.png') if save_dir else None
    plot_PW2_density(system, save_path=save_path_2, show=show, title_suffix=f"({group_name})")

    # 图3：SA3密度
    save_path_3 = os.path.join(save_dir, f'{group_name}_SA3_density.png') if save_dir else None
    plot_SA3_density(system, save_path=save_path_3, show=show, title_suffix=f"({group_name})")

    print(f"  ✓ {group_name} 可视化完成")


def plot_comparison(systems: List[System], group_names: List[str],
                   metric: str = 'D_PW1', save_path: Optional[str] = None,
                   show: bool = True) -> None:
    """绘制多个实验组的对比图

    Args:
        systems: 系统对象列表
        group_names: 实验组名称列表
        metric: 要对比的指标（'D_PW1', 'K_PW2', 'K_SA3', 'D_pass'等）
        save_path: 保存路径
        show: 是否显示图表
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    for i, (system, name) in enumerate(zip(systems, group_names)):
        df = extract_time_series(system)
        color = colors[i % len(colors)]
        ax.plot(df['T'], df[metric], linewidth=2, color=color, label=name, alpha=0.8)

    # 设置标签
    metric_labels = {
        'D_PW1': ('PW1 Queue Length', 'Number of Passengers'),
        'D_SA3': ('SA3 Queue', 'Number of Passengers'),
        'K_PW2': ('PW2 Density', 'Density (ped/m²)'),
        'K_SA3': ('SA3 Density', 'Density (ped/m²)'),
        'D_pass': ('Passed Passengers', 'Number of Passengers')
    }

    title, ylabel = metric_labels.get(metric, (metric, 'Value'))

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(f'{title} Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=11)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  对比图已保存: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def plot_time_breakdown(system: System, save_path: Optional[str] = None,
                       show: bool = True) -> None:
    """绘制时间分解柱状图

    Args:
        system: 系统对象（仿真完成后）
        save_path: 保存路径
        show: 是否显示图表
    """
    from metrics import compute_time_breakdown

    breakdown = compute_time_breakdown(system)

    # 准备数据
    categories = ['SA1', 'PW', 'SA3']

    PA1_basic = [breakdown['PA1']['basic_SA1'],
                breakdown['PA1']['basic_PW'],
                breakdown['PA1']['basic_SA3']]
    PA1_add = [breakdown['PA1']['add_SA1'],
              breakdown['PA1']['add_SA2'],
              breakdown['PA1']['add_SA3']]

    PA2_basic = [breakdown['PA2']['basic_SA1'],
                breakdown['PA2']['basic_PW'],
                breakdown['PA2']['basic_SA3']]
    PA2_add = [breakdown['PA2']['add_SA1'],
              breakdown['PA2']['add_SA2'],
              breakdown['PA2']['add_SA3']]

    # 绘图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    x = range(len(categories))
    width = 0.35

    # PA1
    ax1.bar(x, PA1_basic, width, label='Basic Time', color='#1f77b4')
    ax1.bar(x, PA1_add, width, bottom=PA1_basic, label='Additional Time', color='#ff7f0e')
    ax1.set_xlabel('Zone', fontsize=12)
    ax1.set_ylabel('Time (s)', fontsize=12)
    ax1.set_title('PA1 Time Breakdown', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # PA2
    ax2.bar(x, PA2_basic, width, label='Basic Time', color='#2ca02c')
    ax2.bar(x, PA2_add, width, bottom=PA2_basic, label='Additional Time', color='#d62728')
    ax2.set_xlabel('Zone', fontsize=12)
    ax2.set_ylabel('Time (s)', fontsize=12)
    ax2.set_title('PA2 Time Breakdown', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  时间分解图已保存: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


# ==================== 模块测试函数 ====================

if __name__ == "__main__":
    """模块自测：验证可视化功能"""

    # 自测时的导入
    import sys
    import os
    if 'src' not in sys.path[0]:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import SystemParameters
    from data_structures import System
    from simulation_engine import simulation_step, run_simulation

    print("=" * 70)
    print("可视化模块自测")
    print("=" * 70)

    # 创建测试系统并运行仿真
    print("\n[准备] 运行中等规模仿真...")
    params = SystemParameters()
    system = System(params=params)

    # 允许约150个乘客到达（10秒内，q_PA1=7.5, q_PA2=7.5 → 每秒15人）
    for i in range(100):  # 100步 = 10秒
        simulation_step(system, q_PA1=7.5, q_PA2=7.5)

    # 运行直到所有人通过
    run_simulation(system, q_PA1=0.0, q_PA2=0.0, max_time=300.0, verbose=False)

    print(f"  仿真完成: {system.D_All} 个乘客通过系统")

    # 测试1：绘制PW1排队长度
    print("\n[测试1] 绘制PW1排队长度曲线")
    plot_queue_length(system, show=False, title_suffix="(Test)")
    print("  ✓ 通过")

    # 测试2：绘制PW2密度
    print("\n[测试2] 绘制PW2密度曲线")
    plot_PW2_density(system, show=False, title_suffix="(Test)")
    print("  ✓ 通过")

    # 测试3：绘制SA3密度
    print("\n[测试3] 绘制SA3密度曲线")
    plot_SA3_density(system, show=False, title_suffix="(Test)")
    print("  ✓ 通过")

    # 测试4：绘制时间分解
    print("\n[测试4] 绘制时间分解图")
    plot_time_breakdown(system, show=False)
    print("  ✓ 通过")

    # 测试5：绘制所有指标（保存到指定目录）
    print("\n[测试5] 绘制所有指标")
    output_dir = r"C:\Users\chang\PycharmProjects\metro_security_simulator\outputs\figures"
    plot_all_metrics(system, group_name="Test", save_dir=output_dir, show=False)

    # 检查文件是否生成
    expected_files = ['Test_PW1_queue.png', 'Test_PW2_density.png', 'Test_SA3_density.png']
    for fname in expected_files:
        fpath = os.path.join(output_dir, fname)
        assert os.path.exists(fpath), f"文件未生成: {fname}"
    print(f"  文件已生成到: {output_dir}")
    print("  ✓ 通过")

    print("\n" + "=" * 70)
    print("所有测试通过！可视化功能正常。")
    print("=" * 70)

    # 设置输出目录
    output_dir = r"C:\Users\chang\PycharmProjects\metro_security_simulator\outputs\figures"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"\n提示：运行主程序时将自动生成可视化结果并保存到 {output_dir}")
