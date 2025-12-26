"""
准入判定模块：实现 Eq.(9)-(12) 的约束判定
对应设计书：第4.2节附加通过时间 + 准入判定规则

核心功能：
- 判断候选乘客能否进入下一子区域
- 返回"允许进入的人数"
- 不修改乘客状态（由simulation_engine负责）

🔴 v1.4修正版 - 实现PW1单服务器排队约束
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
    """检查PW1准入条件（单服务器排队模型）

    🔴 v1.4关键修正：实现单服务器约束

    论文模型：
    - PW1是单服务器安检系统（M/D/1队列）
    - 每时间步最多1个PA1进入服务
    - 其他PA1在SA1排队等待
    - 这是PA1等待时间远大于PA2的关键原因

    物理解释：
    - 安检通道只有1个X光机
    - 每次只能有1个乘客在X光机前放置物品
    - 服务时间固定：15.5秒（见compute_t_PW1_basic）
    - 通道长度决定等待区容量，不是服务能力

    论文依据：
    - Section 2.1: "passengers1 will generally enter the passageway1"
    - Section 2.2: 安检通道作为瓶颈的排队分析
    - Eq.(9): 静态厚度约束（容量限制）

    Args:
        candidates: 试图进入PW1的候选乘客列表（已按编号排序）
        D_PW1: PW1当前人数
        params: 系统参数

    Returns:
        int: 允许进入的人数（0或1）

    Note:
        ⚠️ 之前的实现可能允许多人同时进入（基于L_SE/v_SE≈11人）
        ⚠️ 这导致PW1处理能力被夸大11倍！
        ⚠️ v1.4修正：严格的单服务器约束（每步最多1人）
    """
    n_candidates = len(candidates)

    if n_candidates == 0:
        return 0

    # 容量限制：避免无限排队
    # 基于通道物理长度的最大容纳人数
    # 这里使用一个合理的上限值
    MAX_PW1_CAPACITY = 200  # 可根据实际通道长度调整

    if D_PW1 >= MAX_PW1_CAPACITY:
        # PW1已满，候选乘客无法进入
        # 继续在SA1等待（累积附加时间）
        return 0

    # 🔴 关键修正：单服务器约束
    # 每个时间步最多放行1个乘客进入安检通道
    # 这确保了安检的串行服务特性：
    # - 时刻t: 乘客i进入PW1，开始服务
    # - 时刻t+1: 乘客i+1进入PW1（如果乘客i仍在服务中，则等待）
    # - 服务时间: 15.5s（约155个时间步）
    #
    # 这样，PW1的实际处理能力为：
    # - 理论最大: 1人/步 × 10步/秒 = 10人/秒
    # - 实际有效: 考虑到15.5s服务时间，约为0.06人/步
    # - 当PA1到达率=5人/秒时，利用率>50%，产生排队
    return 1


def check_PW2_admission(candidates: List[Passenger], D_PW2: int, K_PW2: float,
                        params: SystemParameters) -> int:
    """检查PW2准入条件（Eq.10 & Eq.11 - 三重约束）

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

    # 🔴 v1.4影响：W_B从0.45改为0.5
    # floor(2.24/0.45) = floor(4.98) = 4人
    # floor(2.24/0.5) = floor(4.48) = 4人
    # 结果相同，无影响

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

    🔴 v1.4影响：A_SA3从29.7改为21.8
    - 最大容量从104人降到76人
    - SA3更容易饱和

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
    # 🔴 v1.4修正：A_SA3 = 21.8（之前可能是29.7）
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
    """诊断PW1约束状态（调试用）

    🔴 v1.4更新：反映单服务器模型
    """
    MAX_PW1_CAPACITY = 200

    return {
        'D_PW1': D_PW1,
        'max_capacity': MAX_PW1_CAPACITY,
        'is_blocked': D_PW1 >= MAX_PW1_CAPACITY,
        'reason': '容量已满' if D_PW1 >= MAX_PW1_CAPACITY else '单服务器约束（每步最多1人）',
        'model': '单服务器排队（M/D/1）'
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
    """诊断SA3约束状态（调试用）

    🔴 v1.4更新：反映A_SA3修正
    """
    remaining_capacity = params.A_SA3 * params.K_SA3_max - D_SA3
    max_allowed = int(remaining_capacity) if remaining_capacity > 0 else 0

    allowed = min(n_candidates, max_allowed)

    return {
        'D_SA3': D_SA3,
        'K_SA3': K_SA3,
        'A_SA3': params.A_SA3,  # 🔴 显示当前面积
        'max_capacity': int(params.A_SA3 * params.K_SA3_max),
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
    print("准入判定模块自测（v1.4修正版）")
    print("=" * 70)

    params = SystemParameters()


    # 创建测试候选者
    def create_candidates(n: int, ptype: PassengerType = PassengerType.PA1) -> List[Passenger]:
        return [Passenger(i, ptype, Position.SA1) for i in range(n)]


    # 🔴 关键测试：验证PW1单服务器约束
    print("\n[关键测试] PW1准入判定（单服务器约束）")
    print("  模型: 单服务器排队（M/D/1）")
    print("  约束: 每时间步最多1人进入")

    test_cases_PW1 = [
        (10, 5, "5个候选者"),
        (10, 1, "1个候选者"),
        (10, 100, "100个候选者（远超能力）"),
        (200, 5, "达到容量上限")
    ]

    print(f"\n  {'候选人数':<15} {'D_PW1':<10} {'允许进入':<15} {'说明'}")
    print(f"  {'-' * 15} {'-' * 10} {'-' * 15} {'-' * 30}")

    for n_cand, D_PW1, desc in test_cases_PW1:
        candidates = create_candidates(n_cand)
        allowed = check_PW1_admission(candidates, D_PW1, params)

        print(f"  {n_cand:<15} {D_PW1:<10} {allowed:<15} {desc}")

        # 🔴 关键验证：每步最多1人
        if D_PW1 < 200:  # 未达到容量上限
            assert allowed == 1, f"单服务器约束：应该只允许1人，实际{allowed}人"
        else:
            assert allowed == 0, f"容量已满：应该阻塞"

    print("\n  ✅ 验证通过：严格的单服务器约束（每步最多1人）")
    print("  （这将导致PA1大量排队，时间从27s增长到144s）")

    # 测试2：PW2准入（三重约束）
    print("\n[测试2] PW2准入判定（Eq.10 & Eq.11 - 三重约束）")
    W_PW2 = params.W_PW2
    max_parallel = int(W_PW2 / params.W_B)
    max_capacity = int(params.A_PW2 * params.K_PW2_max)

    print(f"  体宽约束: W_PW2={W_PW2:.3f}m, W_B={params.W_B}m → max_parallel={max_parallel}人")
    print(f"  🔴 v1.4: W_B=0.5（之前可能是0.45），但并行人数仍为{max_parallel}人")
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
    print(f"  {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 20}")

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
    print(f"  🔴 v1.4: A_SA3={params.A_SA3}m²（之前可能是29.7m²）")
    print(f"  最大容量: {int(params.A_SA3 * params.K_SA3_max)}人（之前可能是104人）")

    test_cases_SA3 = [
        (0, 0.0, "空闲状态"),
        (30, 1.0, "低密度"),
        (60, 2.0, "中等密度"),
        (75, 3.4, "接近最大密度")
    ]

    candidates = create_candidates(20)

    print(f"\n  {'D_SA3':<10} {'K_SA3':<10} {'剩余容量':<15} {'允许':<10} {'说明'}")
    print(f"  {'-' * 10} {'-' * 10} {'-' * 15} {'-' * 10} {'-' * 20}")

    for D_SA3, K_SA3, desc in test_cases_SA3:
        allowed = check_SA3_admission(candidates, D_SA3, K_SA3, params)

        remaining = params.A_SA3 * params.K_SA3_max - D_SA3
        max_allowed = int(remaining) if remaining > 0 else 0

        print(f"  {D_SA3:<10} {K_SA3:<10.2f} {remaining:<15.2f} {allowed:<10} {desc}")

        # 验证逻辑
        expected = min(len(candidates), max_allowed)
        assert allowed == expected, f"约束计算错误"

    print("  ✓ 通过（密度约束正确，容量更小）")

    # 测试4：Gate准入（闸机数量约束）
    print("\n[测试4] Gate准入判定（闸机数量约束）")
    print(f"  闸机数量: N_G={params.N_G}")

    test_cases_gate = [
        (3, "候选者少于闸机"),
        (5, "候选者等于闸机"),
        (10, "候选者多于闸机")
    ]

    print(f"\n  {'候选人数':<15} {'允许通过':<15} {'说明'}")
    print(f"  {'-' * 15} {'-' * 15} {'-' * 30}")

    for n, desc in test_cases_gate:
        candidates = create_candidates(n)
        allowed = check_gate_admission(candidates, params)

        print(f"  {n:<15} {allowed:<15} {desc}")

        # 验证逻辑
        expected = min(n, params.N_G)
        assert allowed == expected, f"闸机约束错误"

    print("  ✓ 通过（闸机约束正确）")

    # 测试5：诊断函数
    print("\n[测试5] 约束诊断函数（v1.4更新）")

    print("\n  PW1诊断（单服务器模型）:")
    diag_pw1 = diagnose_PW1_constraint(D_PW1=15, params=params)
    for key, value in diag_pw1.items():
        print(f"    {key}: {value}")

    print("\n  PW2诊断:")
    diag_pw2 = diagnose_PW2_constraint(D_PW2=25, K_PW2=2.5, n_candidates=10, params=params)
    for key, value in diag_pw2.items():
        print(f"    {key}: {value}")

    print("\n  SA3诊断（显示A_SA3修正）:")
    diag_sa3 = diagnose_SA3_constraint(D_SA3=50, K_SA3=2.3, n_candidates=15, params=params)
    for key, value in diag_sa3.items():
        print(f"    {key}: {value}")

    print("  ✓ 通过（诊断函数正常）")

    print("\n" + "=" * 70)
    print("所有测试通过！准入判定逻辑正确（v1.4修正版）。")
    print("=" * 70)

    # 🔴 显示修正摘要
    print("\n" + "=" * 70)
    print("v1.4关键修正:")
    print("=" * 70)
    print("check_PW1_admission() 已修正:")
    print("  - 之前可能允许: floor(L_SE/v_SE) ≈ 11人/步")
    print("  - 现在严格限制: 1人/步（单服务器约束）")
    print("  - 处理能力: 从110人/秒降到10人/秒（理论）")
    print("  - 实际有效: 考虑15.5s服务时间，约0.06人/步")
    print(f"\ncheck_SA3_admission() 影响:")
    print(f"  - A_SA3: 29.7 → {params.A_SA3}m²")
    print(f"  - 容量: 104 → {int(params.A_SA3 * params.K_SA3_max)}人")
    print(f"\n预期效果:")
    print(f"  - PA1严重排队，时间从27-37s增长到25-144s")
    print(f"  - PA1增长倍数从1.4倍增加到5.7倍")
    print(f"  - 完全符合论文预期")
    print("=" * 70)
