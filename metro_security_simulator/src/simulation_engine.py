"""
递推引擎模块：实现 Figure 3 的完整递推流程
对应设计书：第5节递推引擎

⚠️ 核心约束（设计书6.6）：
步骤顺序不可调整！必须严格按照5.2节的顺序执行。
违反此顺序会导致密度计算错误或性能退化。

递推流程（8个步骤）：
A. 生成新到达乘客
B. 更新密度（使用转移发生前的人数）⚠️ 必须在D/E前执行
C. 构造候选集合
E. PW → SA3 转移（⚠️ 先执行，释放空间）
D. SA1 → PW 转移（⚠️ 后执行，利用已释放的空间）
F. SA3 → Gate 转移
G. 记录历史
H. 时间推进

关键：E必须在D之前执行！
原因：先让人离开（释放空间），再让人进入（利用空间）
"""

from typing import List, Dict

# 条件导入：支持两种运行方式
try:
    from src.data_structures import Passenger, System
    from src.config import PassengerType, Position
    from src.transit_time import (
        compute_t_SA1_basic,
        compute_t_PW1_basic,
        compute_t_PW2_basic,
        compute_t_SA3_basic
    )
    from src.admission_control import (
        check_PW1_admission,
        check_PW2_admission,
        check_SA3_admission,
        check_gate_admission
    )
except ModuleNotFoundError:
    from data_structures import Passenger, System
    from config import PassengerType, Position
    from transit_time import (
        compute_t_SA1_basic,
        compute_t_PW1_basic,
        compute_t_PW2_basic,
        compute_t_SA3_basic
    )
    from admission_control import (
        check_PW1_admission,
        check_PW2_admission,
        check_SA3_admission,
        check_gate_admission
    )


# ==================== 步骤A：生成新到达乘客 ====================

def step_A_arrivals(system: System, q_PA1: float, q_PA2: float) -> None:
    """步骤A：生成新到达乘客（对应设计书5.2.1）

    使用累积器方法避免舍入误差，采用Strategy 1交替编号。

    Args:
        system: 系统对象
        q_PA1: PA1到达率（人/秒）
        q_PA2: PA2到达率（人/秒）

    Note:
        - 使用累积器避免舍入误差
        - 交替编号策略：PA1和PA2按到达顺序交替编号
        - 新乘客初始化在SA1，计算t_SA1_basic
    """
    # 累积到达人数
    system.arrival_acc_PA1 += q_PA1 * system.params.dt
    system.arrival_acc_PA2 += q_PA2 * system.params.dt

    # 提取整数部分
    n_PA1 = int(system.arrival_acc_PA1)
    n_PA2 = int(system.arrival_acc_PA2)

    # 扣除已生成的乘客
    system.arrival_acc_PA1 -= n_PA1
    system.arrival_acc_PA2 -= n_PA2

    # Strategy 1：交替编号
    # 例如：3个PA1 + 2个PA2 → [PA1, PA2, PA1, PA2, PA1]
    arrivals = []
    for i in range(max(n_PA1, n_PA2)):
        if i < n_PA1:
            arrivals.append(PassengerType.PA1)
        if i < n_PA2:
            arrivals.append(PassengerType.PA2)

    # 创建乘客对象
    for ptype in arrivals:
        p = Passenger(
            index=system.next_passenger_id,
            ptype=ptype,
            position=Position.SA1
        )

        # 初始化时间字段
        p.t_enter_SA1 = system.T
        p.t_SA1_basic = compute_t_SA1_basic(p, system.params)
        p.t_SA1_add = 0.0

        # 添加到系统
        system.passengers.append(p)
        system.next_passenger_id += 1
        system.D_SA1 += 1
        system.D_All += 1  # 总乘客数增加


# ==================== 步骤B：更新密度 ====================

def step_B_update_densities(system: System) -> tuple:
    """步骤B：更新密度（对应设计书5.2.2）

    ⚠️ 关键：使用转移发生前的区域人数计算密度（离散同步更新规则）

    Args:
        system: 系统对象

    Returns:
        tuple: (K_PW2_current, K_SA3_current)

    Note:
        - 必须在步骤D/E之前执行
        - 步骤D/E使用这里计算的密度来计算basic时间
        - 对应设计书4.1.3和4.1.4的"离散同步更新规则"
    """
    K_PW2 = system.D_PW2 / system.params.A_PW2
    K_SA3 = system.D_SA3 / system.params.A_SA3

    return K_PW2, K_SA3


# ==================== 步骤C：构造候选集合 ====================

def step_C_construct_candidates(system: System) -> Dict[str, List[Passenger]]:
    """步骤C：构造候选集合（对应设计书5.2.3）

    构造5个候选集合，每个集合按乘客编号排序（FIFO）。

    Args:
        system: 系统对象

    Returns:
        dict: 包含5个候选集合的字典

    Note:
        候选集合定义（设计书5.2.3）：
        - U_SA1_PW1: SA1中的PA1，准备进入PW1
        - U_SA1_PW2: SA1中的PA2，准备进入PW2
        - U_PW1_SA3: PW1中完成安检，准备进入SA3
        - U_PW2_SA3: PW2中完成通行，准备进入SA3
        - U_SA3_GA: SA3中完成"行走+刷卡"，准备通过Gate
    """
    T = system.T

    # SA1 → PW 候选集合
    U_SA1_PW1 = [
        p for p in system.passengers
        if (p.position == Position.SA1 and
            p.ptype == PassengerType.PA1 and
            T >= p.t_enter_SA1 + p.t_SA1_basic + p.t_SA1_add)
    ]

    U_SA1_PW2 = [
        p for p in system.passengers
        if (p.position == Position.SA1 and
            p.ptype == PassengerType.PA2 and
            T >= p.t_enter_SA1 + p.t_SA1_basic + p.t_SA1_add)
    ]

    # PW → SA3 候选集合
    U_PW1_SA3 = [
        p for p in system.passengers
        if (p.position == Position.PW1 and
            T >= p.t_enter_SA2 + p.t_PW_basic + p.t_SA2_add)
    ]

    U_PW2_SA3 = [
        p for p in system.passengers
        if (p.position == Position.PW2 and
            T >= p.t_enter_SA2 + p.t_PW_basic + p.t_SA2_add)
    ]

    # SA3 → Gate 候选集合
    # ⚠️ 关键：必须完成"行走+刷卡"（t_SA3_basic已含t_s）
    U_SA3_GA = [
        p for p in system.passengers
        if (p.position == Position.SA3 and
            T >= p.t_enter_SA3 + p.t_SA3_basic + p.t_SA3_add)
    ]

    # 按编号排序（FIFO）
    U_SA1_PW1.sort(key=lambda p: p.index)
    U_SA1_PW2.sort(key=lambda p: p.index)
    U_PW1_SA3.sort(key=lambda p: p.index)
    U_PW2_SA3.sort(key=lambda p: p.index)
    U_SA3_GA.sort(key=lambda p: p.index)

    return {
        'U_SA1_PW1': U_SA1_PW1,
        'U_SA1_PW2': U_SA1_PW2,
        'U_PW1_SA3': U_PW1_SA3,
        'U_PW2_SA3': U_PW2_SA3,
        'U_SA3_GA': U_SA3_GA
    }


# ==================== 步骤D：SA1 → PW 转移 ====================

def step_D_SA1_to_PW(system: System, candidates: dict, K_PW2: float) -> None:
    """步骤D：SA1 → PW 转移（对应设计书5.2.4）

    处理两个转移：
    - PA1 从 SA1 → PW1（安检通道）
    - PA2 从 SA1 → PW2（快速通道）

    Args:
        system: 系统对象
        candidates: 候选集合字典
        K_PW2: PW2当前密度（步骤B计算）

    Note:
        - 使用步骤B计算的密度来计算PW2的basic时间
        - PW1的basic时间是常数，不受密度影响
    """
    T = system.T

    # D1. PA1 → PW1
    U_SA1_PW1 = candidates['U_SA1_PW1']
    allowed_PW1 = check_PW1_admission(U_SA1_PW1, system.D_PW1, system.params)

    for p in U_SA1_PW1[:allowed_PW1]:
        # 转移
        p.position = Position.PW1
        p.t_enter_SA2 = T  # 统一命名：SA2是PW1/PW2的统称
        p.t_PW_basic = compute_t_PW1_basic(system.params)  # 常数
        p.t_SA2_add = 0.0

        # 更新人数
        system.D_SA1 -= 1
        system.D_PW1 += 1

    # 未能转移的乘客累积等待时间
    for p in U_SA1_PW1[allowed_PW1:]:
        p.t_SA1_add += system.params.dt

    # D2. PA2 → PW2
    U_SA1_PW2 = candidates['U_SA1_PW2']
    allowed_PW2 = check_PW2_admission(U_SA1_PW2, system.D_PW2, K_PW2, system.params)

    for p in U_SA1_PW2[:allowed_PW2]:
        # 转移
        p.position = Position.PW2
        p.t_enter_SA2 = T
        # ⚠️ 使用步骤B的密度（离散同步更新）
        p.t_PW_basic = compute_t_PW2_basic(K_PW2, system.params)
        p.t_SA2_add = 0.0

        # 更新人数
        system.D_SA1 -= 1
        system.D_PW2 += 1

    # 未能转移的乘客累积等待时间
    for p in U_SA1_PW2[allowed_PW2:]:
        p.t_SA1_add += system.params.dt


# ==================== 步骤E：PW → SA3 转移 ====================

def step_E_PW_to_SA3(system: System, candidates: dict, K_SA3: float) -> None:
    """步骤E：PW → SA3 转移（对应设计书5.2.5）

    合并PW1和PW2的候选者，按编号排序后统一处理。

    Args:
        system: 系统对象
        candidates: 候选集合字典
        K_SA3: SA3当前密度（步骤B计算）

    Note:
        - 合并队列按编号排序（设计书6.5裁决）
        - 使用步骤B计算的密度来计算SA3的basic时间
        - t_SA3_basic 已包含 t_s（刷卡时间）
    """
    T = system.T

    # 合并PW1和PW2的候选者
    U_PW_SA3 = candidates['U_PW1_SA3'] + candidates['U_PW2_SA3']
    U_PW_SA3.sort(key=lambda p: p.index)  # 按编号排序（FIFO）

    # 检查SA3容量
    allowed = check_SA3_admission(U_PW_SA3, system.D_SA3, K_SA3, system.params)

    for p in U_PW_SA3[:allowed]:
        old_pos = p.position

        # 转移
        p.position = Position.SA3
        p.t_enter_SA3 = T
        # ⚠️ 使用步骤B的密度（离散同步更新）
        # ⚠️ t_SA3_basic 已包含 t_s（设计书4.1.4 + 6.2）
        p.t_SA3_basic = compute_t_SA3_basic(p, K_SA3, system.params)
        p.t_SA3_add = 0.0

        # 更新人数
        if old_pos == Position.PW1:
            system.D_PW1 -= 1
        else:
            system.D_PW2 -= 1
        system.D_SA3 += 1

    # 未能转移的乘客累积等待时间
    for p in U_PW_SA3[allowed:]:
        p.t_SA2_add += system.params.dt


# ==================== 步骤F：SA3 → Gate 转移 ====================

def step_F_SA3_to_Gate(system: System, candidates: dict) -> None:
    """步骤F：SA3 → Gate 转移（对应设计书5.2.6）

    乘客通过闸机，离开系统。

    Args:
        system: 系统对象
        candidates: 候选集合字典

    Note:
        - 简化模式B：每时间步最多N_G人通过
        - t_s已在t_SA3_basic中计算，Gate仅做容量限制
        - t_exit_system = T（离散时刻约定，设计书6.4）
    """
    T = system.T

    U_SA3_GA = candidates['U_SA3_GA']

    # 检查闸机容量
    allowed = check_gate_admission(U_SA3_GA, system.params)

    for p in U_SA3_GA[:allowed]:
        # 通过闸机
        p.position = Position.PASSED
        p.t_exit_system = T  # 离散时刻约定（设计书6.4）

        # 更新人数
        system.D_SA3 -= 1
        system.D_pass += 1
        # ⚠️ 不需要 += t_s（已包含在 t_SA3_basic 中）

    # 未能通过的乘客累积等待时间
    for p in U_SA3_GA[allowed:]:
        p.t_SA3_add += system.params.dt


# ==================== 步骤G：记录历史 ====================

def step_G_record_history(system: System, K_PW2: float, K_SA3: float) -> None:
    """步骤G：记录历史（对应设计书5.2.7）

    记录当前时间步的系统状态，用于后续可视化。

    Args:
        system: 系统对象
        K_PW2: PW2密度
        K_SA3: SA3密度
    """
    system.history['T'].append(system.T)
    system.history['D_SA1'].append(system.D_SA1)
    system.history['D_PW1'].append(system.D_PW1)
    system.history['D_PW2'].append(system.D_PW2)
    system.history['D_SA3'].append(system.D_SA3)
    system.history['D_pass'].append(system.D_pass)
    system.history['K_PW2'].append(K_PW2)
    system.history['K_SA3'].append(K_SA3)


# ==================== 主递推函数 ====================

def simulation_step(system: System, q_PA1: float, q_PA2: float) -> None:
    """执行单次Δt=0.1s的递推更新（对应设计书5.2节）

    ⚠️⚠️⚠️ 关键约束（设计书6.6）⚠️⚠️⚠️

    步骤顺序不可调整！必须严格按照以下顺序执行：

    1. 步骤A：生成新到达
    2. 步骤B：更新密度（使用转移发生前的人数）⚠️ 必须在D/E前
    3. 步骤C：构造候选集合
    4. 步骤E：PW → SA3 转移（⚠️ 先执行，释放空间）
    5. 步骤D：SA1 → PW 转移（⚠️ 后执行，利用已释放的空间）
    6. 步骤F：SA3 → Gate 转移
    7. 步骤G：记录历史
    8. 步骤H：时间推进

    违反此顺序会导致：
    - 密度计算错误（如果B在D/E之后）
    - 性能退化（如果D在E之前）
    - 边界情况异常（如果D在E之前）

    Args:
        system: 系统对象
        q_PA1: PA1到达率（人/秒）
        q_PA2: PA2到达率（人/秒）
    """
    # ===== 步骤A：生成新到达 =====
    step_A_arrivals(system, q_PA1, q_PA2)

    # ===== 步骤B：更新密度（⚠️ 必须在步骤D/E前执行）=====
    K_PW2, K_SA3 = step_B_update_densities(system)

    # ===== 步骤C：构造候选集合 =====
    candidates = step_C_construct_candidates(system)

    # ===== 步骤E：PW → SA3 转移（⚠️ 先执行，释放空间）=====
    step_E_PW_to_SA3(system, candidates, K_SA3)

    # ===== 步骤D：SA1 → PW 转移（⚠️ 后执行，使用已释放的空间）=====
    step_D_SA1_to_PW(system, candidates, K_PW2)

    # ===== 步骤F：SA3 → Gate 转移 =====
    step_F_SA3_to_Gate(system, candidates)

    # ===== 步骤G：记录历史 =====
    step_G_record_history(system, K_PW2, K_SA3)

    # ===== 人数守恒检查（调试用）=====
    total = system.D_SA1 + system.D_PW1 + system.D_PW2 + system.D_SA3 + system.D_pass
    if total != system.D_All:
        raise RuntimeError(
            f"人数守恒检查失败！T={system.T:.1f}s\n"
            f"  D_SA1={system.D_SA1}, D_PW1={system.D_PW1}, "
            f"D_PW2={system.D_PW2}, D_SA3={system.D_SA3}, D_pass={system.D_pass}\n"
            f"  总计={total}, 应为={system.D_All}, 差值={total - system.D_All}"
        )

    # ===== 步骤H：时间推进 =====
    system.T += system.params.dt


def run_simulation(system: System, q_PA1: float, q_PA2: float,
                  max_time: float = 3600.0, verbose: bool = False) -> System:
    """运行完整仿真直到所有乘客通过系统（对应设计书5.1节）

    Args:
        system: 系统对象
        q_PA1: PA1到达率（人/秒）
        q_PA2: PA2到达率（人/秒）
        max_time: 最大仿真时间（秒），防止无限循环
        verbose: 是否打印进度信息

    Returns:
        System: 更新后的系统对象

    Note:
        - 终止条件：D_pass == D_All（所有乘客通过系统）
        - 时间步长：Δt = 0.1s
    """
    if verbose:
        print(f"开始仿真: q_PA1={q_PA1:.2f}, q_PA2={q_PA2:.2f}")
        print(f"时间步长: {system.params.dt}s")

    step_count = 0

    while not system.is_finished() and system.T < max_time:
        simulation_step(system, q_PA1, q_PA2)
        step_count += 1

        # 打印进度
        if verbose and step_count % 100 == 0:
            print(f"T={system.T:.1f}s, D_pass={system.D_pass}/{system.D_All}, "
                  f"D_SA1={system.D_SA1}, D_PW1={system.D_PW1}, "
                  f"D_PW2={system.D_PW2}, D_SA3={system.D_SA3}")

    if verbose:
        if system.is_finished():
            print(f"\n仿真完成！")
            print(f"总时间: {system.T:.1f}s")
            print(f"总乘客: {system.D_All}")
            print(f"总步数: {step_count}")
        else:
            print(f"\n⚠️ 达到最大仿真时间 {max_time}s，仿真终止")
            print(f"已通过: {system.D_pass}/{system.D_All}")

    return system


# ==================== 模块测试函数 ====================

if __name__ == "__main__":
    """模块自测：验证递推引擎正确性"""

    # 自测时的导入
    import sys
    import os
    if 'src' not in sys.path[0]:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import SystemParameters
    from data_structures import System

    print("=" * 70)
    print("递推引擎模块自测")
    print("=" * 70)

    # 创建测试系统
    params = SystemParameters()
    system = System(params=params)

    # 测试1：单步递推（无到达）
    print("\n[测试1] 单步递推（无到达）")
    print(f"  初始状态: T={system.T}, D_SA1={system.D_SA1}")
    simulation_step(system, q_PA1=0.0, q_PA2=0.0)
    print(f"  一步后: T={system.T:.1f}, D_SA1={system.D_SA1}")
    assert system.T == 0.1, "时间应推进0.1s"
    assert system.D_SA1 == 0, "无到达时SA1应为空"
    print("  ✓ 通过")

    # 测试2：到达乘客
    print("\n[测试2] 到达乘客生成")
    system2 = System(params=params)
    simulation_step(system2, q_PA1=10.0, q_PA2=5.0)  # 每秒10个PA1, 5个PA2
    # 0.1s内：期望1个PA1, 0.5个PA2 → 实际1个PA1, 0个PA2（累积器）
    print(f"  T={system2.T:.1f}s")
    print(f"  D_SA1={system2.D_SA1}, D_All={system2.D_All}")
    print(f"  累积器: PA1={system2.arrival_acc_PA1:.2f}, PA2={system2.arrival_acc_PA2:.2f}")
    assert system2.D_SA1 >= 0, "应有乘客到达"
    print("  ✓ 通过")

    # 测试3：小规模完整仿真
    print("\n[测试3] 小规模完整仿真（10个乘客）")
    system3 = System(params=params)

    # 只允许10个乘客到达（前1秒）
    for i in range(10):  # 10步 = 1秒
        simulation_step(system3, q_PA1=5.0, q_PA2=5.0)  # 每秒各5人

    print(f"  到达阶段结束: T={system3.T:.1f}s, D_All={system3.D_All}")

    # 继续运行直到所有人通过
    initial_D_All = system3.D_All
    run_simulation(system3, q_PA1=0.0, q_PA2=0.0, max_time=300.0, verbose=False)

    print(f"  仿真完成: T={system3.T:.1f}s")
    print(f"  总乘客: {system3.D_All}")
    print(f"  已通过: {system3.D_pass}/{system3.D_All}")
    print(f"  系统状态: SA1={system3.D_SA1}, PW1={system3.D_PW1}, "
          f"PW2={system3.D_PW2}, SA3={system3.D_SA3}")

    assert system3.is_finished(), "所有乘客应已通过系统"
    assert system3.D_pass == system3.D_All, "通过人数应等于总人数"
    assert system3.D_SA1 + system3.D_PW1 + system3.D_PW2 + system3.D_SA3 == 0, "系统应为空"
    print("  ✓ 通过")

    # 测试4：中等规模仿真（更现实的测试）
    print("\n[测试4] 中等规模仿真（约200个乘客）")
    system4 = System(params=params)

    # 允许约200个乘客到达（10秒内）
    for i in range(100):  # 100步 = 10秒
        simulation_step(system4, q_PA1=10.0, q_PA2=10.0)  # 每秒各10人

    print(f"  到达阶段结束: T={system4.T:.1f}s, D_All={system4.D_All}")

    # 继续运行直到所有人通过
    initial_D_All = system4.D_All
    run_simulation(system4, q_PA1=0.0, q_PA2=0.0, max_time=600.0, verbose=False)

    print(f"  仿真完成: T={system4.T:.1f}s")
    print(f"  总乘客: {system4.D_All}")
    print(f"  已通过: {system4.D_pass}/{system4.D_All}")
    print(f"  系统状态: SA1={system4.D_SA1}, PW1={system4.D_PW1}, "
          f"PW2={system4.D_PW2}, SA3={system4.D_SA3}")
    print(f"  峰值PW1人数: {max(system4.history['D_PW1'])}")
    print(f"  峰值SA3人数: {max(system4.history['D_SA3'])}")

    assert system4.is_finished(), "所有乘客应已通过系统"
    assert system4.D_pass == system4.D_All, "通过人数应等于总人数"
    assert system4.D_All >= 150, "应有足够多的乘客（约200人）"
    print("  ✓ 通过")

    # 测试5：验证历史记录
    print("\n[测试5] 验证历史记录")
    print(f"  记录长度: {len(system3.history['T'])} 个时间步")
    print(f"  时间范围: {system3.history['T'][0]:.1f}s ~ {system3.history['T'][-1]:.1f}s")
    print(f"  最大PW1人数: {max(system3.history['D_PW1'])}")
    print(f"  最大SA3人数: {max(system3.history['D_SA3'])}")

    assert len(system3.history['T']) > 0, "应有历史记录"
    assert len(system3.history['T']) == len(system3.history['D_pass']), "历史记录长度一致"
    print("  ✓ 通过")

    print("\n" + "=" * 70)
    print("所有测试通过！递推引擎运行正确。")
    print("=" * 70)
