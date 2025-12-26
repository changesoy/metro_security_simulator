"""
基本时间计算模块
严格实现论文公式 (1)-(8)

核心原则：
- 基本时间在乘客进入区域时一次性确定
- 基本时间是"无干扰通行时间"，不随后续状态变化
"""

from src.config import PassengerType, SystemParameters
from src.data_structures import Passenger


def compute_t_SA1_basic(passenger: Passenger, params: SystemParameters) -> float:
    """计算SA1基本通过时间 - 公式(1)(2)
    
    物理过程：从入口自由流行走到PW1/PW2入口
    
    公式(1) PA1: t = L_EN_PW1 / v0 = 5.36 / 1.61 ≈ 3.33s
    公式(2) PA2: t = L_EN_PW2 / v0 = 4.69 / 1.61 ≈ 2.91s
    
    Args:
        passenger: 乘客对象
        params: 系统参数
        
    Returns:
        SA1基本时间 (s)
    """
    if passenger.ptype == PassengerType.PA1:
        return params.L_EN_PW1 / params.v0
    else:
        return params.L_EN_PW2 / params.v0


def compute_t_PW1_basic(params: SystemParameters) -> float:
    """计算PW1基本通过时间 - 公式(3)
    
    物理过程：安检三阶段（放物→安检→取物）
    
    公式(3): t = t_pi + L_SE/v_SE + t_ti
              = 2.0 + 2.3/0.2 + 2.0
              = 2.0 + 11.5 + 2.0
              = 15.5s
    
    注意：这是固定时间，不受密度影响（传送带匀速运行）
    
    Args:
        params: 系统参数
        
    Returns:
        PW1基本时间 (s)，恒为15.5s
    """
    return params.t_pi + params.L_SE / params.v_SE + params.t_ti


def compute_t_PW2_basic(K_PW2: float, params: SystemParameters) -> float:
    """计算PW2基本通过时间 - 公式(4)(5)
    
    物理过程：快速通道行走
    
    公式(4): t = L_PW2 / v(K)
    公式(5): 速度-密度关系
    
    密度采用"进入PW2时刻的瞬时密度"，一次性确定。
    
    Args:
        K_PW2: 进入时刻的PW2密度 (ped/m²)
        params: 系统参数
        
    Returns:
        PW2基本时间 (s)
    """
    v = params.v_PW2(K_PW2)
    return params.L_PW2 / v


def compute_t_SA3_basic_PA1(K_SA3: float, params: SystemParameters) -> float:
    """计算PA1在SA3的基本通过时间 - 公式(6)
    
    物理过程：从PW1出口走到闸机 + 刷卡
    
    公式(6): t = L_PW1_GA / v(K) + t_s
    
    Args:
        K_SA3: 进入时刻的SA3密度 (ped/m²)
        params: 系统参数
        
    Returns:
        SA3基本时间 (s)
    """
    v = params.v_SA3(K_SA3)
    return params.L_PW1_GA / v + params.t_s


def compute_t_SA3_basic_PA2(K_SA3: float, params: SystemParameters) -> float:
    """计算PA2在SA3的基本通过时间 - 公式(7)
    
    物理过程：从PW2出口走到闸机 + 刷卡
    
    公式(7): t = L_PW2_GA / v(K) + t_s
    
    Args:
        K_SA3: 进入时刻的SA3密度 (ped/m²)
        params: 系统参数
        
    Returns:
        SA3基本时间 (s)
    """
    v = params.v_SA3(K_SA3)
    return params.L_PW2_GA / v + params.t_s


def compute_t_SA3_basic(passenger: Passenger, K_SA3: float, 
                        params: SystemParameters) -> float:
    """计算SA3基本通过时间（统一接口）
    
    根据乘客类型调用对应公式
    
    Args:
        passenger: 乘客对象
        K_SA3: 进入时刻的SA3密度 (ped/m²)
        params: 系统参数
        
    Returns:
        SA3基本时间 (s)
    """
    if passenger.ptype == PassengerType.PA1:
        return compute_t_SA3_basic_PA1(K_SA3, params)
    else:
        return compute_t_SA3_basic_PA2(K_SA3, params)
