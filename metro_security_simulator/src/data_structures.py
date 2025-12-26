"""
数据结构模块：Passenger 和 System 类定义
对应设计书：第8.2节数据结构设计
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

# 条件导入：支持两种运行方式
try:
    from src.config import PassengerType, Position, SystemParameters
except ModuleNotFoundError:
    from config import PassengerType, Position, SystemParameters


@dataclass
class Passenger:
    """乘客数据结构

    包含乘客在系统中的完整状态信息，支持递推计算。

    Attributes:
        index: 乘客编号（全局唯一）
        ptype: 乘客类型（PA1或PA2）
        position: 当前位置（SA1/PW1/PW2/SA3/PASSED）

        t_enter_SA1: 进入SA1的时刻
        t_enter_SA2: 进入PW（PW1或PW2）的时刻
        t_enter_SA3: 进入SA3的时刻
        t_exit_system: 离开系统的时刻

        t_SA1_basic: SA1基本通过时间
        t_PW_basic: PW基本通过时间（PW1或PW2）
        t_SA3_basic: SA3基本通过时间（含t_s）

        t_SA1_add: SA1附加等待时间
        t_SA2_add: PW附加等待时间
        t_SA3_add: SA3附加等待时间
    """
    # 基本属性
    index: int
    ptype: PassengerType
    position: Position

    # 时间戳
    t_enter_SA1: float = 0.0
    t_enter_SA2: float = 0.0
    t_enter_SA3: float = 0.0
    t_exit_system: float = 0.0

    # 基本时间
    t_SA1_basic: float = 0.0
    t_PW_basic: float = 0.0
    t_SA3_basic: float = 0.0

    # 附加时间
    t_SA1_add: float = 0.0
    t_SA2_add: float = 0.0
    t_SA3_add: float = 0.0

    def total_time(self) -> float:
        """计算总通行时间

        Returns:
            float: 总时间 = 所有basic时间 + 所有add时间
        """
        return (self.t_SA1_basic + self.t_PW_basic + self.t_SA3_basic +
                self.t_SA1_add + self.t_SA2_add + self.t_SA3_add)

    def __repr__(self) -> str:
        """自定义字符串表示（便于调试）"""
        return (f"Passenger(index={self.index}, type={self.ptype.value}, "
                f"pos={self.position.value}, total_time={self.total_time():.2f}s)")


@dataclass
class System:
    """系统状态数据结构

    维护系统的全局状态，包括所有乘客和区域人数。

    Attributes:
        params: 系统参数
        T: 当前仿真时间
        passengers: 所有乘客列表
        next_passenger_id: 下一个乘客的编号

        arrival_acc_PA1: PA1到达累积器（浮点数）
        arrival_acc_PA2: PA2到达累积器（浮点数）

        D_SA1: SA1区域人数
        D_PW1: PW1区域人数
        D_PW2: PW2区域人数
        D_SA3: SA3区域人数
        D_pass: 已通过闸机人数
        D_All: 总到达人数

        history: 历史记录（时间序列数据）
    """
    params: SystemParameters
    T: float = 0.0
    passengers: List[Passenger] = field(default_factory=list)
    next_passenger_id: int = 0

    # 到达累积器
    arrival_acc_PA1: float = 0.0
    arrival_acc_PA2: float = 0.0

    # 区域人数
    D_SA1: int = 0
    D_PW1: int = 0
    D_PW2: int = 0
    D_SA3: int = 0
    D_pass: int = 0
    D_All: int = 0

    # 历史记录
    history: Dict[str, List] = field(default_factory=lambda: {
        'T': [],
        'D_SA1': [],
        'D_PW1': [],
        'D_PW2': [],
        'D_SA3': [],
        'D_pass': [],
        'K_PW2': [],
        'K_SA3': []
    })

    def get_passenger_by_index(self, index: int) -> Optional[Passenger]:
        """根据编号获取乘客对象"""
        for p in self.passengers:
            if p.index == index:
                return p
        return None

    def get_passengers_by_position(self, position: Position) -> List[Passenger]:
        """根据位置获取乘客列表"""
        return [p for p in self.passengers if p.position == position]

    def get_passengers_by_type(self, ptype: PassengerType) -> List[Passenger]:
        """根据类型获取乘客列表"""
        return [p for p in self.passengers if p.ptype == ptype]

    def current_density_PW2(self) -> float:
        """计算PW2当前密度"""
        return self.D_PW2 / self.params.A_PW2

    def current_density_SA3(self) -> float:
        """计算SA3当前密度"""
        return self.D_SA3 / self.params.A_SA3

    def is_finished(self):
        """检查仿真是否完成

        Returns:
            bool: 所有区域为空且有人通过
        """
        return (self.D_SA1 == 0 and
                self.D_PW1 == 0 and
                self.D_PW2 == 0 and
                self.D_SA3 == 0 and
                self.D_pass > 0)

    def __repr__(self) -> str:
        """自定义字符串表示（便于调试）"""
        return (f"System(T={self.T:.1f}s, passengers={len(self.passengers)}, "
                f"D_pass={self.D_pass}/{self.D_All})")


if __name__ == "__main__":
    """模块自测：验证数据结构正确性"""

    # 自测时的导入（避免循环导入问题）
    import sys
    import os
    if 'src' not in sys.path[0]:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import PassengerType, Position, SystemParameters

    print("=" * 60)
    print("数据结构模块自测")
    print("=" * 60)

    # 测试1：Passenger 创建与方法
    print("\n[测试1] Passenger 对象创建")
    p1 = Passenger(index=1, ptype=PassengerType.PA1, position=Position.SA1)
    print(f"  创建乘客: {p1}")
    assert p1.index == 1
    assert p1.ptype == PassengerType.PA1
    assert p1.position == Position.SA1
    assert p1.total_time() == 0.0
    print("  ✓ 通过")

    # 测试2：total_time() 计算
    print("\n[测试2] Passenger.total_time() 计算")
    p2 = Passenger(index=2, ptype=PassengerType.PA2, position=Position.PW2)
    p2.t_SA1_basic = 3.0
    p2.t_PW_basic = 4.5
    p2.t_SA3_basic = 5.5
    p2.t_SA1_add = 1.0
    p2.t_SA2_add = 2.0
    p2.t_SA3_add = 0.5

    total = p2.total_time()
    expected = 3.0 + 4.5 + 5.5 + 1.0 + 2.0 + 0.5

    print(f"  各时间分量: basic=({p2.t_SA1_basic}, {p2.t_PW_basic}, {p2.t_SA3_basic}), "
          f"add=({p2.t_SA1_add}, {p2.t_SA2_add}, {p2.t_SA3_add})")
    print(f"  总时间: {total:.2f}s (期望: {expected:.2f}s)")

    assert abs(total - expected) < 1e-6
    print("  ✓ 通过")

    # 测试3：System 对象初始化
    print("\n[测试3] System 对象初始化")
    params = SystemParameters()
    sys = System(params=params)

    print(f"  系统状态: {sys}")
    assert sys.T == 0.0
    assert sys.D_pass == 0
    assert len(sys.passengers) == 0
    assert sys.is_finished() == True  # D_All=0, D_pass=0 → 0>=0 → True（空系统是"完成"状态）
    print("  ✓ 通过")

    # 测试4：System 方法
    print("\n[测试4] System 辅助方法")

    # 添加测试乘客
    sys.passengers.append(Passenger(1, PassengerType.PA1, Position.SA1))
    sys.passengers.append(Passenger(2, PassengerType.PA2, Position.SA1))
    sys.passengers.append(Passenger(3, PassengerType.PA1, Position.PW1))
    sys.D_SA1 = 2
    sys.D_PW1 = 1

    # 测试按位置查询
    sa1_passengers = sys.get_passengers_by_position(Position.SA1)
    print(f"  SA1中的乘客数: {len(sa1_passengers)} (期望: 2)")
    assert len(sa1_passengers) == 2

    # 测试按类型查询
    pa1_passengers = sys.get_passengers_by_type(PassengerType.PA1)
    print(f"  PA1类型乘客数: {len(pa1_passengers)} (期望: 2)")
    assert len(pa1_passengers) == 2

    # 测试按编号查询
    p = sys.get_passenger_by_index(2)
    print(f"  编号2的乘客: {p}")
    assert p is not None
    assert p.index == 2

    print("  ✓ 通过")

    # 测试5：密度计算
    print("\n[测试5] 密度计算方法")
    sys.D_PW2 = 10
    sys.D_SA3 = 20

    K_PW2 = sys.current_density_PW2()
    K_SA3 = sys.current_density_SA3()

    expected_K_PW2 = 10 / params.A_PW2
    expected_K_SA3 = 20 / params.A_SA3

    print(f"  PW2密度: {K_PW2:.4f} (期望: {expected_K_PW2:.4f})")
    print(f"  SA3密度: {K_SA3:.4f} (期望: {expected_K_SA3:.4f})")

    assert abs(K_PW2 - expected_K_PW2) < 1e-6
    assert abs(K_SA3 - expected_K_SA3) < 1e-6
    print("  ✓ 通过")

    # 测试6：终止条件
    print("\n[测试6] 终止条件判定")
    sys.D_All = 100
    sys.D_pass = 50
    assert sys.is_finished() == False
    print(f"  D_pass={sys.D_pass}, D_All={sys.D_All} → is_finished()=False")

    sys.D_pass = 100
    assert sys.is_finished() == True
    print(f"  D_pass={sys.D_pass}, D_All={sys.D_All} → is_finished()=True")
    print("  ✓ 通过")

    print("\n" + "=" * 60)
    print("所有测试通过！数据结构定义正确。")
    print("=" * 60)
