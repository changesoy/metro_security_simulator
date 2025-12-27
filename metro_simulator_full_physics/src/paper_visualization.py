"""
论文风格可视化模块

生成与论文匹配的高质量图表（全英文标注）：
- Figure 4: PW1排队柱状图
- Figure 5: PW2密度对比（连续 vs 脉冲）
- Figure 6: SA3密度箱线图对比

所有标注使用英文，避免中文字体问题
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from typing import Dict, List, Tuple, Optional
import os

from src.config import SystemParameters, PassengerType, Position
from src.data_structures import SystemState


# ==================== 图表样式配置 ====================
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'legend.fontsize': 9,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
})

# 颜色方案 - 5组用5种不同颜色
COLORS_5 = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
# 线型方案 - 用于对比图中区分5个组
LINE_STYLES_5 = ['-', '--', '-.', ':', (0, (3, 1, 1, 1))]
MARKERS = ['o', 's', '^', 'D', 'v']

# 兼容旧代码
COLORS_CONTINUOUS = COLORS_5
COLORS_PULSED = COLORS_5
LINE_STYLES = LINE_STYLES_5


def plot_queue_pw1_single_mode(states: List[Tuple[str, SystemState]], 
                                mode_name: str = "Continuous",
                                save_path: Optional[str] = None):
    """
    绘制单一模式下的PW1队列长度对比图（5组5色）
    
    Args:
        states: [(group_name, state), ...] 列表
        mode_name: 模式名称（用于标题）
        save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for i, (name, state) in enumerate(states):
        T = state.history['T']
        queue = state.history['queue_PW1']
        color = COLORS_5[i % len(COLORS_5)]
        ax.plot(T, queue, color=color, linewidth=1.5, label=name)
    
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Number of Passengers')
    ax.set_title(f'PW1 Queue Length - {mode_name} Arrival')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(0, None)
    ax.set_ylim(0, None)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"  Saved: {save_path}")
    
    plt.close()
    return fig


def plot_queue_pw1_comparison(continuous_states: List[Tuple[str, SystemState]],
                               discontinuous_states: List[Tuple[str, SystemState]],
                               save_path: Optional[str] = None):
    """
    绘制两种模式的PW1队列长度对比图
    
    连续到达：蓝色系，5种线型区分组别
    间隔到达：红色系，5种线型区分组别
    
    Args:
        continuous_states: 连续到达的状态列表
        discontinuous_states: 间隔到达的状态列表
        save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # 蓝色系（连续到达）
    blue_color = '#1f77b4'
    # 红色系（间隔到达）
    red_color = '#d62728'
    
    # 绘制连续到达（蓝色，不同线型）
    for i, (name, state) in enumerate(continuous_states):
        T = state.history['T']
        queue = state.history['queue_PW1']
        linestyle = LINE_STYLES_5[i % len(LINE_STYLES_5)]
        # 提取组号用于图例
        group_num = name.replace('Group', '').strip()
        ax.plot(T, queue, color=blue_color, linestyle=linestyle, 
                linewidth=1.5, label=f'Cont. G{group_num}', alpha=0.9)
    
    # 绘制间隔到达（红色，不同线型）
    for i, (name, state) in enumerate(discontinuous_states):
        T = state.history['T']
        queue = state.history['queue_PW1']
        linestyle = LINE_STYLES_5[i % len(LINE_STYLES_5)]
        # 提取组号用于图例
        group_num = name.replace('Group', '').strip()
        ax.plot(T, queue, color=red_color, linestyle=linestyle,
                linewidth=1.5, label=f'Disc. G{group_num}', alpha=0.9)
    
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Number of Passengers')
    ax.set_title('PW1 Queue Length Comparison: Continuous (Blue) vs Discontinuous (Red)')
    
    # 分两列显示图例
    ax.legend(loc='upper right', ncol=2, fontsize=8)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(0, None)
    ax.set_ylim(0, None)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"  Saved: {save_path}")
    
    plt.close()
    return fig


def plot_queue_pw1_bar(state: SystemState, group_name: str = "Group 1",
                       save_path: Optional[str] = None):
    """
    Figure 4 风格: PW1入口排队人数柱状图
    
    显示SA1中等待进入安检通道(PW1)的乘客数量
    """
    history = state.history
    T = np.array(history['T'])
    queue = np.array(history['queue_PW1'])
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Bar chart
    ax.bar(T, queue, width=0.1, color='#5a7d9a', edgecolor='none', alpha=0.8,
           label=group_name)
    
    ax.set_xlabel('Time T [s]')
    ax.set_ylabel('Number of passengers queuing')
    ax.set_title('Queue Length at Passageway 1 Entrance')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(0, max(T) * 1.02)
    ax.set_ylim(0, max(queue) * 1.1 if max(queue) > 0 else 1)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"  Saved: {save_path}")
    
    plt.close()
    return fig


def plot_pw2_density_comparison(continuous_states: List[Tuple[str, SystemState]],
                                 pulsed_states: List[Tuple[str, SystemState]],
                                 save_path: Optional[str] = None):
    """
    Figure 5 风格: PW2密度对比图（连续到达 vs 脉冲到达）
    
    两个子图:
    (a) 连续到达 - Group 1-5
    (b) 脉冲到达 - Group 6-10
    """
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    
    # (a) Continuous arrival
    ax1 = axes[0]
    for i, (name, state) in enumerate(continuous_states):
        T = state.history['T']
        K = state.history['K_PW2']
        ax1.plot(T, K, linestyle=LINE_STYLES[i % len(LINE_STYLES)],
                 color=COLORS_CONTINUOUS[i % len(COLORS_CONTINUOUS)],
                 linewidth=1.5, label=name)
    
    ax1.set_xlabel('Time T [s]')
    ax1.set_ylabel('Passenger flow density of PW2 [ped/m²]')
    ax1.set_title('(a) The passenger flow is continuous')
    ax1.legend(loc='upper right', ncol=2)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xlim(0, 70)
    ax1.set_ylim(0, 2.5)
    
    # (b) Pulsed arrival
    ax2 = axes[1]
    for i, (name, state) in enumerate(pulsed_states):
        T = state.history['T']
        K = state.history['K_PW2']
        ax2.plot(T, K, linestyle=LINE_STYLES[i % len(LINE_STYLES)],
                 color=COLORS_PULSED[i % len(COLORS_PULSED)],
                 linewidth=1.5, label=name)
    
    ax2.set_xlabel('Time T [s]')
    ax2.set_ylabel('Passenger flow density of PW2 [ped/m²]')
    ax2.set_title('(b) The passenger flow is discontinuous')
    ax2.legend(loc='upper right', ncol=2)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xlim(0, 80)
    ax2.set_ylim(0, 2.5)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"  Saved: {save_path}")
    
    plt.close()
    return fig


def plot_sa3_density_boxplot(continuous_states: List[Tuple[str, SystemState]],
                              pulsed_states: List[Tuple[str, SystemState]],
                              save_path: Optional[str] = None):
    """
    Figure 6 风格: SA3密度箱线图对比
    
    并排两个子图:
    (a) 连续到达 - Group 1-5
    (b) 脉冲到达 - Group 6-10
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # 收集每组的密度数据
    continuous_data = []
    continuous_labels = []
    for name, state in continuous_states:
        K_SA3 = state.history['K_SA3']
        # 过滤掉零值（乘客到达前）
        K_SA3_nonzero = [k for k in K_SA3 if k > 0]
        continuous_data.append(K_SA3_nonzero if K_SA3_nonzero else [0])
        continuous_labels.append(name)
    
    pulsed_data = []
    pulsed_labels = []
    for name, state in pulsed_states:
        K_SA3 = state.history['K_SA3']
        K_SA3_nonzero = [k for k in K_SA3 if k > 0]
        pulsed_data.append(K_SA3_nonzero if K_SA3_nonzero else [0])
        pulsed_labels.append(name)
    
    # (a) Continuous arrival
    ax1 = axes[0]
    bp1 = ax1.boxplot(continuous_data, labels=continuous_labels, patch_artist=True)
    for patch, color in zip(bp1['boxes'], COLORS_CONTINUOUS):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax1.set_xlabel('Experiment Group')
    ax1.set_ylabel('Density of Subarea 3 [ped/m²]')
    ax1.set_title('(a) The passenger flow is continuous')
    ax1.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax1.set_ylim(0, 0.9)
    
    # (b) Pulsed arrival
    ax2 = axes[1]
    bp2 = ax2.boxplot(pulsed_data, labels=pulsed_labels, patch_artist=True)
    for patch, color in zip(bp2['boxes'], COLORS_PULSED):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax2.set_xlabel('Experiment Group')
    ax2.set_ylabel('Density of Subarea 3 [ped/m²]')
    ax2.set_title('(b) The passenger flow is discontinuous')
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.set_ylim(0, 0.9)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"  Saved: {save_path}")
    
    plt.close()
    return fig


def plot_congestion_evolution_english(state: SystemState, params: SystemParameters,
                                       title: str = "", save_path: Optional[str] = None):
    """
    拥堵演化图（4子图）- 英文标注
    
    子图1: 各区域人数随时间变化
    子图2: 密度演化（K_PW2, K_SA3）
    子图3: PW1入口排队长度
    子图4: 累计通过人数
    """
    history = state.history
    T = history['T']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Congestion Dynamics Analysis {title}', fontsize=14)
    
    # Subplot 1: Population in each area
    ax1 = axes[0, 0]
    ax1.plot(T, history['D_SA1'], label='SA1 (Entrance)', linewidth=1.5)
    ax1.plot(T, history['D_PW1'], label='PW1 (Security)', linewidth=1.5)
    ax1.plot(T, history['D_PW2'], label='PW2 (Fast Lane)', linewidth=1.5)
    ax1.plot(T, history['D_SA3'], label='SA3 (Gate Area)', linewidth=1.5)
    ax1.set_xlabel('Time [s]')
    ax1.set_ylabel('Number of Passengers')
    ax1.set_title('Population in Each Area')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: Density evolution
    ax2 = axes[0, 1]
    ax2.plot(T, history['K_PW2'], label='K_PW2', linewidth=1.5, color='orange')
    ax2.plot(T, history['K_SA3'], label='K_SA3', linewidth=1.5, color='green')
    ax2.axhline(y=params.K_PW2_init, color='orange', linestyle='--', alpha=0.5, 
                label=f'K_init={params.K_PW2_init}')
    ax2.axhline(y=params.K_PW2_max, color='red', linestyle='--', alpha=0.5, 
                label=f'K_max={params.K_PW2_max}')
    ax2.set_xlabel('Time [s]')
    ax2.set_ylabel('Density [ped/m²]')
    ax2.set_title('Density Evolution')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # Subplot 3: Queue at PW1
    ax3 = axes[1, 0]
    ax3.fill_between(T, 0, history['queue_PW1'], alpha=0.5, color='coral')
    ax3.plot(T, history['queue_PW1'], color='red', linewidth=1.5)
    ax3.set_xlabel('Time [s]')
    ax3.set_ylabel('Queue Length')
    ax3.set_title('Queue at PW1 Entrance')
    ax3.grid(True, alpha=0.3)
    
    # Subplot 4: Cumulative throughput
    ax4 = axes[1, 1]
    ax4.plot(T, history['D_pass'], linewidth=2, color='green')
    total_arrived = len(state.passengers)
    ax4.axhline(y=total_arrived, color='gray', linestyle='--', alpha=0.5, 
                label=f'Total arrived={total_arrived}')
    ax4.set_xlabel('Time [s]')
    ax4.set_ylabel('Cumulative Passengers Passed')
    ax4.set_title('System Throughput')
    ax4.legend(loc='lower right')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"  Saved: {save_path}")
    
    plt.close()
    return fig


def plot_time_decomposition_english(state: SystemState, title: str = "",
                                     save_path: Optional[str] = None):
    """
    时间分解图 - 英文标注
    
    左图: PA1（带行李）时间分解
    右图: PA2（无行李）时间分解
    蓝色: 基本时间（行走+服务）
    红色: 附加时间（排队延迟）
    """
    passed_PA1 = [p for p in state.passengers 
                  if p.position == Position.PASSED and p.ptype == PassengerType.PA1]
    passed_PA2 = [p for p in state.passengers 
                  if p.position == Position.PASSED and p.ptype == PassengerType.PA2]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'Transit Time Decomposition {title}', fontsize=14)
    
    # PA1 decomposition
    if passed_PA1:
        ax1 = axes[0]
        categories = ['SA1\nBasic', 'PW1\nBasic', 'SA3\nBasic', 
                      'SA1\nExtra', 'SA2\nExtra', 'SA3\nExtra']
        means = [
            np.mean([p.t_SA1_basic for p in passed_PA1]),
            np.mean([p.t_PW_basic for p in passed_PA1]),
            np.mean([p.t_SA3_basic for p in passed_PA1]),
            np.mean([p.t_SA1_add for p in passed_PA1]),
            np.mean([p.t_SA2_add for p in passed_PA1]),
            np.mean([p.t_SA3_add for p in passed_PA1])
        ]
        colors = ['steelblue', 'steelblue', 'steelblue', 'coral', 'coral', 'coral']
        
        bars = ax1.bar(categories, means, color=colors, edgecolor='black', alpha=0.8)
        ax1.set_ylabel('Average Time [s]')
        ax1.set_title(f'PA1 (With Luggage) Time Decomposition (n={len(passed_PA1)})')
        
        for bar, val in zip(bars, means):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                     f'{val:.1f}', ha='center', va='bottom', fontsize=9)
        
        total_basic = sum(means[:3])
        total_extra = sum(means[3:])
        ax1.text(0.02, 0.95, f'Basic: {total_basic:.1f}s\nExtra: {total_extra:.1f}s',
                 transform=ax1.transAxes, fontsize=10, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # PA2 decomposition
    if passed_PA2:
        ax2 = axes[1]
        categories = ['SA1\nBasic', 'PW2\nBasic', 'SA3\nBasic', 
                      'SA1\nExtra', 'SA2\nExtra', 'SA3\nExtra']
        means = [
            np.mean([p.t_SA1_basic for p in passed_PA2]),
            np.mean([p.t_PW_basic for p in passed_PA2]),
            np.mean([p.t_SA3_basic for p in passed_PA2]),
            np.mean([p.t_SA1_add for p in passed_PA2]),
            np.mean([p.t_SA2_add for p in passed_PA2]),
            np.mean([p.t_SA3_add for p in passed_PA2])
        ]
        colors = ['steelblue', 'steelblue', 'steelblue', 'coral', 'coral', 'coral']
        
        bars = ax2.bar(categories, means, color=colors, edgecolor='black', alpha=0.8)
        ax2.set_ylabel('Average Time [s]')
        ax2.set_title(f'PA2 (Without Luggage) Time Decomposition (n={len(passed_PA2)})')
        
        for bar, val in zip(bars, means):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                     f'{val:.1f}', ha='center', va='bottom', fontsize=9)
        
        total_basic = sum(means[:3])
        total_extra = sum(means[3:])
        ax2.text(0.02, 0.95, f'Basic: {total_basic:.1f}s\nExtra: {total_extra:.1f}s',
                 transform=ax2.transAxes, fontsize=10, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"  Saved: {save_path}")
    
    plt.close()
    return fig


def plot_sensitivity_english(param_name: str, param_values: List[float],
                              T_ae: List[float], t_PA1: List[float], t_PA2: List[float],
                              peak_queue: List[int], throughput: List[float],
                              save_path: Optional[str] = None):
    """
    敏感性分析图 - 英文标注
    
    4子图展示参数变化对各指标的影响
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'Sensitivity Analysis: {param_name}', fontsize=14)
    
    x = param_values
    
    # Access/Egress Time
    ax1 = axes[0, 0]
    ax1.plot(x, T_ae, 'o-', linewidth=2, markersize=8, color='steelblue')
    ax1.set_xlabel(param_name)
    ax1.set_ylabel('Access/Egress Time [s]')
    ax1.set_title('System Clearance Time')
    ax1.grid(True, alpha=0.3)
    
    # Average transit time
    ax2 = axes[0, 1]
    ax2.plot(x, t_PA1, 'o-', linewidth=2, markersize=8, label='PA1', color='coral')
    ax2.plot(x, t_PA2, 's-', linewidth=2, markersize=8, label='PA2', color='green')
    ax2.set_xlabel(param_name)
    ax2.set_ylabel('Average Transit Time [s]')
    ax2.set_title('Passenger Transit Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Peak queue
    ax3 = axes[1, 0]
    ax3.plot(x, peak_queue, 'o-', linewidth=2, markersize=8, color='red')
    ax3.set_xlabel(param_name)
    ax3.set_ylabel('Peak Queue Length')
    ax3.set_title('Peak Queue at PW1')
    ax3.grid(True, alpha=0.3)
    
    # Throughput
    ax4 = axes[1, 1]
    ax4.plot(x, throughput, 'o-', linewidth=2, markersize=8, color='green')
    ax4.set_xlabel(param_name)
    ax4.set_ylabel('Throughput [ped/s]')
    ax4.set_title('System Throughput')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"  Saved: {save_path}")
    
    plt.close()
    return fig


def plot_pattern_comparison_english(states: List[Tuple[str, SystemState]],
                                     params: SystemParameters,
                                     save_path: Optional[str] = None):
    """
    到达模式对比图 - 英文标注
    
    对比不同到达模式下的系统表现
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Arrival Pattern Comparison', fontsize=14)
    
    colors = ['steelblue', 'coral', 'green', 'purple', 'orange']
    
    # Queue length comparison
    ax1 = axes[0, 0]
    for i, (name, state) in enumerate(states):
        T = state.history['T']
        queue = state.history['queue_PW1']
        ax1.plot(T, queue, label=name, color=colors[i % len(colors)], linewidth=1.5)
    ax1.set_xlabel('Time [s]')
    ax1.set_ylabel('Queue Length at PW1')
    ax1.set_title('Queue Length Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # PW2 density comparison
    ax2 = axes[0, 1]
    for i, (name, state) in enumerate(states):
        T = state.history['T']
        K = state.history['K_PW2']
        ax2.plot(T, K, label=name, color=colors[i % len(colors)], linewidth=1.5)
    ax2.axhline(y=params.K_PW2_init, color='gray', linestyle='--', alpha=0.5, label='K_init')
    ax2.set_xlabel('Time [s]')
    ax2.set_ylabel('Density [ped/m²]')
    ax2.set_title('PW2 Density Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Cumulative throughput
    ax3 = axes[1, 0]
    for i, (name, state) in enumerate(states):
        T = state.history['T']
        D_pass = state.history['D_pass']
        ax3.plot(T, D_pass, label=name, color=colors[i % len(colors)], linewidth=1.5)
    ax3.set_xlabel('Time [s]')
    ax3.set_ylabel('Cumulative Passengers')
    ax3.set_title('System Throughput Comparison')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # SA1 population
    ax4 = axes[1, 1]
    for i, (name, state) in enumerate(states):
        T = state.history['T']
        D_SA1 = state.history['D_SA1']
        ax4.plot(T, D_SA1, label=name, color=colors[i % len(colors)], linewidth=1.5)
    ax4.set_xlabel('Time [s]')
    ax4.set_ylabel('Number of Passengers in SA1')
    ax4.set_title('Entrance Area Congestion')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"  Saved: {save_path}")
    
    plt.close()
    return fig
