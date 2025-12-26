"""
基本时间计算模块：实现 Eq.(1)-(8) 的计算函数
对应设计书：第4.1节基本通过时间

核心设计原则（微调A）：
- 所有速度-密度函数调用 params.v_PW2() 和 params.v_SA3()
- 不重复多项式计算，保持代码一致性
"""

# 条件导入：支持两种运行方式
try:
    from src.data_structures import Passenger, SystemParameters
    from src.config import PassengerType
except ModuleNotFoundError:
    from data_structures import Passenger, SystemParameters
    from config import PassengerType


def compute_t_SA1_basic(passenger: Passenger, params: SystemParameters) -> float:
    """计算SA1基本通过时间（Eq.1 & Eq.2）

    物理过程：从入口自由流行走到PW1/PW2入口

    Args:
        passenger: 乘客对象
        params: 系统参数

    Returns:
        float: SA1基本通过时间（秒）

    Note:
        - PA1: t = L_EN_PW1 / v0
        - PA2: t = L_EN_PW2 / v0
        - 自由流速度 v0 = 1.61 m/s（不受密度影响）
    """
    if passenger.ptype == PassengerType.PA1:
        # Eq.(1): 带包乘客走较长路径
        return params.L_EN_PW1 / params.v0
    else:
        # Eq.(2): 无包乘客走较短路径
        return params.L_EN_PW2 / params.v0


def compute_t_PW1_basic(params: SystemParameters) -> float:
    """计算PW1基本通过时间（Eq.3）

    物理过程：安检设备检查（三阶段刚性流程）

    Args:
        params: 系统参数

    Returns:
        float: PW1基本通过时间（秒）

    Note:
        - t = t_pi + L_SE/v_SE + t_ti
        - 常数时间，不受密度影响
        - t_pi: 取物放物时间
        - L_SE/v_SE: 设备检查时间
        - t_ti: 检票时间
    """
    # Eq.(3): 三阶段刚性流程
    return params.t_pi + params.L_SE / params.v_SE + params.t_ti


def compute_t_PW2_basic(K_PW2: float, params: SystemParameters) -> float:
    """计算PW2基本通过时间（Eq.4 & Eq.5）

    物理过程：快速通道行走（受密度影响）

    Args:
        K_PW2: PW2当前密度（ped/m²）
        params: 系统参数

    Returns:
        float: PW2基本通过时间（秒）

    Note:
        - t = L_PW2 / v_PW2(K)
        - 速度v由Eq.(5)计算，随密度变化
        - 离散同步更新：使用"转移发生前"的密度
    """
    # Eq.(4): 时间 = 距离 / 速度
    # Eq.(5): 速度-密度关系（调用params方法，避免重复）
    v = params.v_PW2(K_PW2)
    return params.L_PW2 / v


def compute_t_SA3_basic(passenger: Passenger, K_SA3: float, params: SystemParameters) -> float:
    """计算SA3基本通过时间（Eq.6 & Eq.7 & Eq.8）

    物理过程：从PW出口行走到闸机 + 刷卡

    Args:
        passenger: 乘客对象
        K_SA3: SA3当前密度（ped/m²）
        params: 系统参数

    Returns:
        float: SA3基本通过时间（秒）

    Note:
        - PA1: t = L_PW1_GA / v_SA3(K) + t_s
        - PA2: t = L_PW2_GA / v_SA3(K) + t_s
        - 速度v由Eq.(8)计算，随密度变化
        - ⚠️ t_s（刷卡时间）完全包含在此，Gate不重复计时
        - 离散同步更新：使用"转移发生前"的密度
    """
    # Eq.(8): 速度-密度关系（调用params方法）
    v = params.v_SA3(K_SA3)

    if passenger.ptype == PassengerType.PA1:
        # Eq.(6): PA1从PW1出口到闸机
        return params.L_PW1_GA / v + params.t_s
    else:
        # Eq.(7): PA2从PW2出口到闸机
        return params.L_PW2_GA / v + params.t_s


def compute_all_basic_times(passenger: Passenger, K_PW2: float, K_SA3: float,
                           params: SystemParameters) -> dict:
    """批量计算所有基本时间（便捷函数）

    Args:
        passenger: 乘客对象
        K_PW2: PW2当前密度
        K_SA3: SA3当前密度
        params: 系统参数

    Returns:
        dict: 包含所有基本时间的字典

    Note:
        返回值包含：
        - 't_SA1_basic': SA1基本时间
        - 't_PW_basic': PW基本时间（PW1或PW2）
        - 't_SA3_basic': SA3基本时间
    """
    result = {}

    # SA1基本时间
    result['t_SA1_basic'] = compute_t_SA1_basic(passenger, params)

    # PW基本时间（根据类型选择）
    if passenger.ptype == PassengerType.PA1:
        result['t_PW_basic'] = compute_t_PW1_basic(params)
    else:
        result['t_PW_basic'] = compute_t_PW2_basic(K_PW2, params)

    # SA3基本时间
    result['t_SA3_basic'] = compute_t_SA3_basic(passenger, K_SA3, params)

    return result


# ==================== 模块测试函数 ====================

if __name__ == "__main__":
    """模块自测：验证基本时间计算正确性"""

    # 自测时的导入
    import sys
    import os
    if 'src' not in sys.path[0]:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import Position, PassengerType, SystemParameters
    from data_structures import Passenger

    print("=" * 70)
    print("基本时间计算模块自测")
    print("=" * 70)

    params = SystemParameters()

    # 测试1：SA1基本时间
    print("\n[测试1] SA1基本时间计算（Eq.1 & Eq.2）")
    p_PA1 = Passenger(1, PassengerType.PA1, Position.SA1)
    p_PA2 = Passenger(2, PassengerType.PA2, Position.SA1)

    t_PA1_SA1 = compute_t_SA1_basic(p_PA1, params)
    t_PA2_SA1 = compute_t_SA1_basic(p_PA2, params)

    print(f"  PA1: L={params.L_EN_PW1}m, v={params.v0}m/s → t={t_PA1_SA1:.3f}s")
    print(f"  PA2: L={params.L_EN_PW2}m, v={params.v0}m/s → t={t_PA2_SA1:.3f}s")

    expected_PA1 = params.L_EN_PW1 / params.v0
    expected_PA2 = params.L_EN_PW2 / params.v0

    assert abs(t_PA1_SA1 - expected_PA1) < 1e-6
    assert abs(t_PA2_SA1 - expected_PA2) < 1e-6
    assert t_PA1_SA1 > t_PA2_SA1  # PA1路径更长
    print("  ✓ 通过（PA1>PA2，符合预期）")

    # 测试2：PW1基本时间（常数）
    print("\n[测试2] PW1基本时间计算（Eq.3）")
    t_PW1 = compute_t_PW1_basic(params)
    print(f"  t_PW1 = t_pi + L_SE/v_SE + t_ti")
    print(f"        = {params.t_pi} + {params.L_SE}/{params.v_SE} + {params.t_ti}")
    print(f"        = {t_PW1:.3f}s")

    expected = params.t_pi + params.L_SE / params.v_SE + params.t_ti
    assert abs(t_PW1 - expected) < 1e-6
    assert t_PW1 == expected
    print("  ✓ 通过（常数时间，不受密度影响）")

    # 测试3：PW2基本时间（密度相关）
    print("\n[测试3] PW2基本时间计算（Eq.4 & Eq.5）")
    densities = [0.0, 0.31, 1.0, 2.0, 3.5]

    print(f"  {'密度 K':<15} {'速度 v':<15} {'时间 t':<15} {'说明'}")
    print(f"  {'-'*15} {'-'*15} {'-'*15} {'-'*30}")

    t_prev = 0.0
    for K in densities:
        t = compute_t_PW2_basic(K, params)
        v = params.v_PW2(K)

        desc = ""
        if K == 0.0:
            desc = "零密度（最快）"
        elif K == params.K_PW2_init:
            desc = "阈值密度"
        elif K == params.K_PW2_max:
            desc = "最大密度（最慢）"

        print(f"  {K:<15.2f} {v:<15.3f} {t:<15.3f} {desc}")

        # 验证：密度越大，时间越长
        if K > 0:
            assert t >= t_prev, "密度增加时时间应增加"
        t_prev = t

    print("  ✓ 通过（时间随密度单调递增）")

    # 测试4：SA3基本时间（含t_s）
    print("\n[测试4] SA3基本时间计算（Eq.6 & Eq.7 & Eq.8，含刷卡时间）")
    K_SA3 = 1.0

    t_PA1_SA3 = compute_t_SA3_basic(p_PA1, K_SA3, params)
    t_PA2_SA3 = compute_t_SA3_basic(p_PA2, K_SA3, params)

    v_SA3 = params.v_SA3(K_SA3)
    print(f"  密度: K_SA3={K_SA3}ped/m², 速度: v={v_SA3:.3f}m/s")
    print(f"  PA1: ({params.L_PW1_GA}m / {v_SA3:.3f}m/s) + {params.t_s}s = {t_PA1_SA3:.3f}s")
    print(f"  PA2: ({params.L_PW2_GA}m / {v_SA3:.3f}m/s) + {params.t_s}s = {t_PA2_SA3:.3f}s")

    # 验证包含t_s
    assert t_PA1_SA3 > params.t_s, "SA3时间应大于刷卡时间"
    assert t_PA2_SA3 > params.t_s, "SA3时间应大于刷卡时间"
    print("  ✓ 通过（已包含刷卡时间t_s）")

    # 测试5：SA3时间随密度变化
    print("\n[测试5] SA3时间随密度变化（Eq.8）")
    densities_SA3 = [0.0, 1.0, 2.0, 3.5]

    print(f"  {'密度 K':<15} {'速度 v':<15} {'时间 t':<15}")
    print(f"  {'-'*15} {'-'*15} {'-'*15}")

    t_prev = 0.0
    for K in densities_SA3:
        t = compute_t_SA3_basic(p_PA1, K, params)
        v = params.v_SA3(K)
        print(f"  {K:<15.2f} {v:<15.3f} {t:<15.3f}")

        if K > 0:
            assert t >= t_prev, "密度增加时时间应增加"
        t_prev = t

    print("  ✓ 通过（时间随密度单调递增）")

    # 测试6：批量计算
    print("\n[测试6] 批量计算所有基本时间")
    K_PW2 = 1.0
    K_SA3 = 1.5

    times = compute_all_basic_times(p_PA1, K_PW2, K_SA3, params)

    print(f"  PA1在(K_PW2={K_PW2}, K_SA3={K_SA3})下的基本时间:")
    print(f"    SA1: {times['t_SA1_basic']:.3f}s")
    print(f"    PW1: {times['t_PW_basic']:.3f}s")
    print(f"    SA3: {times['t_SA3_basic']:.3f}s")
    print(f"    总计: {sum(times.values()):.3f}s")

    assert 't_SA1_basic' in times
    assert 't_PW_basic' in times
    assert 't_SA3_basic' in times
    print("  ✓ 通过（批量计算正确）")

    # 测试7：数值保护（极端密度）
    print("\n[测试7] 数值保护（极端密度）")
    K_extreme = 10.0  # 远超K_max

    t_extreme = compute_t_PW2_basic(K_extreme, params)
    print(f"  极端密度K={K_extreme}时，t_PW2={t_extreme:.3f}s")

    assert t_extreme > 0, "时间应>0"
    assert t_extreme < 1000, "时间应有界（<1000s）"
    print("  ✓ 通过（数值保护有效，时间有界）")

    print("\n" + "=" * 70)
    print("所有测试通过！基本时间计算正确。")
    print("=" * 70)
