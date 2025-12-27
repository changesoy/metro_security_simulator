"""
3.2.2 拥堵特性动态分析模块

功能：
1. 拥堵波传播分析 - 揭示高峰期拥堵的形成和消散机理
2. 时空演化可视化 - 排队长度、密度随时间变化
3. 拥堵传播延迟 - 分析上下游区域的拥堵传递关系
4. 附加时间贡献分析 - 量化拥堵对通行时间的影响

注：所有图表输出为英文标注
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import os

from src.config import SystemParameters, PassengerType, Position
from src.data_structures import SystemState
from src.simulation_engine import run_simulation
from src.metrics import compute_average_transit_time, compute_access_egress_time

# 图表样式配置（使用英文字体避免中文显示问题）
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'legend.fontsize': 9,
    'figure.dpi': 150,
})


@dataclass
class CongestionMetrics:
    """拥堵指标数据类"""
    # 峰值指标
    peak_queue_SA1: int
    peak_queue_PW1: int
    peak_D_PW2: int
    peak_D_SA3: int
    peak_K_PW2: float
    peak_K_SA3: float
    
    # 峰值时刻
    t_peak_queue_SA1: float
    t_peak_queue_PW1: float
    t_peak_K_PW2: float
    t_peak_K_SA3: float
    
    # 拥堵持续时间
    congestion_duration_PW2: float  # K_PW2 > K_init的持续时间
    congestion_duration_SA3: float  # K_SA3 > K_init的持续时间
    
    # 附加时间贡献
    avg_add_time_PA1: float
    avg_add_time_PA2: float
    add_time_ratio_PA1: float  # 附加时间占总时间比例
    add_time_ratio_PA2: float


def analyze_congestion(state: SystemState, params: SystemParameters) -> CongestionMetrics:
    """分析单次仿真的拥堵特性
    
    Args:
        state: 仿真完成后的系统状态
        params: 系统参数
        
    Returns:
        CongestionMetrics: 拥堵指标
    """
    history = state.history
    T_arr = np.array(history['T'])
    
    # 计算SA1排队人数（等待进入PW的PA1和PA2）
    D_SA1_arr = np.array(history['D_SA1'])
    queue_PW1_arr = np.array(history['queue_PW1'])
    D_PW2_arr = np.array(history['D_PW2'])
    D_SA3_arr = np.array(history['D_SA3'])
    K_PW2_arr = np.array(history['K_PW2'])
    K_SA3_arr = np.array(history['K_SA3'])
    
    # 峰值及峰值时刻
    peak_queue_SA1 = int(np.max(D_SA1_arr)) if len(D_SA1_arr) > 0 else 0
    peak_queue_PW1 = int(np.max(queue_PW1_arr)) if len(queue_PW1_arr) > 0 else 0
    peak_D_PW2 = int(np.max(D_PW2_arr)) if len(D_PW2_arr) > 0 else 0
    peak_D_SA3 = int(np.max(D_SA3_arr)) if len(D_SA3_arr) > 0 else 0
    peak_K_PW2 = float(np.max(K_PW2_arr)) if len(K_PW2_arr) > 0 else 0.0
    peak_K_SA3 = float(np.max(K_SA3_arr)) if len(K_SA3_arr) > 0 else 0.0
    
    t_peak_queue_SA1 = T_arr[np.argmax(D_SA1_arr)] if len(D_SA1_arr) > 0 else 0.0
    t_peak_queue_PW1 = T_arr[np.argmax(queue_PW1_arr)] if len(queue_PW1_arr) > 0 else 0.0
    t_peak_K_PW2 = T_arr[np.argmax(K_PW2_arr)] if len(K_PW2_arr) > 0 else 0.0
    t_peak_K_SA3 = T_arr[np.argmax(K_SA3_arr)] if len(K_SA3_arr) > 0 else 0.0
    
    # 拥堵持续时间（密度超过阈值的时长）
    K_init = params.K_PW2_init
    congestion_PW2 = K_PW2_arr > K_init
    congestion_SA3 = K_SA3_arr > K_init
    congestion_duration_PW2 = np.sum(congestion_PW2) * params.dt
    congestion_duration_SA3 = np.sum(congestion_SA3) * params.dt
    
    # 附加时间分析
    passed_PA1 = [p for p in state.passengers 
                  if p.position == Position.PASSED and p.ptype == PassengerType.PA1]
    passed_PA2 = [p for p in state.passengers 
                  if p.position == Position.PASSED and p.ptype == PassengerType.PA2]
    
    if passed_PA1:
        total_times_PA1 = [p.total_time() for p in passed_PA1]
        add_times_PA1 = [p.t_SA1_add + p.t_SA2_add + p.t_SA3_add for p in passed_PA1]
        avg_add_time_PA1 = np.mean(add_times_PA1)
        avg_total_PA1 = np.mean(total_times_PA1)
        add_time_ratio_PA1 = avg_add_time_PA1 / avg_total_PA1 if avg_total_PA1 > 0 else 0
    else:
        avg_add_time_PA1 = 0.0
        add_time_ratio_PA1 = 0.0
    
    if passed_PA2:
        total_times_PA2 = [p.total_time() for p in passed_PA2]
        add_times_PA2 = [p.t_SA1_add + p.t_SA2_add + p.t_SA3_add for p in passed_PA2]
        avg_add_time_PA2 = np.mean(add_times_PA2)
        avg_total_PA2 = np.mean(total_times_PA2)
        add_time_ratio_PA2 = avg_add_time_PA2 / avg_total_PA2 if avg_total_PA2 > 0 else 0
    else:
        avg_add_time_PA2 = 0.0
        add_time_ratio_PA2 = 0.0
    
    return CongestionMetrics(
        peak_queue_SA1=peak_queue_SA1,
        peak_queue_PW1=peak_queue_PW1,
        peak_D_PW2=peak_D_PW2,
        peak_D_SA3=peak_D_SA3,
        peak_K_PW2=peak_K_PW2,
        peak_K_SA3=peak_K_SA3,
        t_peak_queue_SA1=t_peak_queue_SA1,
        t_peak_queue_PW1=t_peak_queue_PW1,
        t_peak_K_PW2=t_peak_K_PW2,
        t_peak_K_SA3=t_peak_K_SA3,
        congestion_duration_PW2=congestion_duration_PW2,
        congestion_duration_SA3=congestion_duration_SA3,
        avg_add_time_PA1=avg_add_time_PA1,
        avg_add_time_PA2=avg_add_time_PA2,
        add_time_ratio_PA1=add_time_ratio_PA1,
        add_time_ratio_PA2=add_time_ratio_PA2
    )


def plot_congestion_evolution(state: SystemState, params: SystemParameters,
                              title: str = "", save_path: Optional[str] = None):
    """绘制拥堵演化图（4子图）- 英文标注
    
    子图1: 各区域人数随时间变化
    子图2: 密度随时间变化
    子图3: PW1排队长度
    子图4: 累计通过人数
    """
    history = state.history
    T = history['T']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Congestion Dynamics Analysis {title}', fontsize=14)
    
    # 子图1: 各区域人数
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
    
    # 子图2: 密度演化
    ax2 = axes[0, 1]
    ax2.plot(T, history['K_PW2'], label='K_PW2', linewidth=1.5, color='orange')
    ax2.plot(T, history['K_SA3'], label='K_SA3', linewidth=1.5, color='green')
    ax2.axhline(y=params.K_PW2_init, color='orange', linestyle='--', alpha=0.5, label=f'K_init={params.K_PW2_init}')
    ax2.axhline(y=params.K_PW2_max, color='red', linestyle='--', alpha=0.5, label=f'K_max={params.K_PW2_max}')
    ax2.set_xlabel('Time [s]')
    ax2.set_ylabel('Density [ped/m²]')
    ax2.set_title('Density Evolution and Thresholds')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # 子图3: PW1排队长度
    ax3 = axes[1, 0]
    ax3.fill_between(T, 0, history['queue_PW1'], alpha=0.5, color='coral')
    ax3.plot(T, history['queue_PW1'], color='red', linewidth=1.5)
    ax3.set_xlabel('Time [s]')
    ax3.set_ylabel('Queue Length')
    ax3.set_title('Queue at PW1 Entrance (PA1 waiting in SA1)')
    ax3.grid(True, alpha=0.3)
    
    # 子图4: 累计通过人数
    ax4 = axes[1, 1]
    ax4.plot(T, history['D_pass'], linewidth=2, color='green')
    total_arrived = len(state.passengers)
    ax4.axhline(y=total_arrived, color='gray', linestyle='--', alpha=0.5, 
                label=f'Total arrived={total_arrived}')
    ax4.set_xlabel('Time [s]')
    ax4.set_ylabel('Cumulative Passengers Passed')
    ax4.set_title('System Throughput Curve')
    ax4.legend(loc='lower right')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  保存图表: {save_path}")
    
    plt.close()


def plot_time_decomposition(state: SystemState, title: str = "", 
                            save_path: Optional[str] = None):
    """绘制时间构成分解图（基本时间 vs 附加时间）- 英文标注"""
    
    passed_PA1 = [p for p in state.passengers 
                  if p.position == Position.PASSED and p.ptype == PassengerType.PA1]
    passed_PA2 = [p for p in state.passengers 
                  if p.position == Position.PASSED and p.ptype == PassengerType.PA2]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'Transit Time Decomposition {title}', fontsize=14)
    
    # PA1时间分解
    if passed_PA1:
        ax1 = axes[0]
        t_SA1_basic = [p.t_SA1_basic for p in passed_PA1]
        t_PW_basic = [p.t_PW_basic for p in passed_PA1]
        t_SA3_basic = [p.t_SA3_basic for p in passed_PA1]
        t_SA1_add = [p.t_SA1_add for p in passed_PA1]
        t_SA2_add = [p.t_SA2_add for p in passed_PA1]
        t_SA3_add = [p.t_SA3_add for p in passed_PA1]
        
        categories = ['SA1\nBasic', 'PW1\nBasic', 'SA3\nBasic', 'SA1\nExtra', 'SA2\nExtra', 'SA3\nExtra']
        means = [np.mean(t_SA1_basic), np.mean(t_PW_basic), np.mean(t_SA3_basic),
                 np.mean(t_SA1_add), np.mean(t_SA2_add), np.mean(t_SA3_add)]
        colors = ['steelblue', 'steelblue', 'steelblue', 'coral', 'coral', 'coral']
        
        bars = ax1.bar(categories, means, color=colors, edgecolor='black', alpha=0.8)
        ax1.set_ylabel('Average Time [s]')
        ax1.set_title(f'PA1 (With Luggage) Time Decomposition (n={len(passed_PA1)})')
        
        # 添加数值标签
        for bar, val in zip(bars, means):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                     f'{val:.1f}', ha='center', va='bottom', fontsize=9)
        
        # 添加基本/附加总计
        total_basic = means[0] + means[1] + means[2]
        total_add = means[3] + means[4] + means[5]
        ax1.text(0.02, 0.95, f'Basic: {total_basic:.1f}s\nExtra: {total_add:.1f}s',
                 transform=ax1.transAxes, fontsize=10, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # PA2时间分解
    if passed_PA2:
        ax2 = axes[1]
        t_SA1_basic = [p.t_SA1_basic for p in passed_PA2]
        t_PW_basic = [p.t_PW_basic for p in passed_PA2]
        t_SA3_basic = [p.t_SA3_basic for p in passed_PA2]
        t_SA1_add = [p.t_SA1_add for p in passed_PA2]
        t_SA2_add = [p.t_SA2_add for p in passed_PA2]
        t_SA3_add = [p.t_SA3_add for p in passed_PA2]
        
        categories = ['SA1\nBasic', 'PW2\nBasic', 'SA3\nBasic', 'SA1\nExtra', 'SA2\nExtra', 'SA3\nExtra']
        means = [np.mean(t_SA1_basic), np.mean(t_PW_basic), np.mean(t_SA3_basic),
                 np.mean(t_SA1_add), np.mean(t_SA2_add), np.mean(t_SA3_add)]
        colors = ['steelblue', 'steelblue', 'steelblue', 'coral', 'coral', 'coral']
        
        bars = ax2.bar(categories, means, color=colors, edgecolor='black', alpha=0.8)
        ax2.set_ylabel('Average Time [s]')
        ax2.set_title(f'PA2 (Without Luggage) Time Decomposition (n={len(passed_PA2)})')
        
        for bar, val in zip(bars, means):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                     f'{val:.1f}', ha='center', va='bottom', fontsize=9)
        
        total_basic = means[0] + means[1] + means[2]
        total_add = means[3] + means[4] + means[5]
        ax2.text(0.02, 0.95, f'Basic: {total_basic:.1f}s\nExtra: {total_add:.1f}s',
                 transform=ax2.transAxes, fontsize=10, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  保存图表: {save_path}")
    
    plt.close()


def plot_congestion_propagation(state: SystemState, params: SystemParameters,
                                title: str = "", save_path: Optional[str] = None):
    """绘制拥堵波传播图 - 展示上下游拥堵的时序关系（英文标注）"""
    
    history = state.history
    T = np.array(history['T'])
    
    # 归一化各指标以便比较
    D_SA1 = np.array(history['D_SA1'])
    queue_PW1 = np.array(history['queue_PW1'])
    K_PW2 = np.array(history['K_PW2'])
    K_SA3 = np.array(history['K_SA3'])
    
    # 归一化到0-1
    def normalize(arr):
        if np.max(arr) > 0:
            return arr / np.max(arr)
        return arr
    
    D_SA1_norm = normalize(D_SA1)
    queue_PW1_norm = normalize(queue_PW1)
    K_PW2_norm = normalize(K_PW2)
    K_SA3_norm = normalize(K_SA3)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(T, D_SA1_norm, label='SA1 Population', linewidth=1.5, alpha=0.8)
    ax.plot(T, queue_PW1_norm, label='PW1 Queue', linewidth=1.5, alpha=0.8)
    ax.plot(T, K_PW2_norm, label='PW2 Density', linewidth=1.5, alpha=0.8)
    ax.plot(T, K_SA3_norm, label='SA3 Density', linewidth=1.5, alpha=0.8)
    
    # 标记峰值点
    peaks = [
        (T[np.argmax(D_SA1)], np.max(D_SA1_norm), 'SA1 Peak'),
        (T[np.argmax(queue_PW1)], np.max(queue_PW1_norm), 'PW1 Peak'),
        (T[np.argmax(K_PW2)], np.max(K_PW2_norm), 'PW2 Peak'),
        (T[np.argmax(K_SA3)], np.max(K_SA3_norm), 'SA3 Peak'),
    ]
    
    for t_peak, val, label in peaks:
        ax.axvline(x=t_peak, linestyle=':', alpha=0.5)
        ax.annotate(f'{label}\nt={t_peak:.1f}s', xy=(t_peak, val),
                    xytext=(t_peak+5, val-0.1), fontsize=8,
                    arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5))
    
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Normalized Metric')
    ax.set_title(f'Congestion Wave Propagation Analysis {title}')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  保存图表: {save_path}")
    
    plt.close()


def run_congestion_analysis(output_dir: str = "outputs/congestion_analysis"):
    """运行拥堵特性分析实验"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print("3.2.2 拥堵特性动态分析")
    print("="*60)
    
    params = SystemParameters()
    
    # 实验组：不同的PA1/PA2配比
    experiments = [
        ("Low_Load", 1.0, 2.0, 60.0),
        ("Medium_Load", 2.0, 3.0, 60.0),
        ("High_Load", 3.0, 3.0, 60.0),
        ("Very_High_Load", 4.0, 4.0, 60.0),
    ]
    
    results = []
    
    for name, q_PA1, q_PA2, duration in experiments:
        print(f"\n运行实验: {name} (PA1={q_PA1}, PA2={q_PA2})")
        
        state = run_simulation(params, q_PA1, q_PA2, duration, max_time=800.0)
        
        # 分析拥堵指标
        metrics = analyze_congestion(state, params)
        results.append((name, q_PA1, q_PA2, metrics, state))
        
        print(f"  峰值PW1排队: {metrics.peak_queue_PW1}人 @ t={metrics.t_peak_queue_PW1:.1f}s")
        print(f"  峰值PW2密度: {metrics.peak_K_PW2:.2f} ped/m² @ t={metrics.t_peak_K_PW2:.1f}s")
        print(f"  拥堵持续时间: PW2={metrics.congestion_duration_PW2:.1f}s, SA3={metrics.congestion_duration_SA3:.1f}s")
        print(f"  PA1附加时间占比: {metrics.add_time_ratio_PA1*100:.1f}%")
        print(f"  PA2附加时间占比: {metrics.add_time_ratio_PA2*100:.1f}%")
        
        # 绘制图表
        plot_congestion_evolution(
            state, params, title=f"- {name}",
            save_path=f"{output_dir}/evolution_{name}.png"
        )
        
        plot_time_decomposition(
            state, title=f"- {name}",
            save_path=f"{output_dir}/time_decomposition_{name}.png"
        )
        
        plot_congestion_propagation(
            state, params, title=f"- {name}",
            save_path=f"{output_dir}/propagation_{name}.png"
        )
    
    # 生成汇总表
    summary_path = f"{output_dir}/congestion_summary.csv"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("实验名称,PA1到达率,PA2到达率,峰值PW1排队,峰值PW2密度,峰值SA3密度,")
        f.write("拥堵持续PW2(s),拥堵持续SA3(s),PA1附加时间占比(%),PA2附加时间占比(%)\n")
        for name, q1, q2, m, _ in results:
            f.write(f"{name},{q1},{q2},{m.peak_queue_PW1},{m.peak_K_PW2:.2f},{m.peak_K_SA3:.2f},")
            f.write(f"{m.congestion_duration_PW2:.1f},{m.congestion_duration_SA3:.1f},")
            f.write(f"{m.add_time_ratio_PA1*100:.1f},{m.add_time_ratio_PA2*100:.1f}\n")
    
    print(f"\n保存汇总表: {summary_path}")
    
    return results


if __name__ == "__main__":
    run_congestion_analysis()
