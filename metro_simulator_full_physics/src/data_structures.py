"""
数据结构模块：乘客和系统状态
对应论文 Table 1 变量定义
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from src.config import PassengerType, Position, SystemParameters


@dataclass
class Passenger:
    """乘客数据结构
    
    记录乘客在系统中的完整状态和时间信息
    """
    # 基本属性
    index: int                      # 乘客编号（全局唯一，按Strategy1交替编号）
    ptype: PassengerType            # 乘客类型（PA1或PA2）
    position: Position              # 当前位置
    
    # 时间戳（进入各区域的时刻）
    t_enter_SA1: float = 0.0        # 进入SA1的时刻（到达时刻）
    t_enter_PW: float = 0.0         # 进入PW1/PW2的时刻
    t_enter_SA3: float = 0.0        # 进入SA3的时刻
    t_enter_gate: float = 0.0       # 进入闸机的时刻
    t_exit_system: float = 0.0      # 离开系统的时刻
    
    # 基本通过时间（进入时一次性确定，不再改变）
    t_SA1_basic: float = 0.0        # SA1基本时间 - 公式(1)(2)
    t_PW_basic: float = 0.0         # PW基本时间 - 公式(3)(4)
    t_SA3_basic: float = 0.0        # SA3基本时间 - 公式(6)(7)，含t_s
    
    # 附加等待时间（动态累加）
    t_SA1_add: float = 0.0          # SA1附加时间（等待进入PW）
    t_SA2_add: float = 0.0          # PW附加时间（等待进入SA3）
    t_SA3_add: float = 0.0          # SA3附加时间（等待进入闸机）
    
    # 预计离开当前区域的时刻（随附加时间动态更新）
    t_leave_current: float = 0.0    # 预计离开当前区域的时刻
    
    def total_time(self) -> float:
        """计算总通行时间"""
        return (self.t_SA1_basic + self.t_PW_basic + self.t_SA3_basic +
                self.t_SA1_add + self.t_SA2_add + self.t_SA3_add)
    
    def update_leave_time(self):
        """更新预计离开时刻
        
        离开时刻 = 进入时刻 + 基本时间 + 附加时间
        """
        if self.position == Position.SA1:
            self.t_leave_current = self.t_enter_SA1 + self.t_SA1_basic + self.t_SA1_add
        elif self.position in (Position.PW1, Position.PW2):
            self.t_leave_current = self.t_enter_PW + self.t_PW_basic + self.t_SA2_add
        elif self.position == Position.SA3:
            self.t_leave_current = self.t_enter_SA3 + self.t_SA3_basic + self.t_SA3_add
        elif self.position == Position.GATE:
            self.t_leave_current = self.t_enter_gate + 0  # 闸机服务由系统管理


@dataclass 
class GateServer:
    """闸机服务器状态"""
    busy_until: float = 0.0  # 忙碌到何时（0表示空闲）


@dataclass
class SystemState:
    """系统状态
    
    维护所有区域的乘客和统计信息
    """
    params: SystemParameters
    T: float = 0.0                  # 当前仿真时间
    
    # 乘客列表
    passengers: List[Passenger] = field(default_factory=list)
    next_passenger_id: int = 0      # 下一个乘客编号
    
    # 到达累积器（处理浮点到达率）
    arrival_acc_PA1: float = 0.0
    arrival_acc_PA2: float = 0.0
    
    # 闸机状态（5台并行服务器）
    gates: List[GateServer] = field(default_factory=list)
    
    # 历史记录
    history: Dict[str, List] = field(default_factory=lambda: {
        'T': [],
        'D_SA1': [],
        'D_PW1': [],
        'D_PW2': [],
        'D_SA3': [],
        'D_pass': [],
        'K_PW2': [],
        'K_SA3': [],
        'queue_PW1': [],  # PW1前排队人数（SA1中等待进入PW1的PA1）
    })
    
    def __post_init__(self):
        """初始化闸机"""
        if not self.gates:
            self.gates = [GateServer() for _ in range(self.params.N_G)]
    
    # ==================== 区域人数统计 ====================
    
    def get_D_SA1(self) -> int:
        """SA1区域人数"""
        return sum(1 for p in self.passengers if p.position == Position.SA1)
    
    def get_D_PW1(self) -> int:
        """PW1区域人数"""
        return sum(1 for p in self.passengers if p.position == Position.PW1)
    
    def get_D_PW2(self) -> int:
        """PW2区域人数"""
        return sum(1 for p in self.passengers if p.position == Position.PW2)
    
    def get_D_SA3(self) -> int:
        """SA3区域人数"""
        return sum(1 for p in self.passengers if p.position == Position.SA3)
    
    def get_D_gate(self) -> int:
        """闸机服务中人数"""
        return sum(1 for p in self.passengers if p.position == Position.GATE)
    
    def get_D_pass(self) -> int:
        """已通过系统人数"""
        return sum(1 for p in self.passengers if p.position == Position.PASSED)
    
    def get_D_all(self) -> int:
        """总到达人数"""
        return len(self.passengers)
    
    # ==================== 密度计算 ====================
    
    def get_K_PW2(self) -> float:
        """PW2密度 (ped/m²)"""
        D = self.get_D_PW2()
        if self.params.A_PW2 > 0:
            return D / self.params.A_PW2
        return 0.0
    
    def get_K_SA3(self) -> float:
        """SA3密度 (ped/m²)"""
        D = self.get_D_SA3()
        if self.params.A_SA3 > 0:
            return D / self.params.A_SA3
        return 0.0
    
    # ==================== 排队人数统计 ====================
    
    def get_queue_before_PW1(self) -> int:
        """PW1前排队人数
        
        统计SA1中预计离开时刻<=T但还未能进入PW1的PA1
        """
        count = 0
        for p in self.passengers:
            if (p.position == Position.SA1 and 
                p.ptype == PassengerType.PA1 and
                p.t_SA1_add > 0):  # 有附加等待时间说明在排队
                count += 1
        return count
    
    # ==================== 闸机管理 ====================
    
    def get_free_gates(self) -> int:
        """获取空闲闸机数量"""
        return sum(1 for g in self.gates if g.busy_until <= self.T)
    
    def occupy_gate(self) -> bool:
        """占用一个闸机
        
        Returns:
            是否成功占用
        """
        for g in self.gates:
            if g.busy_until <= self.T:
                g.busy_until = self.T + self.params.t_s
                return True
        return False
    
    # ==================== 历史记录 ====================
    
    def record_history(self):
        """记录当前时刻的状态"""
        self.history['T'].append(self.T)
        self.history['D_SA1'].append(self.get_D_SA1())
        self.history['D_PW1'].append(self.get_D_PW1())
        self.history['D_PW2'].append(self.get_D_PW2())
        self.history['D_SA3'].append(self.get_D_SA3())
        self.history['D_pass'].append(self.get_D_pass())
        self.history['K_PW2'].append(self.get_K_PW2())
        self.history['K_SA3'].append(self.get_K_SA3())
        self.history['queue_PW1'].append(self.get_queue_before_PW1())
