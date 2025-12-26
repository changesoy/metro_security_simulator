"""
配置模块：系统参数定义
严格对应论文 Table 2 参数

论文: Passenger Queuing Analysis Method of Security Inspection 
      and Ticket-Checking Area of Metro Stations
"""

from dataclasses import dataclass
from enum import Enum


class PassengerType(Enum):
    """乘客类型"""
    PA1 = "PA1"  # 有包乘客（需安检）
    PA2 = "PA2"  # 无包乘客（快速通道）


class Position(Enum):
    """乘客位置"""
    SA1 = "SA1"          # 子区域1（入口到安检/通道前）
    PW1 = "PW1"          # 通道1（安检通道）
    PW2 = "PW2"          # 通道2（快速通道）
    SA3 = "SA3"          # 子区域3（检票前）
    GATE = "GATE"        # 闸机服务中
    PASSED = "PASSED"    # 已离开系统


@dataclass
class SystemParameters:
    """系统参数（Table 2）
    
    所有参数严格对应论文Table 2
    """
    
    # ==================== 几何参数 ====================
    L_EN_PW1: float = 5.36      # 入口到PW1距离 (m)
    L_EN_PW2: float = 4.69      # 入口到PW2距离 (m)
    L_PW2: float = 4.55         # PW2通道长度 (m)
    L_SE: float = 2.3           # X光机传送带长度 (m)
    L_PW1_GA: float = 3.65      # PW1到闸机距离 (m)
    L_PW2_GA: float = 4.07      # PW2到闸机距离 (m)
    
    A_PW2: float = 10.2         # PW2面积 (m²) - 论文未直接给出，根据L_PW2推算
    A_SA3: float = 21.8         # SA3面积 (m²)
    
    # ==================== 人体参数 ====================
    H: float = 0.5              # 人体厚度 (m) - 用于一般空间计算
    H_bag: float = 0.15         # 包的厚度 (m) - 用于PW1传送带容量计算
    W_B: float = 0.5            # 人体宽度 (m) - 用于PW2宽度约束（与H相同）
    
    # ==================== 速度参数 ====================
    v0: float = 1.61            # 自由流速度 (m/s)
    v_SE: float = 0.2           # 传送带速度 (m/s)
    v_PW2_init: float = 1.61    # PW2自由流速度 (m/s)
    v_SA3_init: float = 1.61    # SA3自由流速度 (m/s)
    
    # ==================== 密度参数 ====================
    K_PW2_init: float = 0.31    # PW2密度阈值 (ped/m²)
    K_SA3_init: float = 0.31    # SA3密度阈值 (ped/m²)
    K_PW2_max: float = 3.5      # PW2最大密度 (ped/m²)
    K_SA3_max: float = 3.5      # SA3最大密度 (ped/m²)
    
    # ==================== 时间参数 ====================
    t_pi: float = 2.0           # 放物时间 (s)
    t_ti: float = 2.0           # 取物时间 (s)
    t_s: float = 3.5            # 刷卡/扫码时间 (s)
    
    # ==================== 设施参数 ====================
    N_G: int = 5                # 闸机数量
    
    # ==================== 仿真参数 ====================
    dt: float = 0.1             # 时间步长 (s)
    
    # ==================== 派生属性 ====================
    
    @property
    def W_PW2(self) -> float:
        """PW2宽度 (m)"""
        return self.A_PW2 / self.L_PW2  # ≈ 2.24m
    
    @property
    def C_PW1(self) -> int:
        """PW1容量（传送带最大人数）- 公式(9)"""
        return int(self.L_SE / self.H)  # 2.3/0.5 = 4人
    
    @property
    def t_PW1_basic(self) -> float:
        """PW1基本通过时间 - 公式(3)
        
        t = t_pi + L_SE/v_SE + t_ti
          = 2.0 + 2.3/0.2 + 2.0
          = 2.0 + 11.5 + 2.0
          = 15.5s
        """
        return self.t_pi + self.L_SE / self.v_SE + self.t_ti
    
    # ==================== 速度-密度函数 ====================
    
    def v_PW2(self, K: float) -> float:
        """PW2速度-密度关系 - 公式(5)
        
        当 K <= K_init: v = v_init
        当 K > K_init:  v = 0.11x³ - 0.53x² + 0.15x + 1.61
        其中 x = K - K_init
        
        Args:
            K: 当前密度 (ped/m²)
            
        Returns:
            速度 (m/s)
        """
        if K <= self.K_PW2_init:
            return self.v_PW2_init
        else:
            x = K - self.K_PW2_init
            v = 0.11 * x**3 - 0.53 * x**2 + 0.15 * x + 1.61
            return max(v, 0.01)  # 数值保护
    
    def v_SA3(self, K: float) -> float:
        """SA3速度-密度关系 - 公式(8)
        
        与PW2使用相同的函数形式
        
        Args:
            K: 当前密度 (ped/m²)
            
        Returns:
            速度 (m/s)
        """
        if K <= self.K_SA3_init:
            return self.v_SA3_init
        else:
            x = K - self.K_SA3_init
            v = 0.11 * x**3 - 0.53 * x**2 + 0.15 * x + 1.61
            return max(v, 0.01)  # 数值保护
