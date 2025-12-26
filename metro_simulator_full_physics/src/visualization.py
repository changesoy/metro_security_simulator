"""
可视化模块
生成论文风格的图表（对应Figure 4-6）
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import os
from typing import Dict, List, Optional
from src.data_structures import SystemState
from src.metrics import extract_time_series

# 设置字体
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
mpl.rcParams['axes.unicode_minus'] = False


def plot_PW1_queue(state: SystemState, save_path: Optional[str] = None,
                   show: bool = True, title_suffix: str = "") -> None:
    """绘制PW1排队长度曲线（对应Figure 4）
    
    注意：这里绘制的是"PW1前的排队人数"（SA1中等待进入PW1的PA1），
    而不是"PW1内的人数"。
    """
    df = extract_time_series(state)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 使用queue_PW1（PW1前排队人数）
    if 'queue_PW1' in df.columns:
        ax.plot(df['T'], df['queue_PW1'], linewidth=2, color='#1f77b4')
    else:
        # 兼容旧版本，使用D_PW1
        ax.plot(df['T'], df['D_PW1'], linewidth=2, color='#1f77b4')
    
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Number of Passengers', fontsize=12)
    ax.set_title(f'Queue Length in front of Passageway1 {title_suffix}', fontsize=14)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


def plot_PW2_density(state: SystemState, save_path: Optional[str] = None,
                     show: bool = True, title_suffix: str = "") -> None:
    """绘制PW2密度曲线（对应Figure 5）"""
    df = extract_time_series(state)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df['T'], df['K_PW2'], linewidth=2, color='#ff7f0e')
    
    # 添加阈值线
    ax.axhline(y=state.params.K_PW2_init, color='g', linestyle='--',
               linewidth=1.5, alpha=0.7, label=f'K_init ({state.params.K_PW2_init})')
    ax.axhline(y=state.params.K_PW2_max, color='r', linestyle='--',
               linewidth=1.5, alpha=0.7, label=f'K_max ({state.params.K_PW2_max})')
    
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Density (ped/m²)', fontsize=12)
    ax.set_title(f'Passageway2 Density {title_suffix}', fontsize=14)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


def plot_SA3_density(state: SystemState, save_path: Optional[str] = None,
                     show: bool = True, title_suffix: str = "") -> None:
    """绘制SA3密度曲线（对应Figure 6）"""
    df = extract_time_series(state)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df['T'], df['K_SA3'], linewidth=2, color='#2ca02c')
    
    # 添加阈值线
    ax.axhline(y=state.params.K_SA3_init, color='g', linestyle='--',
               linewidth=1.5, alpha=0.7, label=f'K_init ({state.params.K_SA3_init})')
    ax.axhline(y=state.params.K_SA3_max, color='r', linestyle='--',
               linewidth=1.5, alpha=0.7, label=f'K_max ({state.params.K_SA3_max})')
    
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Density (ped/m²)', fontsize=12)
    ax.set_title(f'Subarea3 Density {title_suffix}', fontsize=14)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


def plot_passed_passengers(state: SystemState, save_path: Optional[str] = None,
                           show: bool = True, title_suffix: str = "") -> None:
    """绘制已通过乘客数曲线"""
    df = extract_time_series(state)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df['T'], df['D_pass'], linewidth=2, color='#9467bd')
    
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Number of Passengers', fontsize=12)
    ax.set_title(f'Cumulative Passed Passengers {title_suffix}', fontsize=14)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


def plot_comparison(results: Dict[str, SystemState], metric: str,
                    save_path: Optional[str] = None, show: bool = True) -> None:
    """绘制多组实验对比图
    
    Args:
        results: {group_name: SystemState} 字典
        metric: 要对比的指标（'queue_PW1', 'K_PW2', 'K_SA3', 'D_pass'）
        save_path: 保存路径
        show: 是否显示
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, (name, state) in enumerate(results.items()):
        df = extract_time_series(state)
        color = colors[i % len(colors)]
        
        if metric in df.columns:
            ax.plot(df['T'], df[metric], linewidth=2, color=color, label=name)
    
    # 设置标题和标签
    titles = {
        'queue_PW1': 'PW1 Queue Length Comparison',
        'D_PW1': 'PW1 Passengers Comparison',
        'K_PW2': 'PW2 Density Comparison',
        'K_SA3': 'SA3 Density Comparison',
        'D_pass': 'Passed Passengers Comparison'
    }
    ylabels = {
        'queue_PW1': 'Number of Passengers',
        'D_PW1': 'Number of Passengers',
        'K_PW2': 'Density (ped/m²)',
        'K_SA3': 'Density (ped/m²)',
        'D_pass': 'Number of Passengers'
    }
    
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel(ylabels.get(metric, 'Value'), fontsize=12)
    ax.set_title(titles.get(metric, f'{metric} Comparison'), fontsize=14)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=10)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


def plot_all_comparisons(results: Dict[str, SystemState], output_dir: str) -> None:
    """生成所有对比图
    
    Args:
        results: 实验结果字典
        output_dir: 输出目录
    """
    os.makedirs(output_dir, exist_ok=True)
    
    metrics = ['queue_PW1', 'K_PW2', 'K_SA3', 'D_pass']
    
    for metric in metrics:
        save_path = os.path.join(output_dir, f'comparison_{metric}.png')
        plot_comparison(results, metric, save_path=save_path, show=False)
        print(f"  保存图表: {save_path}")
