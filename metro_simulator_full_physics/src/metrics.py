"""
指标计算模块
实现论文公式 (13)-(14) 和其他统计指标
"""

from typing import Dict, List
import pandas as pd
from src.config import PassengerType, Position
from src.data_structures import SystemState, Passenger


def compute_average_transit_time(state: SystemState) -> Dict[str, float]:
    """计算平均通行时间 - 公式(13)(14)
    
    公式(13) PA1平均时间：
    t_PA1 = (1/D_PA1) × Σ(t_SA1_basic + t_SA1_add + t_PW_basic + t_SA2_add + t_SA3_basic + t_SA3_add)
    
    公式(14) PA2平均时间：
    t_PA2 = (1/D_PA2) × Σ(t_SA1_basic + t_SA1_add + t_PW_basic + t_SA2_add + t_SA3_basic + t_SA3_add)
    
    Args:
        state: 系统状态
        
    Returns:
        包含 t_avg_PA1, t_avg_PA2, n_PA1, n_PA2 的字典
    """
    # 筛选已通过系统的乘客
    passed = [p for p in state.passengers if p.position == Position.PASSED]
    
    PA1_list = [p for p in passed if p.ptype == PassengerType.PA1]
    PA2_list = [p for p in passed if p.ptype == PassengerType.PA2]
    
    # 计算PA1平均时间
    if PA1_list:
        total_PA1 = sum(p.total_time() for p in PA1_list)
        t_avg_PA1 = total_PA1 / len(PA1_list)
    else:
        t_avg_PA1 = 0.0
    
    # 计算PA2平均时间
    if PA2_list:
        total_PA2 = sum(p.total_time() for p in PA2_list)
        t_avg_PA2 = total_PA2 / len(PA2_list)
    else:
        t_avg_PA2 = 0.0
    
    return {
        't_avg_PA1': t_avg_PA1,
        't_avg_PA2': t_avg_PA2,
        'n_PA1': len(PA1_list),
        'n_PA2': len(PA2_list)
    }


def compute_access_egress_time(state: SystemState) -> float:
    """计算Access/Egress Time
    
    定义：最后一名乘客离开系统的时刻
    
    Args:
        state: 系统状态
        
    Returns:
        Access/Egress Time (s)
    """
    passed = [p for p in state.passengers if p.position == Position.PASSED]
    
    if passed:
        return max(p.t_exit_system for p in passed)
    else:
        return state.T


def compute_time_breakdown(state: SystemState) -> Dict[str, Dict[str, float]]:
    """计算时间分解统计
    
    Args:
        state: 系统状态
        
    Returns:
        PA1和PA2的各时间分量统计
    """
    passed = [p for p in state.passengers if p.position == Position.PASSED]
    PA1_list = [p for p in passed if p.ptype == PassengerType.PA1]
    PA2_list = [p for p in passed if p.ptype == PassengerType.PA2]
    
    result = {'PA1': {}, 'PA2': {}}
    
    if PA1_list:
        n = len(PA1_list)
        result['PA1'] = {
            't_SA1_basic': sum(p.t_SA1_basic for p in PA1_list) / n,
            't_SA1_add': sum(p.t_SA1_add for p in PA1_list) / n,
            't_PW_basic': sum(p.t_PW_basic for p in PA1_list) / n,
            't_SA2_add': sum(p.t_SA2_add for p in PA1_list) / n,
            't_SA3_basic': sum(p.t_SA3_basic for p in PA1_list) / n,
            't_SA3_add': sum(p.t_SA3_add for p in PA1_list) / n,
        }
    
    if PA2_list:
        n = len(PA2_list)
        result['PA2'] = {
            't_SA1_basic': sum(p.t_SA1_basic for p in PA2_list) / n,
            't_SA1_add': sum(p.t_SA1_add for p in PA2_list) / n,
            't_PW_basic': sum(p.t_PW_basic for p in PA2_list) / n,
            't_SA2_add': sum(p.t_SA2_add for p in PA2_list) / n,
            't_SA3_basic': sum(p.t_SA3_basic for p in PA2_list) / n,
            't_SA3_add': sum(p.t_SA3_add for p in PA2_list) / n,
        }
    
    return result


def extract_time_series(state: SystemState) -> pd.DataFrame:
    """提取时间序列数据
    
    Args:
        state: 系统状态
        
    Returns:
        包含历史数据的DataFrame
    """
    return pd.DataFrame(state.history)


def extract_passenger_data(state: SystemState) -> pd.DataFrame:
    """提取乘客数据
    
    Args:
        state: 系统状态
        
    Returns:
        包含每个乘客详细信息的DataFrame
    """
    data = []
    for p in state.passengers:
        data.append({
            'index': p.index,
            'type': p.ptype.value,
            'position': p.position.value,
            't_enter_SA1': p.t_enter_SA1,
            't_enter_PW': p.t_enter_PW,
            't_enter_SA3': p.t_enter_SA3,
            't_exit_system': p.t_exit_system,
            't_SA1_basic': p.t_SA1_basic,
            't_SA1_add': p.t_SA1_add,
            't_PW_basic': p.t_PW_basic,
            't_SA2_add': p.t_SA2_add,
            't_SA3_basic': p.t_SA3_basic,
            't_SA3_add': p.t_SA3_add,
            'total_time': p.total_time()
        })
    return pd.DataFrame(data)


def generate_summary_report(state: SystemState, group_name: str = "") -> str:
    """生成汇总报告
    
    Args:
        state: 系统状态
        group_name: 实验组名称
        
    Returns:
        格式化的报告字符串
    """
    avg_times = compute_average_transit_time(state)
    T_ae = compute_access_egress_time(state)
    breakdown = compute_time_breakdown(state)
    
    report = []
    report.append(f"{'='*60}")
    report.append(f"实验报告: {group_name}")
    report.append(f"{'='*60}")
    report.append("")
    report.append("【核心指标】")
    report.append(f"  Access/Egress Time: {T_ae:.2f} s")
    report.append(f"  PA1平均通行时间: {avg_times['t_avg_PA1']:.2f} s (n={avg_times['n_PA1']})")
    report.append(f"  PA2平均通行时间: {avg_times['t_avg_PA2']:.2f} s (n={avg_times['n_PA2']})")
    report.append("")
    
    if breakdown['PA1']:
        report.append("【PA1时间分解】")
        for k, v in breakdown['PA1'].items():
            report.append(f"  {k}: {v:.2f} s")
        report.append("")
    
    if breakdown['PA2']:
        report.append("【PA2时间分解】")
        for k, v in breakdown['PA2'].items():
            report.append(f"  {k}: {v:.2f} s")
        report.append("")
    
    # 峰值统计
    report.append("【峰值统计】")
    if state.history['D_PW1']:
        report.append(f"  PW1最大人数: {max(state.history['D_PW1'])}")
    if state.history['queue_PW1']:
        report.append(f"  PW1前最大排队: {max(state.history['queue_PW1'])}")
    if state.history['K_PW2']:
        report.append(f"  PW2最大密度: {max(state.history['K_PW2']):.4f} ped/m²")
    if state.history['K_SA3']:
        report.append(f"  SA3最大密度: {max(state.history['K_SA3']):.4f} ped/m²")
    
    return '\n'.join(report)
