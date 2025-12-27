"""
3.2.3 参数敏感性分析模块

功能：
1. 单参数敏感性分析 - 量化关键参数对系统性能的影响
2. 多参数交互分析 - 探索参数组合的影响
3. 关键参数识别 - 找出对系统性能影响最大的参数
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
import os
import copy

from src.config import SystemParameters, PassengerType, Position
from src.data_structures import SystemState
from src.simulation_engine import run_simulation
from src.metrics import compute_average_transit_time, compute_access_egress_time

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


@dataclass
class SensitivityResult:
    """敏感性分析结果"""
    param_name: str
    param_values: List[float]
    T_ae: List[float]
    t_PA1: List[float]
    t_PA2: List[float]
    peak_queue_PW1: List[int]
    peak_K_PW2: List[float]
    throughput: List[float]  # 单位时间通过人数


def run_single_sensitivity(param_name: str, param_values: List[float],
                           q_PA1: float = 3.0, q_PA2: float = 3.0,
                           duration: float = 60.0) -> SensitivityResult:
    """单参数敏感性分析
    
    Args:
        param_name: 参数名称（必须是SystemParameters的属性）
        param_values: 参数取值列表
        q_PA1, q_PA2: 到达率
        duration: 到达持续时间
        
    Returns:
        SensitivityResult: 分析结果
    """
    results = SensitivityResult(
        param_name=param_name,
        param_values=param_values,
        T_ae=[],
        t_PA1=[],
        t_PA2=[],
        peak_queue_PW1=[],
        peak_K_PW2=[],
        throughput=[]
    )
    
    base_params = SystemParameters()
    
    for val in param_values:
        # 创建修改后的参数
        # 使用动态创建子类的方式修改参数
        modified_params = copy.copy(base_params)
        
        # 根据参数名设置值
        if hasattr(modified_params, param_name):
            # 对于dataclass，需要使用object.__setattr__
            object.__setattr__(modified_params, param_name, val)
        else:
            print(f"警告: 参数 {param_name} 不存在")
            continue
        
        # 运行仿真
        state = run_simulation(modified_params, q_PA1, q_PA2, duration, max_time=800.0)
        
        # 收集指标
        T_ae = compute_access_egress_time(state)
        avg_times = compute_average_transit_time(state)
        
        results.T_ae.append(T_ae)
        results.t_PA1.append(avg_times['t_avg_PA1'])
        results.t_PA2.append(avg_times['t_avg_PA2'])
        
        # 峰值指标
        peak_queue = max(state.history['queue_PW1']) if state.history['queue_PW1'] else 0
        peak_K = max(state.history['K_PW2']) if state.history['K_PW2'] else 0
        results.peak_queue_PW1.append(int(peak_queue))
        results.peak_K_PW2.append(peak_K)
        
        # 吞吐量
        throughput = state.get_D_pass() / T_ae if T_ae > 0 else 0
        results.throughput.append(throughput)
    
    return results


def plot_sensitivity_curves(result: SensitivityResult, 
                            save_path: Optional[str] = None):
    """绘制敏感性曲线（4子图）"""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'参数敏感性分析: {result.param_name}', fontsize=14)
    
    x = result.param_values
    
    # 子图1: Access/Egress Time
    ax1 = axes[0, 0]
    ax1.plot(x, result.T_ae, 'o-', linewidth=2, markersize=8, color='steelblue')
    ax1.set_xlabel(result.param_name)
    ax1.set_ylabel('Access/Egress Time (s)')
    ax1.set_title('系统疏散时间')
    ax1.grid(True, alpha=0.3)
    
    # 子图2: 平均通行时间
    ax2 = axes[0, 1]
    ax2.plot(x, result.t_PA1, 'o-', linewidth=2, markersize=8, label='PA1', color='coral')
    ax2.plot(x, result.t_PA2, 's-', linewidth=2, markersize=8, label='PA2', color='green')
    ax2.set_xlabel(result.param_name)
    ax2.set_ylabel('平均通行时间 (s)')
    ax2.set_title('乘客平均通行时间')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 子图3: 峰值排队/密度
    ax3 = axes[1, 0]
    ax3_twin = ax3.twinx()
    line1 = ax3.plot(x, result.peak_queue_PW1, 'o-', linewidth=2, markersize=8, 
                     color='red', label='峰值PW1排队')
    line2 = ax3_twin.plot(x, result.peak_K_PW2, 's-', linewidth=2, markersize=8, 
                          color='purple', label='峰值PW2密度')
    ax3.set_xlabel(result.param_name)
    ax3.set_ylabel('峰值排队人数', color='red')
    ax3_twin.set_ylabel('峰值密度 (ped/m²)', color='purple')
    ax3.set_title('峰值拥堵指标')
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    # 子图4: 吞吐量
    ax4 = axes[1, 1]
    ax4.plot(x, result.throughput, 'o-', linewidth=2, markersize=8, color='green')
    ax4.set_xlabel(result.param_name)
    ax4.set_ylabel('吞吐量 (ped/s)')
    ax4.set_title('系统吞吐量')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  保存图表: {save_path}")
    
    plt.close()


def compute_sensitivity_index(result: SensitivityResult) -> Dict[str, float]:
    """计算敏感性指标（变化率）
    
    敏感性指标 = (指标变化百分比) / (参数变化百分比)
    """
    param_range = (max(result.param_values) - min(result.param_values)) / np.mean(result.param_values)
    
    def calc_sensitivity(values):
        if len(values) < 2 or np.mean(values) == 0:
            return 0.0
        value_range = (max(values) - min(values)) / np.mean(values)
        return value_range / param_range if param_range > 0 else 0.0
    
    return {
        'T_ae': calc_sensitivity(result.T_ae),
        't_PA1': calc_sensitivity(result.t_PA1),
        't_PA2': calc_sensitivity(result.t_PA2),
        'peak_queue': calc_sensitivity(result.peak_queue_PW1),
        'peak_K': calc_sensitivity(result.peak_K_PW2),
        'throughput': calc_sensitivity(result.throughput)
    }


def run_sensitivity_analysis(output_dir: str = "outputs/sensitivity_analysis"):
    """运行完整的参数敏感性分析"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print("3.2.3 参数敏感性分析")
    print("="*60)
    
    # 定义要分析的参数及其取值范围
    sensitivity_configs = [
        # (参数名, 参数值列表, 参数中文名)
        ('N_G', [3, 4, 5, 6, 7, 8], '闸机数量'),
        ('t_s', [2.0, 2.5, 3.0, 3.5, 4.0, 4.5], '刷卡时间(s)'),
        ('A_SA3', [15.0, 18.0, 21.8, 25.0, 30.0, 35.0], 'SA3面积(m²)'),
        ('K_PW2_max', [2.5, 3.0, 3.5, 4.0, 4.5], 'PW2最大密度'),
        ('v0', [1.2, 1.4, 1.61, 1.8, 2.0], '自由流速度(m/s)'),
        ('v_SE', [0.15, 0.18, 0.2, 0.22, 0.25], '传送带速度(m/s)'),
    ]
    
    all_results = []
    sensitivity_indices = {}
    
    for param_name, param_values, param_label in sensitivity_configs:
        print(f"\n分析参数: {param_label} ({param_name})")
        print(f"  取值范围: {param_values}")
        
        result = run_single_sensitivity(param_name, param_values, 
                                         q_PA1=3.0, q_PA2=3.0, duration=60.0)
        all_results.append((param_name, param_label, result))
        
        # 绘制敏感性曲线
        plot_sensitivity_curves(result, save_path=f"{output_dir}/sensitivity_{param_name}.png")
        
        # 计算敏感性指标
        indices = compute_sensitivity_index(result)
        sensitivity_indices[param_name] = indices
        
        print(f"  敏感性指标: T_ae={indices['T_ae']:.2f}, t_PA1={indices['t_PA1']:.2f}")
    
    # 绘制敏感性指标对比图
    plot_sensitivity_comparison(sensitivity_indices, sensitivity_configs,
                                save_path=f"{output_dir}/sensitivity_comparison.png")
    
    # 生成汇总报告
    generate_sensitivity_report(all_results, sensitivity_indices, 
                                sensitivity_configs, output_dir)
    
    return all_results, sensitivity_indices


def plot_sensitivity_comparison(indices: Dict[str, Dict[str, float]],
                                configs: List[Tuple],
                                save_path: Optional[str] = None):
    """绘制各参数敏感性指标对比图"""
    
    params = [c[0] for c in configs]
    labels = [c[2] for c in configs]
    
    metrics = ['T_ae', 't_PA1', 't_PA2', 'throughput']
    metric_labels = ['疏散时间', 'PA1时间', 'PA2时间', '吞吐量']
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(params))
    width = 0.2
    
    for i, (metric, mlabel) in enumerate(zip(metrics, metric_labels)):
        values = [indices[p][metric] for p in params]
        ax.bar(x + i*width, values, width, label=mlabel, alpha=0.8)
    
    ax.set_xlabel('参数')
    ax.set_ylabel('敏感性指标')
    ax.set_title('各参数对不同指标的敏感性对比')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\n保存敏感性对比图: {save_path}")
    
    plt.close()


def generate_sensitivity_report(results: List, indices: Dict, 
                                configs: List, output_dir: str):
    """生成敏感性分析报告"""
    
    report_path = f"{output_dir}/sensitivity_report.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("参数敏感性分析报告\n")
        f.write("="*60 + "\n\n")
        
        f.write("1. 实验设置\n")
        f.write("-"*40 + "\n")
        f.write("基准条件: PA1=3人/秒, PA2=3人/秒, 持续60秒\n")
        f.write("总到达人数: 360人\n\n")
        
        f.write("2. 参数取值范围\n")
        f.write("-"*40 + "\n")
        for param_name, param_label, result in results:
            f.write(f"{param_label} ({param_name}): {result.param_values}\n")
        f.write("\n")
        
        f.write("3. 敏感性指标汇总\n")
        f.write("-"*40 + "\n")
        f.write("敏感性指标 = (指标变化率) / (参数变化率)\n")
        f.write("指标越大，说明系统对该参数越敏感\n\n")
        
        f.write(f"{'参数':<15} {'疏散时间':<12} {'PA1时间':<12} {'PA2时间':<12} {'吞吐量':<12}\n")
        f.write("-"*60 + "\n")
        
        for param_name, param_label, _ in results:
            idx = indices[param_name]
            f.write(f"{param_label:<15} {idx['T_ae']:<12.2f} {idx['t_PA1']:<12.2f} "
                    f"{idx['t_PA2']:<12.2f} {idx['throughput']:<12.2f}\n")
        
        f.write("\n4. 关键发现\n")
        f.write("-"*40 + "\n")
        
        # 找出对各指标最敏感的参数
        for metric, mlabel in [('T_ae', '疏散时间'), ('t_PA1', 'PA1时间'), 
                                ('throughput', '吞吐量')]:
            max_param = max(indices.keys(), key=lambda p: indices[p][metric])
            max_label = next(c[2] for c in configs if c[0] == max_param)
            f.write(f"对{mlabel}影响最大的参数: {max_label} "
                    f"(敏感性指标={indices[max_param][metric]:.2f})\n")
        
        f.write("\n5. 详细结果\n")
        f.write("-"*40 + "\n")
        
        for param_name, param_label, result in results:
            f.write(f"\n{param_label} ({param_name}):\n")
            f.write(f"  取值: {result.param_values}\n")
            f.write(f"  T_ae: {[f'{v:.1f}' for v in result.T_ae]}\n")
            f.write(f"  t_PA1: {[f'{v:.1f}' for v in result.t_PA1]}\n")
            f.write(f"  t_PA2: {[f'{v:.1f}' for v in result.t_PA2]}\n")
    
    print(f"保存分析报告: {report_path}")
    
    # 同时保存CSV格式
    csv_path = f"{output_dir}/sensitivity_data.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("参数名,参数值,T_ae,t_PA1,t_PA2,峰值排队,峰值密度,吞吐量\n")
        for param_name, param_label, result in results:
            for i, val in enumerate(result.param_values):
                f.write(f"{param_name},{val},{result.T_ae[i]:.2f},{result.t_PA1[i]:.2f},"
                        f"{result.t_PA2[i]:.2f},{result.peak_queue_PW1[i]},"
                        f"{result.peak_K_PW2[i]:.2f},{result.throughput[i]:.3f}\n")
    
    print(f"保存CSV数据: {csv_path}")


if __name__ == "__main__":
    run_sensitivity_analysis()
