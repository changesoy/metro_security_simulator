"""
单元测试：admission_control.py
测试准入判定函数（Eq.9-12）
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.admission_control import (
    check_PW1_admission,
    check_PW2_admission,
    check_SA3_admission,
    check_gate_admission,
    diagnose_PW1_constraint,
    diagnose_PW2_constraint,
    diagnose_SA3_constraint
)
from src.data_structures import Passenger
from src.config import PassengerType, Position, SystemParameters


def create_test_candidates(n: int, ptype: PassengerType = PassengerType.PA1):
    """创建测试候选乘客列表"""
    return [Passenger(i, ptype, Position.SA1) for i in range(n)]


def test_PW1_hard_switch():
    """测试PW1硬开关逻辑（Eq.9）"""
    print("\n[测试] PW1硬开关逻辑")

    params = SystemParameters()
    capacity_proxy = params.L_SE / params.v_SE

    print(f"  容量指标: {capacity_proxy:.2f}")

    # 场景1：未超载（H <= 0，应允许全部）
    candidates = create_test_candidates(10)
    allowed_1 = check_PW1_admission(candidates, D_PW1=5, params=params)
    H_1 = 5 - capacity_proxy
    print(f"  场景1: D_PW1=5, H={H_1:.2f} → allowed={allowed_1} (期望: 10)")
    assert allowed_1 == 10, "未超载时应允许全部"

    # 场景2：刚好超载（H > 0，应阻塞全部）
    allowed_2 = check_PW1_admission(candidates, D_PW1=12, params=params)
    H_2 = 12 - capacity_proxy
    print(f"  场景2: D_PW1=12, H={H_2:.2f} → allowed={allowed_2} (期望: 0)")
    assert allowed_2 == 0, "超载时应阻塞全部"

    # 场景3：严重超载
    allowed_3 = check_PW1_admission(candidates, D_PW1=20, params=params)
    H_3 = 20 - capacity_proxy
    print(f"  场景3: D_PW1=20, H={H_3:.2f} → allowed={allowed_3} (期望: 0)")
    assert allowed_3 == 0, "严重超载时应阻塞全部"

    # 场景4：临界点（H = 0）
    D_critical = int(capacity_proxy)
    allowed_4 = check_PW1_admission(candidates, D_PW1=D_critical, params=params)
    H_4 = D_critical - capacity_proxy
    print(f"  场景4: D_PW1={D_critical}, H={H_4:.2f} → allowed={allowed_4} (期望: 10)")
    assert allowed_4 == 10, "临界点时应允许"

    print("  ✓ 通过")


def test_PW2_dual_constraint():
    """测试PW2双重约束（Eq.10 & Eq.11）"""
    print("\n[测试] PW2双重约束")

    params = SystemParameters()
    max_parallel = int(params.W_PW2 / params.W_B)

    print(f"  体宽约束: max_parallel={max_parallel}人")
    print(f"  密度约束: A_PW2={params.A_PW2}m², K_max={params.K_PW2_max}ped/m²")

    # 场景1：体宽约束生效
    candidates = create_test_candidates(10, PassengerType.PA2)
    allowed_1 = check_PW2_admission(candidates, D_PW2=0, K_PW2=0.0, params=params)
    print(f"\n  场景1（空闲）: 候选={len(candidates)}, D_PW2=0")
    print(f"    体宽限={max_parallel}, 密度限={(params.K_PW2_max - 0.0) * params.A_PW2:.0f}")
    print(f"    允许={allowed_1} (期望: {max_parallel}，体宽约束生效)")
    assert allowed_1 == max_parallel, "体宽约束应生效"

    # 场景2：密度约束生效
    D_PW2_high = 30  # 高人数
    K_PW2_high = D_PW2_high / params.A_PW2
    remaining = params.A_PW2 * params.K_PW2_max - D_PW2_high
    max_density = int(remaining) if remaining > 0 else 0

    allowed_2 = check_PW2_admission(candidates, D_PW2=D_PW2_high, K_PW2=K_PW2_high, params=params)
    print(f"\n  场景2（高密度）: 候选={len(candidates)}, D_PW2={D_PW2_high}")
    print(f"    体宽限={max_parallel}, 密度限={max_density}")
    print(f"    允许={allowed_2} (期望: {max_density}，密度约束生效)")

    if max_density < max_parallel:
        assert allowed_2 == max_density, "密度约束应生效"

    # 场景3：候选者数量最小
    candidates_few = create_test_candidates(2, PassengerType.PA2)
    allowed_3 = check_PW2_admission(candidates_few, D_PW2=0, K_PW2=0.0, params=params)
    print(f"\n  场景3（候选少）: 候选={len(candidates_few)}, D_PW2=0")
    print(f"    允许={allowed_3} (期望: {len(candidates_few)}，候选数最小)")
    assert allowed_3 == len(candidates_few), "候选者数量应限制"

    # 场景4：接近最大密度
    D_PW2_max = int(params.A_PW2 * params.K_PW2_max - 1)
    K_PW2_max = D_PW2_max / params.A_PW2
    allowed_4 = check_PW2_admission(candidates, D_PW2=D_PW2_max, K_PW2=K_PW2_max, params=params)
    print(f"\n  场景4（接近最大）: 候选={len(candidates)}, D_PW2={D_PW2_max}")
    print(f"    允许={allowed_4} (期望: 1，只剩1个位置)")
    assert allowed_4 <= 1, "接近最大密度时应限制"

    print("  ✓ 通过")


def test_SA3_density_constraint():
    """测试SA3密度约束（Eq.12）"""
    print("\n[测试] SA3密度约束")

    params = SystemParameters()

    print(f"  区域参数: A_SA3={params.A_SA3}m², K_max={params.K_SA3_max}ped/m²")

    candidates = create_test_candidates(20)

    # 场景1：空闲状态
    allowed_1 = check_SA3_admission(candidates, D_SA3=0, K_SA3=0.0, params=params)
    remaining_1 = params.A_SA3 * params.K_SA3_max
    print(f"\n  场景1（空闲）: 候选={len(candidates)}, D_SA3=0")
    print(f"    剩余容量={remaining_1:.0f}, 允许={allowed_1} (期望: {len(candidates)})")
    assert allowed_1 == len(candidates), "空闲时应允许全部"

    # 场景2：中等密度
    D_SA3_mid = 60
    K_SA3_mid = D_SA3_mid / params.A_SA3
    remaining_2 = params.A_SA3 * params.K_SA3_max - D_SA3_mid
    max_allowed_2 = int(remaining_2)
    allowed_2 = check_SA3_admission(candidates, D_SA3=D_SA3_mid, K_SA3=K_SA3_mid, params=params)

    print(f"\n  场景2（中等）: 候选={len(candidates)}, D_SA3={D_SA3_mid}")
    print(f"    剩余容量={remaining_2:.1f}, 允许={allowed_2} (期望: {min(len(candidates), max_allowed_2)})")
    assert allowed_2 == min(len(candidates), max_allowed_2), "密度约束错误"

    # 场景3：接近最大密度
    D_SA3_max = int(params.A_SA3 * params.K_SA3_max - 5)
    K_SA3_max = D_SA3_max / params.A_SA3
    allowed_3 = check_SA3_admission(candidates, D_SA3=D_SA3_max, K_SA3=K_SA3_max, params=params)

    print(f"\n  场景3（接近最大）: 候选={len(candidates)}, D_SA3={D_SA3_max}")
    print(f"    允许={allowed_3} (期望: <=5)")
    assert allowed_3 <= 5, "接近最大时应严格限制"

    # 场景4：已达最大密度
    D_SA3_full = int(params.A_SA3 * params.K_SA3_max)
    K_SA3_full = D_SA3_full / params.A_SA3
    allowed_4 = check_SA3_admission(candidates, D_SA3=D_SA3_full, K_SA3=K_SA3_full, params=params)

    print(f"\n  场景4（已满）: 候选={len(candidates)}, D_SA3={D_SA3_full}")
    print(f"    允许={allowed_4} (期望: 0)")
    assert allowed_4 == 0, "已满时应阻塞全部"

    print("  ✓ 通过")


def test_gate_capacity_constraint():
    """测试Gate闸机数量约束"""
    print("\n[测试] Gate闸机数量约束")

    params = SystemParameters()

    print(f"  闸机数量: N_G={params.N_G}")

    # 场景1：候选少于闸机
    candidates_few = create_test_candidates(3)
    allowed_1 = check_gate_admission(candidates_few, params)
    print(f"\n  场景1: 候选={len(candidates_few)}, 允许={allowed_1} (期望: 3)")
    assert allowed_1 == 3, "候选少于闸机时应全部通过"

    # 场景2：候选等于闸机
    candidates_eq = create_test_candidates(5)
    allowed_2 = check_gate_admission(candidates_eq, params)
    print(f"  场景2: 候选={len(candidates_eq)}, 允许={allowed_2} (期望: 5)")
    assert allowed_2 == 5, "候选等于闸机时应全部通过"

    # 场景3：候选多于闸机
    candidates_many = create_test_candidates(10)
    allowed_3 = check_gate_admission(candidates_many, params)
    print(f"  场景3: 候选={len(candidates_many)}, 允许={allowed_3} (期望: 5)")
    assert allowed_3 == 5, "候选多于闸机时应限制为N_G"

    # 场景4：大量候选
    candidates_huge = create_test_candidates(100)
    allowed_4 = check_gate_admission(candidates_huge, params)
    print(f"  场景4: 候选={len(candidates_huge)}, 允许={allowed_4} (期望: 5)")
    assert allowed_4 == 5, "大量候选时仍应限制为N_G"

    print("  ✓ 通过")


def test_constraint_consistency():
    """测试约束判定的一致性"""
    print("\n[测试] 约束判定一致性")

    params = SystemParameters()
    candidates = create_test_candidates(10)

    # PW1: 多次调用应返回相同结果
    r1 = check_PW1_admission(candidates, D_PW1=5, params=params)
    r2 = check_PW1_admission(candidates, D_PW1=5, params=params)
    assert r1 == r2, "PW1判定不一致"
    print(f"  PW1一致性: {r1} == {r2} ✓")

    # PW2: 多次调用应返回相同结果
    r3 = check_PW2_admission(candidates, D_PW2=10, K_PW2=1.0, params=params)
    r4 = check_PW2_admission(candidates, D_PW2=10, K_PW2=1.0, params=params)
    assert r3 == r4, "PW2判定不一致"
    print(f"  PW2一致性: {r3} == {r4} ✓")

    # SA3: 多次调用应返回相同结果
    r5 = check_SA3_admission(candidates, D_SA3=30, K_SA3=1.0, params=params)
    r6 = check_SA3_admission(candidates, D_SA3=30, K_SA3=1.0, params=params)
    assert r5 == r6, "SA3判定不一致"
    print(f"  SA3一致性: {r5} == {r6} ✓")

    # Gate: 多次调用应返回相同结果
    r7 = check_gate_admission(candidates, params)
    r8 = check_gate_admission(candidates, params)
    assert r7 == r8, "Gate判定不一致"
    print(f"  Gate一致性: {r7} == {r8} ✓")

    print("  ✓ 通过")


def test_edge_cases():
    """测试边界情况"""
    print("\n[测试] 边界情况")

    params = SystemParameters()

    # 空候选列表
    empty_candidates = []
    assert check_PW1_admission(empty_candidates, 5, params) == 0
    assert check_PW2_admission(empty_candidates, 5, 0.5, params) == 0
    assert check_SA3_admission(empty_candidates, 30, 1.0, params) == 0
    assert check_gate_admission(empty_candidates, params) == 0
    print("  空候选列表: ✓")

    # 单个候选者
    single = create_test_candidates(1)
    assert check_PW1_admission(single, 5, params) == 1
    assert check_PW2_admission(single, 0, 0.0, params) == 1
    assert check_SA3_admission(single, 0, 0.0, params) == 1
    assert check_gate_admission(single, params) == 1
    print("  单个候选者: ✓")

    # 极端人数（D=0）
    candidates = create_test_candidates(5)
    assert check_PW1_admission(candidates, 0, params) == 5
    assert check_PW2_admission(candidates, 0, 0.0, params) >= 1  # 至少允许一些
    assert check_SA3_admission(candidates, 0, 0.0, params) == 5
    print("  极端人数（D=0）: ✓")

    print("  ✓ 通过")


def test_diagnostic_functions():
    """测试诊断函数"""
    print("\n[测试] 诊断函数")

    params = SystemParameters()

    # PW1诊断
    diag1 = diagnose_PW1_constraint(D_PW1=15, params=params)
    assert 'H' in diag1
    assert 'is_blocked' in diag1
    print(f"  PW1诊断: H={diag1['H']:.2f}, 阻塞={diag1['is_blocked']}")

    # PW2诊断
    diag2 = diagnose_PW2_constraint(D_PW2=20, K_PW2=2.0, n_candidates=10, params=params)
    assert 'limiting_factor' in diag2
    assert 'allowed' in diag2
    print(f"  PW2诊断: 限制因素={diag2['limiting_factor']}, 允许={diag2['allowed']}")

    # SA3诊断
    diag3 = diagnose_SA3_constraint(D_SA3=50, K_SA3=1.7, n_candidates=15, params=params)
    assert 'remaining_capacity' in diag3
    assert 'is_blocked' in diag3
    print(f"  SA3诊断: 剩余容量={diag3['remaining_capacity']:.1f}, 阻塞={diag3['is_blocked']}")

    print("  ✓ 通过")


if __name__ == "__main__":
    print("=" * 70)
    print("admission_control.py 单元测试")
    print("=" * 70)

    test_PW1_hard_switch()
    test_PW2_dual_constraint()
    test_SA3_density_constraint()
    test_gate_capacity_constraint()
    test_constraint_consistency()
    test_edge_cases()
    test_diagnostic_functions()

    print("\n" + "=" * 70)
    print("所有测试通过！✓")
    print("=" * 70)
