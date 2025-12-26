"""
准入判定模块：实现 Eq.(9)-(12) 的约束判定
对应设计书：第4.2节附加通过时间 + 准入判定规则

核心功能：
- 判断候选乘客能否进入下一子区域
- 返回"允许进入的人数"
- 不修改乘客状态（由simulation_engine负责）

【v1.1 更新】（2025-12-26）：
- 改进check_PW2_admission：显式的三重限制（密度检查 + 体宽 + 容量）
- 更严格地实现论文Eq.10 & Eq.11
- 对应论文Section 2.2的完整描述
"""

from typing import List
import math

# 条件导入：支持两种运行方式
try:
    from src.data_structures import Passenger, SystemParameters
except ModuleNotFoundError:
    from data_structures import Passenger, SystemParameters


def check_PW1_admission(candidates: List[Passenger], D_PW1: int,
                        params: SystemParameters) -> int:
    """检查PW1准入条件（Eq.9）

    物理约束：静态厚度约束（硬开关规则）

    Args:
        candidates: 试图进入PW1的候选乘客列表（已按编号排序）
        D_PW1: PW1当前人数
        params: 系统参数

    Returns:
        int: 允许进入的人数

    Note:
        - H = D_PW1 - L_SE/v_SE
        - H > 0: 通道已超出设备消化能力，暂停新增进入（max_enter=0）
        - H <= 0: 允许进入（max_enter=len(candidates)）
        - 对应设计书4.2.2(1)：PW1硬开关规则
        - L_SE/v_SE 作为"单位时间尺度上的通道承载能力指标"
    """
    # Eq.(9): 静态厚度
    capacity_proxy = params.L_SE / params.v_SE
    H = D_PW1 - capacity_proxy

    if H > 0:
        # 硬开关：超出消化能力，暂停进入
        return 0
    else:
        # 允许全部进入
        return len(candidates)


def check_PW2_admission(candidates: List[Passenger], D_PW2: int, K_PW2: float,
                        params: SystemParameters) -> int:
    """检查PW2准入条件（Eq.10 & Eq.11 - 双重约束）

    物理约束：密度检查 + 体宽约束 + 容量约束（三重约束）

    Args:
        candidates: 试图进入PW2的候选乘客列表（已按编号排序）
        D_PW2: PW2当前人数
        K_PW2: PW2当前密度（ped/m²）
        params: 系统参数

    Returns:
        int: 允许进入的人数

    Note:
        论文Eq.10 & Eq.11的完整实现：
        - 限制A（密度检查）: K_PW2 < K_max（超过则完全阻塞）
        - 限制B（体宽约束）: Σ W_B ≤ W_PW2（Eq.10，并行限制）
        - 限制C（容量约束）: D_PW2_in = A_PW2 × K_max - D_PW2（Eq.11，剩余空间）
        - 取三者最小值

    对应设计书4.2.2(2) + 6.1裁决
    """
    n_candidates = len(candidates)

    # 限制A：密度检查（论文Section 2.2原文）
    # "When the passenger density in the passageway2 increases..."
    if K_PW2 >= params.K_PW2_max:
        # 密度已达上限，完全阻塞
        return 0

    # 限制B：体宽约束（Eq.10）
    # 论文原文："Passengers2 from subarea1 will generally enter the
    # passageway2 side by side. When the sum of the body widths of
    # these passengers exceeds the width of the passageway2..."
    W_PW2 = params.W_PW2
    max_parallel = int(W_PW2 / params.W_B)  # floor操作

    # 限制C：容量约束（Eq.11）
    # 论文原文："D_PW2,in,T = A_PW2 × (K_PW2,max - K_PW2,T)"
    # 这里使用绝对人数形式（等价）
    max_capacity = int(params.A_PW2 * params.K_PW2_max)  # 最大容纳人数 ≈ 35人
    remaining = max_capacity - D_PW2
    if remaining <= 0:
        # 容量已满，完全阻塞
        return 0

    # 取三者最小值
    allowed = min(n_candidates, max_parallel, remaining)

    return allowed


def check_SA3_admission(candidates: List[Passenger], D_SA3: int, K_SA3: float,
                        params: SystemParameters) -> int:
    """检查SA3准入条件（Eq.12）

    物理约束：密度容量约束

    Args:
        candidates: 试图进入SA3的候选乘客列表（已按编号排序）
        D_SA3: SA3当前人数
        K_SA3: SA3当前密度（ped/m²）
        params: 系统参数

    Returns:
        int: 允许进入的人数

    Note:
        - D_SA3_in = A_SA3 × K_max - D_SA3
        - 候选者包含PW1和PW2的汇合（已按编号排序，对应设计书6.5）
        - 对应设计书4.2.2(3)
    """
    n_candidates = len(candidates)

    # Eq.(12): 密度容量约束
    remaining_capacity = params.A_SA3 * params.K_SA3_max - D_SA3
    max_allowed = int(remaining_capacity) if remaining_capacity > 0 else 0  # floor操作

    return min(n_candidates, max_allowed)


def check_gate_admission(candidates: List[Passenger], params: SystemParameters) -> int:
    """检查Gate准入条件（闸机数量约束）

    物理约束：每时间步最多N_G人通过

    Args:
        candidates: 试图通过闸机的候选乘客列表（已按编号排序）
        params: 系统参数

    Returns:
        int: 允许通过的人数

    Note:
        - 每时间步最多 N_G 人通过
        - 简化模式B：不维护单个闸机占用状态
        - ⚠️ t_s 已在 t_SA3_basic 中计算，Gate仅做容量限制
        - 对应设计书4.2.2(4) + 6.2裁决
    """
    n_candidates = len(candidates)

    # 闸机数量约束
    max_pass = params.N_G

    return min(n_candidates, max_pass)


# ==================== 辅助函数：约束诊断 ====================

def diagnose_PW1_constraint(D_PW1: int, params: SystemParameters) -> dict:
    """诊断PW1约束状态（调试用）"""
    capacity_proxy = params.L_SE / params.v_SE
    H = D_PW1 - capacity_proxy

    return {
        'D_PW1': D_PW1,
        'capacity_proxy': capacity_proxy,
        'H': H,
        'is_blocked': H > 0,
        'reason': '超出设备消化能力' if H > 0 else '正常'
    }


def diagnose_PW2_constraint(D_PW2: int, K_PW2: float, n_candidates: int,
                            params: SystemParameters) -> dict:
    """诊断PW2约束状态（调试用）"""
    # 密度检查
    is_density_blocked = K_PW2 >= params.K_PW2_max

    # 体宽约束
    W_PW2 = params.W_PW2
    max_parallel = int(W_PW2 / params.W_B)

    # 容量约束
    max_capacity = int(params.A_PW2 * params.K_PW2_max)
    remaining = max_capacity - D_PW2
    is_capacity_full = remaining <= 0

    if is_density_blocked:
        allowed = 0
        limiting_factor = '密度超标（完全阻塞）'
    elif is_capacity_full:
        allowed = 0
        limiting_factor = '容量已满（完全阻塞）'
    else:
        allowed = min(n_candidates, max_parallel, remaining)

        # 判断限制因素
        if allowed == max_parallel and allowed < n_candidates:
            limiting_factor = '体宽约束'
        elif allowed == remaining and allowed < n_candidates:
            limiting_factor = '容量约束'
        elif allowed == n_candidates:
            limiting_factor = '无约束'
        else:
            limiting_factor = '混合约束'

    return {
        'D_PW2': D_PW2,
        'K_PW2': K_PW2,
        'K_max': params.K_PW2_max,
        'is_density_blocked': is_density_blocked,
        'max_capacity': max_capacity,
        'remaining': remaining,
        'is_capacity_full': is_capacity_full,
        'n_candidates': n_candidates,
        'max_parallel': max_parallel,
        'allowed': allowed,
        'limiting_factor': limiting_factor
    }


def diagnose_SA3_constraint(D_SA3: int, K_SA3: float, n_candidates: int,
                            params: SystemParameters) -> dict:
    """诊断SA3约束状态（调试用）"""
    remaining_capacity = params.A_SA3 * params.K_SA3_max - D_SA3
    max_allowed = int(remaining_capacity) if remaining_capacity > 0 else 0

    allowed = min(n_candidates, max_allowed)

    return {
        'D_SA3': D_SA3,
        'K_SA3': K_SA3,
        'n_candidates': n_candidates,
        'remaining_capacity': remaining_capacity,
        'max_allowed': max_allowed,
        'allowed': allowed,
        'is_blocked': allowed < n_candidates
    }


# ==================== 模块测试函数 ====================

if __name__ == "__main__":
    """模块自测：验证准入判定正确性"""

    # 自测时的导入
    import sys
    import os
    if 'src' not in sys.path[0]:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import PassengerType, Position, SystemParameters
    from data_structures import Passenger

    print("=" * 70)
    print("准入判定模块自测")
    print("=" * 70)

    params = SystemParameters()

    # 创建测试候选者
    def create_candidates(n: int, ptype: PassengerType = PassengerType.PA1) -> List[Passenger]:
        return [Passenger(i, ptype, Position.SA1) for i in range(n)]

    # 测试1：PW1准入（硬开关）
    print("\n[测试1] PW1准入判定（Eq.9 - 硬开关）")
    capacity_proxy = params.L_SE / params.v_SE
    print(f"  容量指标: L_SE/v_SE = {capacity_proxy:.2f}")

    test_cases_PW1 = [
        (5, "未超载"),
        (11, "接近满载"),
        (12, "超载（触发硬开关）"),
        (20, "严重超载")
    ]

    candidates = create_candidates(10)

    print(f"\n  {'D_PW1':<10} {'H值':<10} {'允许进入':<15} {'说明'}")
    print(f"  {'-'*10} {'-'*10} {'-'*15} {'-'*30}")

    for D_PW1, desc in test_cases_PW1:
        allowed = check_PW1_admission(candidates, D_PW1, params)
        H = D_PW1 - capacity_proxy
        print(f"  {D_PW1:<10} {H:<10.2f} {allowed:<15} {desc}")

        # 验证逻辑
        if H > 0:
            assert allowed == 0, f"H>0时应阻塞全部"
        else:
            assert allowed == len(candidates), f"H<=0时应允许全部"

    print("  ✓ 通过（硬开关逻辑正确）")

    # 测试2：PW2准入（三重约束）
    print("\n[测试2] PW2准入判定（Eq.10 & Eq.11 - 三重约束）")
    W_PW2 = params.W_PW2
    max_parallel = int(W_PW2 / params.W_B)
    max_capacity = int(params.A_PW2 * params.K_PW2_max)
    print(f"  体宽约束: W_PW2={W_PW2:.3f}m, W_B={params.W_B}m → max_parallel={max_parallel}人")
    print(f"  容量约束: A_PW2={params.A_PW2}m², K_max={params.K_PW2_max}ped/m² → max_capacity={max_capacity}人")

    test_cases_PW2 = [
        (0, 0.0, "空闲状态"),
        (5, 0.5, "低密度"),
        (20, 2.0, "中等密度"),
        (34, 3.4, "接近最大密度"),
        (35, 3.5, "达到K_max（密度阻塞）")
    ]

    candidates = create_candidates(10, PassengerType.PA2)

    print(f"\n  {'D_PW2':<10} {'K_PW2':<10} {'剩余':<10} {'体宽限':<10} {'允许':<10} {'说明'}")
    print(f"  {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*20}")

    for D_PW2, K_PW2, desc in test_cases_PW2:
        allowed = check_PW2_admission(candidates, D_PW2, K_PW2, params)

        # 重新计算约束值（验证用）
        remaining = max_capacity - D_PW2

        print(f"  {D_PW2:<10} {K_PW2:<10.2f} {remaining:<10} {max_parallel:<10} {allowed:<10} {desc}")

        # 验证逻辑
        if K_PW2 >= params.K_PW2_max or remaining <= 0:
            assert allowed == 0, f"密度超标或容量满时应阻塞"
        else:
            expected = min(len(candidates), max_parallel, remaining)
            assert allowed == expected, f"约束计算错误"

    print("  ✓ 通过（三重约束：密度检查 + 体宽 + 容量）")

    # 测试3：SA3准入（密度约束）
    print("\n[测试3] SA3准入判定（Eq.12 - 密度约束）")
    print(f"  区域参数: A_SA3={params.A_SA3}m², K_max={params.K_SA3_max}ped/m²")

    test_cases_SA3 = [
        (0, 0.0, "空闲状态"),
        (30, 1.0, "低密度"),
        (60, 2.0, "中等密度"),
        (100, 3.4, "接近最大密度")
    ]

    candidates = create_candidates(20)

    print(f"\n  {'D_SA3':<10} {'K_SA3':<10} {'剩余容量':<15} {'允许':<10} {'说明'}")
    print(f"  {'-'*10} {'-'*10} {'-'*15} {'-'*10} {'-'*20}")

    for D_SA3, K_SA3, desc in test_cases_SA3:
        allowed = check_SA3_admission(candidates, D_SA3, K_SA3, params)

        remaining = params.A_SA3 * params.K_SA3_max - D_SA3
        max_allowed = int(remaining) if remaining > 0 else 0

        print(f"  {D_SA3:<10} {K_SA3:<10.2f} {remaining:<15.2f} {allowed:<10} {desc}")

        # 验证逻辑
        expected = min(len(candidates), max_allowed)
        assert allowed == expected, f"约束计算错误"

    print("  ✓ 通过（密度约束正确）")

    # 测试4：Gate准入（闸机数量约束）
    print("\n[测试4] Gate准入判定（闸机数量约束）")
    print(f"  闸机数量: N_G={params.N_G}")

    test_cases_gate = [
        (3, "候选者少于闸机"),
        (5, "候选者等于闸机"),
        (10, "候选者多于闸机")
    ]

    print(f"\n  {'候选人数':<15} {'允许通过':<15} {'说明'}")
    print(f"  {'-'*15} {'-'*15} {'-'*30}")

    for n, desc in test_cases_gate:
        candidates = create_candidates(n)
        allowed = check_gate_admission(candidates, params)

        print(f"  {n:<15} {allowed:<15} {desc}")

        # 验证逻辑
        expected = min(n, params.N_G)
        assert allowed == expected, f"闸机约束错误"

    print("  ✓ 通过（闸机约束正确）")

    # 测试5：诊断函数
    print("\n[测试5] 约束诊断函数")

    print("\n  PW1诊断:")
    diag_pw1 = diagnose_PW1_constraint(D_PW1=15, params=params)
    for key, value in diag_pw1.items():
        print(f"    {key}: {value}")

    print("\n  PW2诊断:")
    diag_pw2 = diagnose_PW2_constraint(D_PW2=25, K_PW2=2.5, n_candidates=10, params=params)
    for key, value in diag_pw2.items():
        print(f"    {key}: {value}")

    print("\n  SA3诊断:")
    diag_sa3 = diagnose_SA3_constraint(D_SA3=80, K_SA3=2.7, n_candidates=15, params=params)
    for key, value in diag_sa3.items():
        print(f"    {key}: {value}")

    print("  ✓ 通过（诊断函数正常）")

    print("\n" + "=" * 70)
    print("所有测试通过！准入判定逻辑正确。")
    print("=" * 70)
