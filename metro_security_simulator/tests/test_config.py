"""
单元测试：config.py
测试系统参数、枚举类型、速度-密度函数
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import SystemParameters, PassengerType, Position


def test_parameter_derivation():
    """测试派生属性计算"""
    print("\n[测试] 派生属性计算")
    params = SystemParameters()

    # 测试 W_PW2 计算
    expected_W = params.A_PW2 / params.L_PW2
    actual_W = params.W_PW2

    print(f"  A_PW2 = {params.A_PW2} m²")
    print(f"  L_PW2 = {params.L_PW2} m")
    print(f"  W_PW2 = {actual_W:.4f} m")
    print(f"  期望值 = {expected_W:.4f} m")

    assert abs(actual_W - expected_W) < 1e-6, "W_PW2 计算错误"
    print("  ✓ 通过")


def test_velocity_density_functions():
    """测试速度-密度函数"""
    print("\n[测试] 速度-密度函数")
    params = SystemParameters()

    test_cases = [
        (0.0, "极低密度（自由流）"),
        (0.31, "阈值密度（临界点）"),
        (1.0, "中等密度"),
        (2.0, "高密度"),
        (3.5, "最大密度"),
        (10.0, "极端密度（触发保护）")
    ]

    print("\n  PW2速度-密度函数:")
    print(f"  {'密度 K':<15} {'速度 v':<15} {'说明'}")
    print(f"  {'-' * 15} {'-' * 15} {'-' * 30}")

    for K, desc in test_cases:
        v = params.v_PW2(K)
        print(f"  {K:<15.2f} {v:<15.4f} {desc}")

        # 验证数值保护
        assert v >= 0.01, f"数值保护失败: v_PW2({K}) = {v} < 0.01"

        # 验证自由流区域
        if K <= params.K_PW2_init:
            assert v == params.v_PW2_init, f"自由流区域错误: K={K}, v={v}"

    print("\n  SA3速度-密度函数:")
    print(f"  {'密度 K':<15} {'速度 v':<15} {'说明'}")
    print(f"  {'-' * 15} {'-' * 15} {'-' * 30}")

    for K, desc in test_cases:
        v = params.v_SA3(K)
        print(f"  {K:<15.2f} {v:<15.4f} {desc}")

        assert v >= 0.01, f"数值保护失败: v_SA3({K}) = {v} < 0.01"

        if K <= params.K_SA3_init:
            assert v == params.v_SA3_init, f"自由流区域错误: K={K}, v={v}"

    print("  ✓ 通过")


def test_velocity_monotonicity():
    """测试速度单调性（密度越高，速度越低）"""
    print("\n[测试] 速度单调性")
    params = SystemParameters()

    densities = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    print("\n  PW2单调性检查:")
    v_prev = params.v_PW2(densities[0])
    for K in densities[1:]:
        v_curr = params.v_PW2(K)
        print(f"  v({K - 0.5:.1f}) = {v_prev:.4f} > v({K:.1f}) = {v_curr:.4f}")
        assert v_prev >= v_curr, f"单调性违反: v({K - 0.5}) < v({K})"
        v_prev = v_curr

    print("\n  SA3单调性检查:")
    v_prev = params.v_SA3(densities[0])
    for K in densities[1:]:
        v_curr = params.v_SA3(K)
        print(f"  v({K - 0.5:.1f}) = {v_prev:.4f} > v({K:.1f}) = {v_curr:.4f}")
        assert v_prev >= v_curr, f"单调性违反: v({K - 0.5}) < v({K})"
        v_prev = v_curr

    print("  ✓ 通过")


def test_numerical_protection():
    """测试数值保护机制"""
    print("\n[测试] 数值保护机制")
    params = SystemParameters()

    # 极端密度（应该触发保护）
    extreme_densities = [5.0, 10.0, 50.0, 100.0]

    print(f"  {'密度 K':<15} {'v_PW2':<15} {'v_SA3':<15}")
    print(f"  {'-' * 15} {'-' * 15} {'-' * 15}")

    for K in extreme_densities:
        v_pw2 = params.v_PW2(K)
        v_sa3 = params.v_SA3(K)
        print(f"  {K:<15.2f} {v_pw2:<15.4f} {v_sa3:<15.4f}")

        # 验证最小值保护
        assert v_pw2 >= 0.01, f"PW2数值保护失败: K={K}, v={v_pw2}"
        assert v_sa3 >= 0.01, f"SA3数值保护失败: K={K}, v={v_sa3}"

    print("  ✓ 通过（所有速度 >= 0.01 m/s）")


def test_enum_types():
    """测试枚举类型定义"""
    print("\n[测试] 枚举类型定义")

    # 测试 PassengerType
    print(f"  乘客类型: {[pt.value for pt in PassengerType]}")
    assert len(PassengerType) == 2, "乘客类型数量错误"
    assert PassengerType.PA1.value == "PA1"
    assert PassengerType.PA2.value == "PA2"

    # 测试 Position
    print(f"  位置状态: {[pos.value for pos in Position]}")
    assert len(Position) == 5, "位置状态数量错误"
    assert Position.SA1.value == "SA1"
    assert Position.PW1.value == "PW1"
    assert Position.PW2.value == "PW2"
    assert Position.SA3.value == "SA3"
    assert Position.PASSED.value == "PASSED"

    print("  ✓ 通过")


def test_default_params():
    """测试默认参数实例"""
    print("\n[测试] 默认参数实例")
    from src.config import DEFAULT_PARAMS

    assert DEFAULT_PARAMS.dt == 0.1, "默认时间步长错误"
    assert DEFAULT_PARAMS.N_G == 5, "默认闸机数量错误"
    assert DEFAULT_PARAMS.t_s == 3.5, "默认刷卡时间错误"

    print(f"  dt = {DEFAULT_PARAMS.dt} s")
    print(f"  N_G = {DEFAULT_PARAMS.N_G}")
    print(f"  t_s = {DEFAULT_PARAMS.t_s} s")
    print("  ✓ 通过")


if __name__ == "__main__":
    print("=" * 60)
    print("config.py 单元测试")
    print("=" * 60)

    test_parameter_derivation()
    test_velocity_density_functions()
    test_velocity_monotonicity()
    test_numerical_protection()
    test_enum_types()
    test_default_params()

    print("\n" + "=" * 60)
    print("所有测试通过！✓")
    print("=" * 60)
