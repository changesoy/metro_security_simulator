"""
配置模块：系统参数、枚举类型定义
对应设计书：第9节参数管理策略 + Table 2
"""

from dataclasses import dataclass
from enum import Enum


class PassengerType(Enum):
    """乘客类型枚举"""
    PA1 = "PA1"  # 带包乘客（需安检）
    PA2 = "PA2"  # 无包乘客（快速通道）


class Position(Enum):
    """乘客位置状态枚举"""
    SA1 = "SA1"  # 子区域1
    PW1 = "PW1"  # 通道1（安检通道）
    PW2 = "PW2"  # 通道2（快速通道）
    SA3 = "SA3"  # 子区域3（检票前等候区）
    PASSED = "PASSED"  # 已通过系统


@dataclass
class SystemParameters:
    """系统参数封装（Table 2）

    包含：
    - 几何参数（长度、面积）
    - 速度参数（自由流速度、传送带速度）
    - 密度参数（阈值密度、最大密度）
    - 服务参数（放物/取物/刷卡时间、闸机数量）
    - 仿真参数（时间步长）
    - 派生属性（PW2宽度）
    - 速度-密度函数（Eq.5, Eq.8）
    """

    # ==================== 几何参数 ====================
    L_EN_PW1: float = 5.36  # 入口到PW1距离 (m)
    L_EN_PW2: float = 4.69  # 入口到PW2距离 (m)
    L_PW2: float = 4.55  # PW2通道长度 (m)
    L_SE: float = 2.3  # X光机传送带长度 (m)
    L_PW1_GA: float = 3.65  # PW1到闸机距离 (m)
    L_PW2_GA: float = 4.07  # PW2到闸机距离 (m)
    A_PW2: float = 10.2  # PW2面积 (m²)
    A_SA3: float = 29.7  # SA3面积 (m²)
    W_B: float = 0.45  # 乘客体宽 (m)

    # ==================== 速度参数 ====================
    v0: float = 1.61  # 自由流速度 (m/s)
    v_SE: float = 0.2  # 传送带速度 (m/s)
    v_PW2_init: float = 1.61  # PW2自由流速度 (m/s)
    v_SA3_init: float = 1.61  # SA3自由流速度 (m/s)

    # ==================== 密度参数 ====================
    K_PW2_init: float = 0.31  # PW2密度阈值 (ped/m²)
    K_SA3_init: float = 0.31  # SA3密度阈值 (ped/m²)
    K_PW2_max: float = 3.5  # PW2最大密度 (ped/m²)
    K_SA3_max: float = 3.5  # SA3最大密度 (ped/m²)

    # ==================== 服务参数 ====================
    t_pi: float = 2.0  # 放物时间 (s)
    t_ti: float = 2.0  # 取物时间 (s)
    t_s: float = 3.5  # 刷卡/扫码时间 (s)
    N_G: int = 5  # 闸机数量

    # ==================== 仿真参数 ====================
    dt: float = 0.1  # 时间步长 (s)

    # ==================== 派生属性 ====================

    @property
    def W_PW2(self) -> float:
        """PW2宽度（假设矩形通道）

        Returns:
            float: PW2宽度 (m)

        Note:
            基于"PW2为矩形通道"的工程近似
            W_PW2 = A_PW2 / L_PW2
        """
        return self.A_PW2 / self.L_PW2

    # ==================== 速度-密度函数 ====================

    def v_PW2(self, K: float) -> float:
        """PW2速度-密度关系（Eq.5）

        Args:
            K: 当前密度 (ped/m²)

        Returns:
            float: 对应速度 (m/s)

        Note:
            - K <= K_PW2_init: 自由流速度
            - K > K_PW2_init: 分段三次多项式
            - 包含数值保护: v >= 0.01 m/s
        """
        if K <= self.K_PW2_init:
            return self.v_PW2_init
        else:
            x = K - self.K_PW2_init
            v = 0.11 * x ** 3 - 0.53 * x ** 2 + 0.15 * x + 1.61
            return max(v, 0.01)  # 数值保护：避免负速度或除零

    def v_SA3(self, K: float) -> float:
        """SA3速度-密度关系（Eq.8）

        Args:
            K: 当前密度 (ped/m²)

        Returns:
            float: 对应速度 (m/s)

        Note:
            - K <= K_SA3_init: 自由流速度
            - K > K_SA3_init: 分段三次多项式（与PW2相同形式）
            - 包含数值保护: v >= 0.01 m/s
        """
        if K <= self.K_SA3_init:
            return self.v_SA3_init
        else:
            y = K - self.K_SA3_init
            v = 0.11 * y ** 3 - 0.53 * y ** 2 + 0.15 * y + 1.61
            return max(v, 0.01)  # 数值保护：避免负速度或除零


# ==================== 默认参数实例 ====================

DEFAULT_PARAMS = SystemParameters()

# ==================== 模块测试函数 ====================

if __name__ == "__main__":
    """模块自测：验证参数配置正确性"""

    print("=" * 60)
    print("系统参数配置自测")
    print("=" * 60)

    params = SystemParameters()

    # 测试1：派生属性
    print(f"\n[测试1] 派生属性计算")
    print(f"  A_PW2 = {params.A_PW2} m²")
    print(f"  L_PW2 = {params.L_PW2} m")
    print(f"  W_PW2 = {params.W_PW2:.3f} m")
    print(f"  验证: W_PW2 = A_PW2 / L_PW2 = {params.A_PW2 / params.L_PW2:.3f} m")
    assert abs(params.W_PW2 - params.A_PW2 / params.L_PW2) < 1e-6, "派生属性计算错误"
    print("  ✓ 通过")

    # 测试2：速度-密度函数（PW2）
    print(f"\n[测试2] PW2速度-密度函数")
    test_densities = [0.0, 0.31, 1.0, 2.0, 3.5, 10.0]
    print(f"  {'密度 K (ped/m²)':<20} {'速度 v (m/s)':<15} {'说明'}")
    print(f"  {'-' * 20} {'-' * 15} {'-' * 30}")
    for K in test_densities:
        v = params.v_PW2(K)
        status = "自由流" if K <= params.K_PW2_init else "拥堵" if v > 0.01 else "数值保护"
        print(f"  {K:<20.2f} {v:<15.4f} {status}")
        assert v >= 0.01, f"数值保护失败: v_PW2({K}) = {v} < 0.01"
    print("  ✓ 通过（所有速度 >= 0.01 m/s）")

    # 测试3：速度-密度函数（SA3）
    print(f"\n[测试3] SA3速度-密度函数")
    print(f"  {'密度 K (ped/m²)':<20} {'速度 v (m/s)':<15} {'说明'}")
    print(f"  {'-' * 20} {'-' * 15} {'-' * 30}")
    for K in test_densities:
        v = params.v_SA3(K)
        status = "自由流" if K <= params.K_SA3_init else "拥堵" if v > 0.01 else "数值保护"
        print(f"  {K:<20.2f} {v:<15.4f} {status}")
        assert v >= 0.01, f"数值保护失败: v_SA3({K}) = {v} < 0.01"
    print("  ✓ 通过（所有速度 >= 0.01 m/s）")

    # 测试4：速度单调性（密度增加，速度降低）
    print(f"\n[测试4] 速度单调性检查")
    K_low = 0.5
    K_high = 2.0
    v_pw2_low = params.v_PW2(K_low)
    v_pw2_high = params.v_PW2(K_high)
    v_sa3_low = params.v_SA3(K_low)
    v_sa3_high = params.v_SA3(K_high)

    print(f"  PW2: v({K_low}) = {v_pw2_low:.4f} > v({K_high}) = {v_pw2_high:.4f}")
    print(f"  SA3: v({K_low}) = {v_sa3_low:.4f} > v({K_high}) = {v_sa3_high:.4f}")
    assert v_pw2_low > v_pw2_high, "PW2速度单调性错误"
    assert v_sa3_low > v_sa3_high, "SA3速度单调性错误"
    print("  ✓ 通过（密度越高，速度越低）")

    # 测试5：枚举类型
    print(f"\n[测试5] 枚举类型定义")
    print(f"  乘客类型: {[pt.value for pt in PassengerType]}")
    print(f"  位置状态: {[pos.value for pos in Position]}")
    assert len(PassengerType) == 2, "乘客类型数量错误"
    assert len(Position) == 5, "位置状态数量错误"
    print("  ✓ 通过")

    print("\n" + "=" * 60)
    print("所有测试通过！参数配置正确。")
    print("=" * 60)
