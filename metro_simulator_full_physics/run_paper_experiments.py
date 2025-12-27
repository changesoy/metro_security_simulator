"""
论文复现实验主程序

运行与论文设置匹配的实验：
- Group 1-5: 连续到达
- Group 6-10: 间隔到达

生成论文风格图表（英文标注）：
- 图A: PW1队列 - 连续到达（5组5色）
- 图B: PW1队列 - 间隔到达（5组5色）
- 图C: PW1队列对比（连续=蓝，间隔=红，线型区分组）
- Figure 5: PW2密度对比
- Figure 6: SA3密度箱线图
"""

import os
import sys
import yaml
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import SystemParameters
from src.data_structures import SystemState
from src.simulation_engine import simulation_step
from src.metrics import compute_average_transit_time, compute_access_egress_time
from src.paper_visualization import (
    plot_queue_pw1_bar,
    plot_queue_pw1_single_mode,
    plot_queue_pw1_comparison,
    plot_pw2_density_comparison,
    plot_sa3_density_boxplot,
    plot_congestion_evolution_english,
    plot_time_decomposition_english
)


def load_config(config_path: str = "config/experiments.yaml") -> dict:
    """从YAML文件加载实验配置"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_arrival_rate(t: float, q_base: float, pattern: str, 
                     pattern_config: dict) -> float:
    """
    根据到达模式获取t时刻的到达率
    
    Args:
        t: 当前时刻
        q_base: 基准到达率
        pattern: 模式名称（如 "continuous", "discontinuous"）
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
    获取最大到达时间（用于确定arrival_duration）
    
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


def run_single_experiment(params: SystemParameters, 
                          q_PA1: float, q_PA2: float,
                          arrival_pattern: str,
                          pattern_config: dict,
                          max_time: float = 800.0) -> SystemState:
    """
    运行单个实验
    
    Args:
        params: 系统参数
        q_PA1, q_PA2: PA1和PA2的到达率
        arrival_pattern: 到达模式名称
        pattern_config: 模式配置
        max_time: 最大仿真时间
        
    Returns:
        仿真完成后的系统状态
    """
    state = SystemState(params=params)
    
    # 从配置获取最大到达时间
    arrival_duration = get_max_arrival_time(pattern_config)
    
    while state.T < max_time:
        # 确定是否有乘客到达
        if state.T <= arrival_duration:
            q1 = get_arrival_rate(state.T, q_PA1, arrival_pattern, pattern_config)
            q2 = get_arrival_rate(state.T, q_PA2, arrival_pattern, pattern_config)
        else:
            q1, q2 = 0.0, 0.0
        
        # 执行仿真步骤
        simulation_step(state, q1, q2)
        
        # 检查是否终止
        if state.T > arrival_duration + 10:
            if state.get_D_pass() == len(state.passengers) and len(state.passengers) > 0:
                break
    
    return state


def run_paper_experiments(output_dir: str = "outputs/paper_reproduction"):
    """
    运行所有实验并生成论文风格图表
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/figures", exist_ok=True)
    os.makedirs(f"{output_dir}/data", exist_ok=True)
    
    print("\n" + "="*70)
    print("论文复现实验")
    print("="*70)
    
    # 加载配置
    config = load_config()
    arrival_patterns = config.get('arrival_patterns', {})
    experiments = config.get('experiment_groups', [])
    
    params = SystemParameters()
    
    # 存储结果
    continuous_states = []  # Group 1-5
    pulsed_states = []      # Group 6-10
    all_results = []
    
    # 运行实验
    for exp in experiments:
        name = exp['name']
        q_PA1 = exp['q_PA1']
        q_PA2 = exp['q_PA2']
        pattern = exp.get('arrival_pattern', 'continuous')
        max_time = exp.get('max_time', 800.0)
        
        # 获取模式配置
        pattern_config = arrival_patterns.get(pattern, {'type': 'uniform', 'duration': 60.0})
        
        print(f"\n运行: {name}")
        print(f"  模式: {pattern}, PA1={q_PA1}, PA2={q_PA2}")
        
        state = run_single_experiment(
            params, q_PA1, q_PA2, pattern, pattern_config, max_time
        )
        
        # 计算指标
        T_ae = compute_access_egress_time(state)
        avg_times = compute_average_transit_time(state)
        
        print(f"  T_ae: {T_ae:.1f}s, PA1: {avg_times['t_avg_PA1']:.1f}s, PA2: {avg_times['t_avg_PA2']:.1f}s")
        
        # 存储结果
        result = {
            'name': name,
            'pattern': pattern,
            'q_PA1': q_PA1,
            'q_PA2': q_PA2,
            'T_ae': T_ae,
            't_PA1': avg_times['t_avg_PA1'],
            't_PA2': avg_times['t_avg_PA2'],
            'n_PA1': avg_times['n_PA1'],
            'n_PA2': avg_times['n_PA2'],
            'state': state
        }
        all_results.append(result)
        
        # 分类
        if pattern == 'continuous':
            continuous_states.append((name, state))
        else:
            pulsed_states.append((name, state))
    
    # 生成图表
    print("\n" + "-"*50)
    print("生成图表...")
    print("-"*50)
    
    # 图A: PW1队列 - 连续到达（5组5色）
    if continuous_states:
        plot_queue_pw1_single_mode(
            continuous_states,
            mode_name="Continuous",
            save_path=f"{output_dir}/figures/queue_pw1_continuous.png"
        )
    
    # 图B: PW1队列 - 间隔到达（5组5色）
    if pulsed_states:
        plot_queue_pw1_single_mode(
            pulsed_states,
            mode_name="Discontinuous",
            save_path=f"{output_dir}/figures/queue_pw1_discontinuous.png"
        )
    
    # 图C: PW1队列对比（连续=蓝，间隔=红）
    if continuous_states and pulsed_states:
        plot_queue_pw1_comparison(
            continuous_states,
            pulsed_states,
            save_path=f"{output_dir}/figures/queue_pw1_comparison.png"
        )
    
    # Figure 4: Queue at PW1 bar chart (for Group 1)
    if continuous_states:
        plot_queue_pw1_bar(
            continuous_states[0][1], 
            group_name="Group 1",
            save_path=f"{output_dir}/figures/fig4_queue_pw1_bar.png"
        )
    
    # Figure 5: PW2 density comparison
    if continuous_states and pulsed_states:
        plot_pw2_density_comparison(
            continuous_states,
            pulsed_states,
            save_path=f"{output_dir}/figures/fig5_pw2_density_comparison.png"
        )
    
    # Figure 6: SA3 density box plot
    if continuous_states and pulsed_states:
        plot_sa3_density_boxplot(
            continuous_states,
            pulsed_states,
            save_path=f"{output_dir}/figures/fig6_sa3_density_boxplot.png"
        )
    
    # Additional figures for each group
    for result in all_results:
        name = result['name']
        state = result['state']
        
        # Congestion evolution
        plot_congestion_evolution_english(
            state, params, title=f"- {name}",
            save_path=f"{output_dir}/figures/evolution_{name}.png"
        )
        
        # Time decomposition
        plot_time_decomposition_english(
            state, title=f"- {name}",
            save_path=f"{output_dir}/figures/time_decomp_{name}.png"
        )
    
    # Save results table
    save_results_table(all_results, output_dir)
    
    # Generate README
    generate_readme(output_dir)
    
    print("\n" + "="*70)
    print("Experiment Complete!")
    print(f"Output directory: {output_dir}")
    print("="*70)
    
    return all_results


def save_results_table(results: List[dict], output_dir: str):
    """保存结果表为CSV和格式化文本"""
    
    # CSV格式
    csv_path = f"{output_dir}/data/results_summary.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("Group,Pattern,PA1_Rate,PA2_Rate,T_ae,t_PA1,t_PA2,n_PA1,n_PA2\n")
        for r in results:
            f.write(f"{r['name']},{r['pattern']},{r['q_PA1']},{r['q_PA2']},"
                    f"{r['T_ae']:.2f},{r['t_PA1']:.2f},{r['t_PA2']:.2f},"
                    f"{r['n_PA1']},{r['n_PA2']}\n")
    print(f"  保存: {csv_path}")
    
    # 格式化文本表格
    txt_path = f"{output_dir}/data/results_table.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("实验结果汇总\n")
        f.write("="*80 + "\n\n")
        
        f.write("连续到达 (Group 1-5):\n")
        f.write("-"*60 + "\n")
        f.write(f"{'Group':<10} {'PA1':<6} {'PA2':<6} {'T_ae':<10} {'t_PA1':<10} {'t_PA2':<10}\n")
        f.write("-"*60 + "\n")
        for r in results:
            if r['pattern'] == 'continuous':
                f.write(f"{r['name']:<10} {r['q_PA1']:<6} {r['q_PA2']:<6} "
                        f"{r['T_ae']:<10.1f} {r['t_PA1']:<10.1f} {r['t_PA2']:<10.1f}\n")
        
        f.write("\n间隔到达 (Group 6-10):\n")
        f.write("-"*60 + "\n")
        f.write(f"{'Group':<10} {'PA1':<6} {'PA2':<6} {'T_ae':<10} {'t_PA1':<10} {'t_PA2':<10}\n")
        f.write("-"*60 + "\n")
        for r in results:
            if r['pattern'] != 'continuous':  # discontinuous 或其他非连续模式
                f.write(f"{r['name']:<10} {r['q_PA1']:<6} {r['q_PA2']:<6} "
                        f"{r['T_ae']:<10.1f} {r['t_PA1']:<10.1f} {r['t_PA2']:<10.1f}\n")
    
    print(f"  保存: {txt_path}")
    
    # 保存使用的参数
    save_parameters_used(output_dir)


def save_parameters_used(output_dir: str):
    """保存本次实验使用的参数（中文）"""
    
    params = SystemParameters()
    
    param_path = f"{output_dir}/data/parameters_used.txt"
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
    
    print(f"  保存: {param_path}")


def generate_readme(output_dir: str):
    """生成README文件，说明输出内容"""
    
    readme_path = f"{output_dir}/README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("PAPER REPRODUCTION EXPERIMENT OUTPUTS\n")
        f.write("============================================================\n")
        f.write("\n")
        f.write("This directory contains the results of experiments reproducing\n")
        f.write("the paper's analysis of metro security checkpoint congestion.\n")
        f.write("\n")
        f.write("============================================================\n")
        f.write("DIRECTORY STRUCTURE\n")
        f.write("============================================================\n")
        f.write("\n")
        f.write("figures/\n")
        f.write("    queue_pw1_continuous.png - PW1 queue, Groups 1-5 (5 colors)\n")
        f.write("    queue_pw1_discontinuous.png - PW1 queue, Groups 6-10 (5 colors)\n")
        f.write("    queue_pw1_comparison.png - Blue=continuous, Red=discontinuous\n")
        f.write("    \n")
        f.write("    fig4_queue_pw1_bar.png - Bar chart for Group 1 (paper Fig.4)\n")
        f.write("    fig5_pw2_density_comparison.png - PW2 density (paper Fig.5)\n")
        f.write("    fig6_sa3_density_boxplot.png - SA3 boxplot (paper Fig.6)\n")
        f.write("    \n")
        f.write("    evolution_GroupX.png - Congestion dynamics (4 subplots)\n")
        f.write("    time_decomp_GroupX.png - Time breakdown (basic vs extra)\n")
        f.write("\n")
        f.write("data/\n")
        f.write("    results_summary.csv - Complete results in CSV format\n")
        f.write("    results_table.txt - Formatted results table\n")
        f.write("\n")
        f.write("============================================================\n")
        f.write("EXPERIMENT GROUPS\n")
        f.write("============================================================\n")
        f.write("\n")
        f.write("Continuous Arrival (Group 1-5):\n")
        f.write("    - Uniform arrival rate for 60 seconds\n")
        f.write("    - Group 1: PA1=1, PA2=5 ped/s\n")
        f.write("    - Group 2: PA1=2, PA2=4 ped/s\n")
        f.write("    - Group 3: PA1=3, PA2=3 ped/s\n")
        f.write("    - Group 4: PA1=4, PA2=2 ped/s\n")
        f.write("    - Group 5: PA1=5, PA2=1 ped/s\n")
        f.write("\n")
        f.write("Discontinuous Arrival (Group 6-10):\n")
        f.write("    - Arrival in 0-25s and 36-70s, gap in 25-36s\n")
        f.write("    - Same PA1/PA2 rates as Groups 1-5\n")
        f.write("\n")
        f.write("============================================================\n")
    
    print(f"  Saved: {readme_path}")
    
    # Also create README for figures
    fig_readme_path = f"{output_dir}/figures/FIGURES_README.txt"
    with open(fig_readme_path, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("FIGURE DESCRIPTIONS\n")
        f.write("============================================================\n")
        f.write("\n")
        f.write("queue_pw1_continuous.png\n")
        f.write("------------------------\n")
        f.write("PW1 Queue Length - Continuous Arrival (Groups 1-5)\n")
        f.write("X-axis: Time [s]\n")
        f.write("Y-axis: Number of passengers queuing\n")
        f.write("5 lines with 5 different colors, one per group.\n")
        f.write("\n")
        f.write("queue_pw1_discontinuous.png\n")
        f.write("---------------------------\n")
        f.write("PW1 Queue Length - Discontinuous Arrival (Groups 6-10)\n")
        f.write("Same format as above.\n")
        f.write("\n")
        f.write("queue_pw1_comparison.png\n")
        f.write("------------------------\n")
        f.write("Comparison of both arrival patterns.\n")
        f.write("Blue lines = Continuous (Groups 1-5)\n")
        f.write("Red lines = Discontinuous (Groups 6-10)\n")
        f.write("Line styles distinguish groups within each color.\n")
        f.write("\n")
        f.write("fig4_queue_pw1_bar.png\n")
        f.write("----------------------\n")
        f.write("Bar chart of PW1 queue for Group 1 (paper Figure 4 style).\n")
        f.write("\n")
        f.write("fig5_pw2_density_comparison.png\n")
        f.write("-------------------------------\n")
        f.write("PW2 density comparison (paper Figure 5 style).\n")
        f.write("(a) Continuous arrival - Groups 1-5\n")
        f.write("(b) Discontinuous arrival - Groups 6-10\n")
        f.write("\n")
        f.write("fig6_sa3_density_boxplot.png\n")
        f.write("----------------------------\n")
        f.write("SA3 density box plot (paper Figure 6 style).\n")
        f.write("Shows distribution of density values per group.\n")
        f.write("\n")
        f.write("evolution_GroupX.png\n")
        f.write("--------------------\n")
        f.write("Congestion dynamics for each group (4 subplots):\n")
        f.write("  1. Population in each area over time\n")
        f.write("  2. Density evolution (K_PW2, K_SA3)\n")
        f.write("  3. Queue length at PW1 entrance\n")
        f.write("  4. Cumulative passengers passed\n")
        f.write("\n")
        f.write("time_decomp_GroupX.png\n")
        f.write("----------------------\n")
        f.write("Transit time decomposition:\n")
        f.write("  Left: PA1 (with luggage)\n")
        f.write("  Right: PA2 (without luggage)\n")
        f.write("  Blue bars: Basic time (walking + service)\n")
        f.write("  Red bars: Extra time (queuing delays)\n")
        f.write("\n")
        f.write("============================================================\n")
    
    print(f"  Saved: {fig_readme_path}")


if __name__ == "__main__":
    run_paper_experiments()
