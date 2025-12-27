"""
实验运行器模块
负责加载配置、批量运行实验、保存结果
"""

import os
import yaml
import pandas as pd
from typing import Dict, List
from src.config import SystemParameters
from src.data_structures import SystemState
from src.simulation_engine import run_simulation
from src.metrics import (
    compute_average_transit_time,
    compute_access_egress_time,
    generate_summary_report,
    extract_time_series,
    extract_passenger_data
)
from src.visualization import plot_all_comparisons


def load_experiment_config(config_path: str = None) -> Dict:
    """从YAML加载实验配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    if config_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        config_path = os.path.join(project_root, 'config', 'experiments.yaml')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def get_arrival_rate(t: float, q_base: float, pattern_config: dict) -> float:
    """
    根据到达模式获取t时刻的到达率
    
    Args:
        t: 当前时刻
        q_base: 基准到达率
        pattern_config: 模式配置参数
        
    Returns:
        t时刻的到达率
    """
    pattern_type = pattern_config.get('type', 'uniform')
    
    if pattern_type == "uniform":
        # 连续均匀到达
        duration = pattern_config.get('duration', 60.0)
        if t <= duration:
            return q_base
        else:
            return 0.0
            
    elif pattern_type == "segments":
        # 间隔到达：检查t是否在任一时段内
        segments = pattern_config.get('segments', [[0, 60]])
        for seg in segments:
            start, end = seg[0], seg[1]
            if start <= t <= end:
                return q_base
        return 0.0
        
    else:
        # 默认：连续到达
        return q_base


def get_max_arrival_time(pattern_config: dict) -> float:
    """
    获取最大到达时间
    
    Args:
        pattern_config: 模式配置参数
        
    Returns:
        最大到达时间
    """
    pattern_type = pattern_config.get('type', 'uniform')
    
    if pattern_type == "uniform":
        return pattern_config.get('duration', 60.0)
    elif pattern_type == "segments":
        segments = pattern_config.get('segments', [[0, 60]])
        return max(seg[1] for seg in segments)
    else:
        return 60.0


def run_single_experiment(group: Dict, arrival_patterns: Dict = None, 
                          verbose: bool = True) -> SystemState:
    """运行单个实验组
    
    Args:
        group: 实验组配置
        arrival_patterns: 到达模式配置字典
        verbose: 是否显示详细信息
        
    Returns:
        完成仿真的系统状态
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"运行实验: {group['name']}")
        print(f"描述: {group['description']}")
        print(f"{'='*60}")
    
    params = SystemParameters()
    
    q_PA1 = group['q_PA1']
    q_PA2 = group['q_PA2']
    max_time = group.get('max_time', 1000.0)
    
    # 获取到达模式配置
    pattern_name = group.get('arrival_pattern', 'continuous')
    if arrival_patterns and pattern_name in arrival_patterns:
        pattern_config = arrival_patterns[pattern_name]
    else:
        # 默认连续模式
        pattern_config = {'type': 'uniform', 'duration': 60.0}
    
    arrival_duration = get_max_arrival_time(pattern_config)
    
    if verbose:
        print(f"  到达率: PA1={q_PA1} ped/s, PA2={q_PA2} ped/s")
        print(f"  到达模式: {pattern_name}")
        print(f"  最大到达时间: {arrival_duration}s")
        print(f"  最大仿真时间: {max_time}s")
    
    # 使用自定义到达率的仿真
    state = SystemState(params=params)
    
    while state.T < max_time:
        # 根据模式获取当前到达率
        if state.T <= arrival_duration:
            curr_q_PA1 = get_arrival_rate(state.T, q_PA1, pattern_config)
            curr_q_PA2 = get_arrival_rate(state.T, q_PA2, pattern_config)
        else:
            curr_q_PA1, curr_q_PA2 = 0.0, 0.0
        
        # 执行仿真步骤
        from src.simulation_engine import simulation_step
        simulation_step(state, curr_q_PA1, curr_q_PA2)
        
        # 检查终止条件
        if state.T > arrival_duration + 10:
            if state.get_D_pass() == len(state.passengers) and len(state.passengers) > 0:
                break
    
    if verbose:
        avg_times = compute_average_transit_time(state)
        T_ae = compute_access_egress_time(state)
        print(f"\n【结果】")
        print(f"  总乘客数: {state.get_D_all()}")
        print(f"  已通过: {state.get_D_pass()}")
        print(f"  Access/Egress Time: {T_ae:.2f}s")
        print(f"  PA1平均时间: {avg_times['t_avg_PA1']:.2f}s (n={avg_times['n_PA1']})")
        print(f"  PA2平均时间: {avg_times['t_avg_PA2']:.2f}s (n={avg_times['n_PA2']})")
    
    return state


def run_all_experiments(config: Dict, verbose: bool = True) -> Dict[str, SystemState]:
    """运行所有实验组
    
    Args:
        config: 配置字典
        verbose: 是否显示详细信息
        
    Returns:
        {group_name: SystemState} 字典
    """
    results = {}
    groups = config['experiment_groups']
    arrival_patterns = config.get('arrival_patterns', {})
    
    for group in groups:
        state = run_single_experiment(group, arrival_patterns, verbose)
        results[group['name']] = state
    
    return results


def generate_comparison_table(results: Dict[str, SystemState], 
                               groups: List[Dict]) -> pd.DataFrame:
    """生成对比表格（对应论文Table 5）
    
    Args:
        results: 实验结果字典
        groups: 实验组配置列表
        
    Returns:
        对比表格DataFrame
    """
    data = []
    
    for group in groups:
        name = group['name']
        state = results[name]
        
        avg_times = compute_average_transit_time(state)
        T_ae = compute_access_egress_time(state)
        
        # 峰值统计
        peak_queue_PW1 = max(state.history['queue_PW1']) if state.history['queue_PW1'] else 0
        peak_K_PW2 = max(state.history['K_PW2']) if state.history['K_PW2'] else 0
        peak_K_SA3 = max(state.history['K_SA3']) if state.history['K_SA3'] else 0
        
        data.append({
            'Group': name,
            'q_PA1 (ped/s)': group['q_PA1'],
            'q_PA2 (ped/s)': group['q_PA2'],
            'n_PA1': avg_times['n_PA1'],
            'n_PA2': avg_times['n_PA2'],
            'n_total': avg_times['n_PA1'] + avg_times['n_PA2'],
            't_avg_PA1 (s)': round(avg_times['t_avg_PA1'], 2),
            't_avg_PA2 (s)': round(avg_times['t_avg_PA2'], 2),
            'T_access_egress (s)': round(T_ae, 2),
            'peak_queue_PW1': peak_queue_PW1,
            'peak_K_PW2 (ped/m²)': round(peak_K_PW2, 4),
            'peak_K_SA3 (ped/m²)': round(peak_K_SA3, 4),
        })
    
    return pd.DataFrame(data)


def save_results(results: Dict[str, SystemState], groups: List[Dict],
                 config: Dict, output_dir: str = None) -> None:
    """保存所有结果
    
    Args:
        results: 实验结果字典
        groups: 实验组配置列表
        config: 完整配置字典
        output_dir: 输出目录
    """
    output_settings = config.get('output_settings', {})
    
    if output_dir is None:
        output_dir = output_settings.get('output_dir', 'outputs')
    
    # 创建目录结构
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'data'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'figures'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'reports'), exist_ok=True)
    
    print(f"\n{'='*60}")
    print("保存结果...")
    print(f"{'='*60}")
    
    # 1. 保存对比表格
    df_comparison = generate_comparison_table(results, groups)
    comparison_path = os.path.join(output_dir, 'reports', 'comparison_table.csv')
    df_comparison.to_csv(comparison_path, index=False)
    print(f"  保存对比表: {comparison_path}")
    
    # 2. 保存各组数据
    for group in groups:
        name = group['name']
        state = results[name]
        
        # 时间序列
        df_ts = extract_time_series(state)
        ts_path = os.path.join(output_dir, 'data', f'{name}_timeseries.csv')
        df_ts.to_csv(ts_path, index=False)
        
        # 乘客数据
        df_pax = extract_passenger_data(state)
        pax_path = os.path.join(output_dir, 'data', f'{name}_passengers.csv')
        df_pax.to_csv(pax_path, index=False)
    
    print(f"  保存时间序列和乘客数据到: {os.path.join(output_dir, 'data')}")
    
    # 3. 保存使用的参数
    save_parameters_used(output_dir)
    
    # 4. 生成图表
    if output_settings.get('generate_figures', True):
        figures_dir = os.path.join(output_dir, 'figures')
        plot_all_comparisons(results, figures_dir, groups)
    
    # 5. 生成汇总报告
    report_lines = []
    report_lines.append("Metro Security Simulator - 实验报告")
    report_lines.append("="*60)
    report_lines.append("")
    report_lines.append("【论文对比表（Table 5）】")
    report_lines.append("")
    report_lines.append(df_comparison.to_string(index=False))
    report_lines.append("")
    report_lines.append("")
    
    for group in groups:
        name = group['name']
        state = results[name]
        report_lines.append(generate_summary_report(state, name))
        report_lines.append("")
    
    report_path = os.path.join(output_dir, 'reports', 'experiment_summary.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f"  保存汇总报告: {report_path}")
    
    print(f"\n结果已保存到: {output_dir}")


def save_parameters_used(output_dir: str):
    """保存本次实验使用的参数（中文）"""
    
    params = SystemParameters()
    
    param_path = os.path.join(output_dir, 'data', 'parameters_used.txt')
    with open(param_path, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("本次实验使用的系统参数\n")
        f.write("="*60 + "\n\n")
        
        f.write("【几何参数】\n")
        f.write("-"*40 + "\n")
        f.write(f"入口到PW1(安检)距离: {params.L_EN_PW1} m\n")
        f.write(f"入口到PW2(快速通道)距离: {params.L_EN_PW2} m\n")
        f.write(f"PW2通道长度: {params.L_PW2} m\n")
        f.write(f"PW2通道面积: {params.A_PW2} m^2\n")
        f.write(f"PW2通道宽度: {params.W_PW2:.2f} m\n")
        f.write(f"X光机传送带长度: {params.L_SE} m\n")
        f.write(f"PW1到闸机距离: {params.L_PW1_GA} m\n")
        f.write(f"PW2到闸机距离: {params.L_PW2_GA} m\n")
        f.write(f"SA3(闸机前区域)面积: {params.A_SA3} m^2\n")
        f.write("\n")
        
        f.write("【设备参数】\n")
        f.write("-"*40 + "\n")
        f.write(f"闸机数量: {params.N_G} 台\n")
        f.write(f"PW1(安检)容量: {params.C_PW1} 人\n")
        f.write(f"传送带速度: {params.v_SE} m/s\n")
        f.write("\n")
        
        f.write("【服务时间参数】\n")
        f.write("-"*40 + "\n")
        f.write(f"放物时间: {params.t_pi} s\n")
        f.write(f"取物时间: {params.t_ti} s\n")
        f.write(f"PW1基本通过时间: {params.t_PW1_basic:.1f} s\n")
        f.write(f"闸机刷卡/扫码时间: {params.t_s} s\n")
        f.write("\n")
        
        f.write("【速度参数】\n")
        f.write("-"*40 + "\n")
        f.write(f"自由流行走速度: {params.v0} m/s\n")
        f.write(f"PW2自由流速度: {params.v_PW2_init} m/s\n")
        f.write(f"SA3自由流速度: {params.v_SA3_init} m/s\n")
        f.write("\n")
        
        f.write("【仿真参数】\n")
        f.write("-"*40 + "\n")
        f.write(f"时间步长: {params.dt} s\n")
        f.write("\n")
        
        f.write("="*60 + "\n")
        f.write("注: 如需修改参数，请编辑 config/experiments.yaml\n")
        f.write("    或修改 src/config.py 中的 SystemParameters 类\n")
        f.write("="*60 + "\n")
    
    print(f"  保存参数文件: {param_path}")
