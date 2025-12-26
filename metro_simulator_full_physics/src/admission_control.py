"""
准入判定模块
严格实现论文公式 (9)-(12)

核心原则：
- 准入判定基于"时间步开始时的状态"
- 返回允许进入的人数，不修改乘客状态
- 按乘客index顺序判定（先编号先优先）
"""

from typing import List
from src.config import SystemParameters
from src.data_structures import Passenger


def check_PW1_admission(D_PW1_current: int, params: SystemParameters) -> int:
    """检查PW1准入人数 - 公式(9)
    
    论文公式(9): D_in,PW1,T = L_SE/H - D_PW1,T
    
    物理解释：
    - 传送带上放的是"包"而非"人"
    - 包的厚度H_bag ≈ 0.15m（比人体厚度0.5m小）
    - 因此传送带容量 = L_SE / H_bag ≈ 15人
    
    Args:
        D_PW1_current: PW1当前人数
        params: 系统参数
        
    Returns:
        允许进入的人数（>=0）
    """
    capacity = int(params.L_SE / params.H_bag)  # 2.3/0.15 ≈ 15人
    available = capacity - D_PW1_current
    return max(0, available)


def check_PW2_admission(D_PW2_current: int, K_PW2_current: float,
                        params: SystemParameters) -> int:
    """检查PW2准入人数 - 公式(10)(11)
    
    PW2采用双重约束：
    1. 体宽约束 - 公式(10): 并排进入人数 <= W_PW2 / W_B
    2. 密度约束 - 公式(11): 可容纳人数 = A_PW2 × (K_max - K_current)
    
    取两者最小值作为准入上限
    
    Args:
        D_PW2_current: PW2当前人数
        K_PW2_current: PW2当前密度 (ped/m²)
        params: 系统参数
        
    Returns:
        允许进入的人数（>=0）
    """
    # 约束1：体宽约束 - 公式(10)
    # 每个时间步最多并排进入的人数
    width_limit = int(params.W_PW2 / params.W_B)  # 2.24/0.5 ≈ 4人
    
    # 约束2：密度约束 - 公式(11)
    # 区域剩余容量
    density_limit = int(params.A_PW2 * (params.K_PW2_max - K_PW2_current))
    density_limit = max(0, density_limit)
    
    # 取最小值
    return min(width_limit, density_limit)


def check_SA3_admission(D_SA3_current: int, K_SA3_current: float,
                        params: SystemParameters) -> int:
    """检查SA3准入人数 - 公式(12)
    
    SA3采用密度约束：
    公式(12): D_in,SA3,T = A_SA3 × (K_max - K_current)
    
    Args:
        D_SA3_current: SA3当前人数
        K_SA3_current: SA3当前密度 (ped/m²)
        params: 系统参数
        
    Returns:
        允许进入的人数（>=0）
    """
    available = int(params.A_SA3 * (params.K_SA3_max - K_SA3_current))
    return max(0, available)


def check_gate_admission(free_gates: int) -> int:
    """检查闸机准入人数
    
    闸机采用并行服务器模式：
    - 5台闸机，每台服务时间3.5s
    - 空闲闸机数 = 可同时进入人数
    
    Args:
        free_gates: 当前空闲闸机数
        
    Returns:
        允许进入的人数（>=0）
    """
    return max(0, free_gates)
