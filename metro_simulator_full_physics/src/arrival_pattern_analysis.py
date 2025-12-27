"""
3.2.4 客流到达模式对比模块

功能：
1. 连续均匀到达 vs 脉冲式到达的对比
2. 验证间歇性服务策略的效果
3. 探究流变异性对拥堵传播的影响
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import os

from src.config import SystemParameters, PassengerType, Position
from src.data_structures import SystemState, Passenger
from src.simulation_engine import generate_arrivals, simulation_step
from src.metrics import compute_average_transit_time, compute_access_egress_time

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


@dataclass
class ArrivalPattern:
    """到达模式定义"""
    name: str
    description: str
    # 到达率函数: f(t) -> (q_PA1, q_PA2)
    arrival_func: Callable[[float], Tuple[float, float]]
    total_duration: float  # 总持续时间


def create_uniform_pattern(q_PA1: float, q_PA2: float, 
                           duration: float) -> ArrivalPattern:
    """创建均匀到达模式"""
    return ArrivalPattern(
        name="均匀到达",
        description=f"PA1={q_PA1}人/秒, PA2={q_PA2}人/秒, 持续{duration}秒",
        arrival_func=lambda t: (q_PA1, q_PA2) if t <= duration else (0, 0),
        total_duration=duration
    )


def create_pulsed_pattern(q_PA1_peak: float, q_PA2_peak: float,
                          pulse_duration: float, interval: float,
                          num_pulses: int) -> ArrivalPattern:
    """创建脉冲式到达模式
    
    Args:
        q_PA1_peak, q_PA2_peak: 脉冲期间的到达率
        pulse_duration: 每个脉冲的持续时间（秒）
        interval: 脉冲间隔（秒）
        num_pulses: 脉冲数量
    """
    total_duration = num_pulses * (pulse_duration + interval)
    
    def arrival_func(t):
        if t > total_duration:
            return (0, 0)
        # 计算当前处于第几个周期
        cycle = pulse_duration + interval
        phase = t % cycle
        if phase < pulse_duration:
            return (q_PA1_peak, q_PA2_peak)
        else:
            return (0, 0)
    
    return ArrivalPattern(
        name="脉冲到达",
        description=f"PA1={q_PA1_peak}人/秒×{pulse_duration}秒, 间隔{interval}秒, {num_pulses}个脉冲",
        arrival_func=arrival_func,
        total_duration=total_duration
    )


def create_wave_pattern(q_PA1_base: float, q_PA2_base: float,
                        amplitude: float, period: float,
                        duration: float) -> ArrivalPattern:
    """创建波动式到达模式（正弦变化）"""
    def arrival_func(t):
        if t > duration:
            return (0, 0)
        # 正弦调制
        factor = 1 + amplitude * np.sin(2 * np.pi * t / period)
        return (q_PA1_base * factor, q_PA2_base * factor)
    
    return ArrivalPattern(
        name="波动到达",
        description=f"基准PA1={q_PA1_base}, PA2={q_PA2_base}, 振幅={amplitude}, 周期={period}秒",
        arrival_func=arrival_func,
        total_duration=duration
    )


def create_rush_hour_pattern(duration: float = 120.0) -> ArrivalPattern:
    """创建高峰期到达模式（先升后降）"""
    peak_time = duration / 2
    
    def arrival_func(t):
        if t > duration:
            return (0, 0)
        # 高峰期曲线：先升后降
        if t < peak_time:
            factor = t / peak_time
        else:
            factor = 1 - (t - peak_time) / peak_time
        factor = max(0.2, factor)  # 最小保持20%
        return (4.0 * factor, 4.0 * factor)
    
    return ArrivalPattern(
        name="高峰期模式",
        description=f"到达率先升后降，峰值在t={duration/2}秒",
        arrival_func=arrival_func,
        total_duration=duration
    )


def run_simulation_with_pattern(params: SystemParameters,
                                pattern: ArrivalPattern,
                                max_time: float = 800.0) -> SystemState:
    """使用指定到达模式运行仿真"""
    
    state = SystemState(params=params)
    dt = params.dt
    
    while state.T < max_time:
        # 获取当前时刻的到达率
        q_PA1, q_PA2 = pattern.arrival_func(state.T)
        
        # 执行仿真步骤
        simulation_step(state, q_PA1, q_PA2)
        
        # 检查是否所有乘客都已通过
        if state.T > pattern.total_duration + 10:  # 到达结束后10秒
            if state.get_D_pass() == len(state.passengers) and len(state.passengers) > 0:
                break
    
    return state


@dataclass
class PatternComparisonResult:
    """模式对比结果"""
    pattern_name: str
    total_passengers: int
    T_ae: float
    t_PA1: float
    t_PA2: float
    peak_queue_PW1: int
    peak_K_PW2: float
    peak_K_SA3: float
    avg_queue_PW1: float
    congestion_duration: float  # K > K_init的时长


def analyze_pattern(state: SystemState, params: SystemParameters,
                    pattern_name: str) -> PatternComparisonResult:
    """分析单个模式的结果"""
    
    history = state.history
    T_ae = compute_access_egress_time(state)
    avg_times = compute_average_transit_time(state)
    
    queue_PW1 = history['queue_PW1']
    K_PW2 = history['K_PW2']
    K_SA3 = history['K_SA3']
    
    peak_queue_PW1 = max(queue_PW1) if queue_PW1 else 0
    peak_K_PW2 = max(K_PW2) if K_PW2 else 0
    peak_K_SA3 = max(K_SA3) if K_SA3 else 0
    avg_queue_PW1 = np.mean(queue_PW1) if queue_PW1 else 0
    
    # 拥堵持续时间
    K_init = params.K_PW2_init
    congestion_steps = sum(1 for k in K_PW2 if k > K_init)
    congestion_duration = congestion_steps * params.dt
    
    return PatternComparisonResult(
        pattern_name=pattern_name,
        total_passengers=len(state.passengers),
        T_ae=T_ae,
        t_PA1=avg_times['t_avg_PA1'],
        t_PA2=avg_times['t_avg_PA2'],
        peak_queue_PW1=int(peak_queue_PW1),
        peak_K_PW2=peak_K_PW2,
        peak_K_SA3=peak_K_SA3,
        avg_queue_PW1=avg_queue_PW1,
        congestion_duration=congestion_duration
    )


def plot_pattern_comparison(states: List[Tuple[str, SystemState]],
                            params: SystemParameters,
                            save_path: Optional[str] = None):
    """绘制多个到达模式的对比图"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('客流到达模式对比', fontsize=14)
    
    colors = ['steelblue', 'coral', 'green', 'purple', 'orange']
    
    # 子图1: 排队长度对比
    ax1 = axes[0, 0]
    for i, (name, state) in enumerate(states):
        T = state.history['T']
        queue = state.history['queue_PW1']
        ax1.plot(T, queue, label=name, color=colors[i % len(colors)], linewidth=1.5)
    ax1.set_xlabel('时间 (s)')
    ax1.set_ylabel('PW1排队人数')
    ax1.set_title('PW1前排队长度对比')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 子图2: PW2密度对比
    ax2 = axes[0, 1]
    for i, (name, state) in enumerate(states):
        T = state.history['T']
        K = state.history['K_PW2']
        ax2.plot(T, K, label=name, color=colors[i % len(colors)], linewidth=1.5)
    ax2.axhline(y=params.K_PW2_init, color='gray', linestyle='--', alpha=0.5, label='K_init')
    ax2.set_xlabel('时间 (s)')
    ax2.set_ylabel('密度 (ped/m²)')
    ax2.set_title('PW2密度对比')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 子图3: 累计通过人数
    ax3 = axes[1, 0]
    for i, (name, state) in enumerate(states):
        T = state.history['T']
        D_pass = state.history['D_pass']
        ax3.plot(T, D_pass, label=name, color=colors[i % len(colors)], linewidth=1.5)
    ax3.set_xlabel('时间 (s)')
    ax3.set_ylabel('累计通过人数')
    ax3.set_title('系统疏散曲线对比')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 子图4: SA1人数（反映入口拥堵）
    ax4 = axes[1, 1]
    for i, (name, state) in enumerate(states):
        T = state.history['T']
        D_SA1 = state.history['D_SA1']
        ax4.plot(T, D_SA1, label=name, color=colors[i % len(colors)], linewidth=1.5)
    ax4.set_xlabel('时间 (s)')
    ax4.set_ylabel('SA1人数')
    ax4.set_title('入口区堆积对比')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  保存图表: {save_path}")
    
    plt.close()


def plot_metrics_bar_chart(results: List[PatternComparisonResult],
                           save_path: Optional[str] = None):
    """绘制指标对比柱状图"""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('不同到达模式的性能指标对比', fontsize=14)
    
    names = [r.pattern_name for r in results]
    x = np.arange(len(names))
    
    # 子图1: 疏散时间
    ax1 = axes[0, 0]
    values = [r.T_ae for r in results]
    bars = ax1.bar(x, values, color='steelblue', alpha=0.8, edgecolor='black')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=45, ha='right')
    ax1.set_ylabel('时间 (s)')
    ax1.set_title('Access/Egress Time')
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                 f'{val:.1f}', ha='center', fontsize=9)
    
    # 子图2: 平均通行时间
    ax2 = axes[0, 1]
    width = 0.35
    bars1 = ax2.bar(x - width/2, [r.t_PA1 for r in results], width, 
                    label='PA1', color='coral', alpha=0.8, edgecolor='black')
    bars2 = ax2.bar(x + width/2, [r.t_PA2 for r in results], width, 
                    label='PA2', color='green', alpha=0.8, edgecolor='black')
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, rotation=45, ha='right')
    ax2.set_ylabel('时间 (s)')
    ax2.set_title('平均通行时间')
    ax2.legend()
    
    # 子图3: 峰值排队
    ax3 = axes[1, 0]
    values = [r.peak_queue_PW1 for r in results]
    bars = ax3.bar(x, values, color='red', alpha=0.8, edgecolor='black')
    ax3.set_xticks(x)
    ax3.set_xticklabels(names, rotation=45, ha='right')
    ax3.set_ylabel('人数')
    ax3.set_title('峰值PW1排队')
    for bar, val in zip(bars, values):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f'{val}', ha='center', fontsize=9)
    
    # 子图4: 拥堵持续时间
    ax4 = axes[1, 1]
    values = [r.congestion_duration for r in results]
    bars = ax4.bar(x, values, color='purple', alpha=0.8, edgecolor='black')
    ax4.set_xticks(x)
    ax4.set_xticklabels(names, rotation=45, ha='right')
    ax4.set_ylabel('时间 (s)')
    ax4.set_title('拥堵持续时间 (K > K_init)')
    for bar, val in zip(bars, values):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f'{val:.1f}', ha='center', fontsize=9)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  保存图表: {save_path}")
    
    plt.close()


def run_arrival_pattern_comparison(output_dir: str = "outputs/pattern_comparison"):
    """运行客流到达模式对比实验"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print("3.2.4 客流到达模式对比")
    print("="*60)
    
    params = SystemParameters()
    
    # 计算均匀模式的总人数，确保各模式总人数相近
    uniform_q = 3.0  # PA1和PA2各3人/秒
    uniform_duration = 60.0
    total_passengers = int((uniform_q + uniform_q) * uniform_duration)  # 360人
    
    print(f"\n目标总人数: ~{total_passengers}人")
    
    # 定义各种到达模式
    patterns = [
        # 模式1: 均匀到达（基准）
        create_uniform_pattern(3.0, 3.0, 60.0),
        
        # 模式2: 脉冲式到达（6个脉冲，每次10秒，间隔5秒）
        # 为保持总人数相近：6人/秒 × 10秒 × 6脉冲 = 360人
        create_pulsed_pattern(3.0, 3.0, 10.0, 5.0, 6),
        
        # 模式3: 高密度短脉冲（更短更密集的脉冲）
        # 12人/秒 × 5秒 × 6脉冲 = 360人
        create_pulsed_pattern(6.0, 6.0, 5.0, 5.0, 6),
        
        # 模式4: 波动式到达
        create_wave_pattern(3.0, 3.0, 0.5, 20.0, 60.0),
        
        # 模式5: 高峰期模式
        create_rush_hour_pattern(90.0),
    ]
    
    states = []
    results = []
    
    for pattern in patterns:
        print(f"\n运行模式: {pattern.name}")
        print(f"  描述: {pattern.description}")
        
        state = run_simulation_with_pattern(params, pattern, max_time=800.0)
        states.append((pattern.name, state))
        
        result = analyze_pattern(state, params, pattern.name)
        results.append(result)
        
        print(f"  总乘客: {result.total_passengers}")
        print(f"  疏散时间: {result.T_ae:.1f}s")
        print(f"  PA1平均: {result.t_PA1:.1f}s, PA2平均: {result.t_PA2:.1f}s")
        print(f"  峰值排队: {result.peak_queue_PW1}人")
        print(f"  拥堵持续: {result.congestion_duration:.1f}s")
    
    # 绘制对比图
    plot_pattern_comparison(states, params, 
                            save_path=f"{output_dir}/pattern_comparison_curves.png")
    
    plot_metrics_bar_chart(results,
                           save_path=f"{output_dir}/pattern_comparison_bars.png")
    
    # 生成报告
    report_path = f"{output_dir}/pattern_comparison_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("客流到达模式对比分析报告\n")
        f.write("="*60 + "\n\n")
        
        f.write("1. 实验目的\n")
        f.write("-"*40 + "\n")
        f.write("探究流变异性对拥堵传播的影响机制，验证间歇性服务策略\n")
        f.write("在缓解连续性瓶颈中的潜在效能。\n\n")
        
        f.write("2. 实验设计\n")
        f.write("-"*40 + "\n")
        f.write("保持总客流量相近（约360人），对比不同到达模式：\n")
        for pattern in patterns:
            f.write(f"  - {pattern.name}: {pattern.description}\n")
        f.write("\n")
        
        f.write("3. 结果汇总\n")
        f.write("-"*40 + "\n")
        f.write(f"{'模式':<12} {'人数':<8} {'T_ae':<10} {'PA1':<10} {'PA2':<10} "
                f"{'峰值排队':<10} {'拥堵时长':<10}\n")
        f.write("-"*70 + "\n")
        for r in results:
            f.write(f"{r.pattern_name:<12} {r.total_passengers:<8} {r.T_ae:<10.1f} "
                    f"{r.t_PA1:<10.1f} {r.t_PA2:<10.1f} {r.peak_queue_PW1:<10} "
                    f"{r.congestion_duration:<10.1f}\n")
        f.write("\n")
        
        f.write("4. 关键发现\n")
        f.write("-"*40 + "\n")
        
        # 找出峰值排队最小的模式
        min_queue_result = min(results, key=lambda r: r.peak_queue_PW1)
        f.write(f"峰值排队最小: {min_queue_result.pattern_name} "
                f"({min_queue_result.peak_queue_PW1}人)\n")
        
        # 找出疏散最快的模式
        min_tae_result = min(results, key=lambda r: r.T_ae)
        f.write(f"疏散最快: {min_tae_result.pattern_name} "
                f"({min_tae_result.T_ae:.1f}秒)\n")
        
        # 找出拥堵时间最短的模式
        min_cong_result = min(results, key=lambda r: r.congestion_duration)
        f.write(f"拥堵时间最短: {min_cong_result.pattern_name} "
                f"({min_cong_result.congestion_duration:.1f}秒)\n")
        
        f.write("\n5. 结论\n")
        f.write("-"*40 + "\n")
        
        # 对比均匀模式和脉冲模式
        uniform_result = results[0]
        pulsed_result = results[1]
        
        queue_reduction = (uniform_result.peak_queue_PW1 - pulsed_result.peak_queue_PW1) / uniform_result.peak_queue_PW1 * 100 if uniform_result.peak_queue_PW1 > 0 else 0
        
        if pulsed_result.peak_queue_PW1 < uniform_result.peak_queue_PW1:
            f.write(f"脉冲式到达相比均匀到达，峰值排队降低{queue_reduction:.1f}%\n")
            f.write("这验证了引入客流控制间隔可以降低排队峰值的假设。\n")
        else:
            f.write("在当前参数设置下，脉冲式到达未能显著降低峰值排队。\n")
            f.write("可能需要调整脉冲参数（间隔、强度）以优化效果。\n")
    
    print(f"\n保存分析报告: {report_path}")
    
    # 保存CSV
    csv_path = f"{output_dir}/pattern_comparison_data.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("模式,总人数,T_ae,t_PA1,t_PA2,峰值排队,峰值K_PW2,拥堵时长\n")
        for r in results:
            f.write(f"{r.pattern_name},{r.total_passengers},{r.T_ae:.2f},"
                    f"{r.t_PA1:.2f},{r.t_PA2:.2f},{r.peak_queue_PW1},"
                    f"{r.peak_K_PW2:.2f},{r.congestion_duration:.1f}\n")
    
    print(f"保存CSV数据: {csv_path}")
    
    return results, states


if __name__ == "__main__":
    run_arrival_pattern_comparison()
