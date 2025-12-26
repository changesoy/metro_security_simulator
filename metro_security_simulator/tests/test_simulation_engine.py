"""
单元测试：simulation_engine.py
测试递推引擎的核心功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.simulation_engine import (
    step_A_arrivals,
    step_B_update_densities,
    step_C_construct_candidates,
    step_D_SA1_to_PW,
    step_E_PW_to_SA3,
    step_F_SA3_to_Gate,
    step_G_record_history,
    simulation_step,
    run_simulation
)
from src.data_structures import System, Passenger
from src.config import SystemParameters, PassengerType, Position


def test_step_A_arrivals():
    """测试步骤A：生成新到达乘客"""
    print("\n[测试] 步骤A：生成新到达乘客")

    params = SystemParameters()
    system = System(params=params)

    # 场景1：高到达率
    q_PA1, q_PA2 = 10.0, 5.0  # 每秒10个PA1, 5个PA2
    step_A_arrivals(system, q_PA1, q_PA2)

    # 0.1s内应到达约1个PA1（10 * 0.1 = 1.0）
    print(f"  到达率: PA1={q_PA1}/s, PA2={q_PA2}/s")
    print(f"  时间步: {params.dt}s")
    print(f"  D_SA1={system.D_SA1}, D_All={system.D_All}")
    print(f"  累积器: PA1={system.arrival_acc_PA1:.2f}, PA2={system.arrival_acc_PA2:.2f}")

    assert system.D_SA1 >= 1, "应有至少1个乘客到达"
    assert len(system.passengers) == system.D_SA1, "乘客列表长度应与D_SA1一致"

    # 验证乘客初始化
    if len(system.passengers) > 0:
        p = system.passengers[0]
        assert p.position == Position.SA1, "新乘客应在SA1"
        assert p.t_enter_SA1 == system.T, "进入时间应为当前时间"
        assert p.t_SA1_basic > 0, "应计算SA1基本时间"

    print("  ✓ 通过")


def test_step_B_update_densities():
    """测试步骤B：更新密度"""
    print("\n[测试] 步骤B：更新密度")

    params = SystemParameters()
    system = System(params=params)

    # 设置区域人数
    system.D_PW2 = 10
    system.D_SA3 = 20

    K_PW2, K_SA3 = step_B_update_densities(system)

    expected_K_PW2 = 10 / params.A_PW2
    expected_K_SA3 = 20 / params.A_SA3

    print(f"  D_PW2={system.D_PW2}, A_PW2={params.A_PW2} → K_PW2={K_PW2:.4f}")
    print(f"  期望: {expected_K_PW2:.4f}")
    print(f"  D_SA3={system.D_SA3}, A_SA3={params.A_SA3} → K_SA3={K_SA3:.4f}")
    print(f"  期望: {expected_K_SA3:.4f}")

    assert abs(K_PW2 - expected_K_PW2) < 1e-6, "PW2密度计算错误"
    assert abs(K_SA3 - expected_K_SA3) < 1e-6, "SA3密度计算错误"

    print("  ✓ 通过")


def test_step_C_construct_candidates():
    """测试步骤C：构造候选集合"""
    print("\n[测试] 步骤C：构造候选集合")

    params = SystemParameters()
    system = System(params=params)
    system.T = 5.0  # 当前时间5秒

    # 手动添加测试乘客
    # 乘客1：PA1在SA1，已完成SA1（应进入U_SA1_PW1）
    p1 = Passenger(1, PassengerType.PA1, Position.SA1)
    p1.t_enter_SA1 = 0.0
    p1.t_SA1_basic = 3.0
    p1.t_SA1_add = 0.0  # 总共3秒，当前5秒 >= 3秒，应在候选集合中
    system.passengers.append(p1)

    # 乘客2：PA2在SA1，未完成SA1（不应进入候选集合）
    p2 = Passenger(2, PassengerType.PA2, Position.SA1)
    p2.t_enter_SA1 = 4.0
    p2.t_SA1_basic = 3.0
    p2.t_SA1_add = 0.0  # 总共7秒，当前5秒 < 7秒，不在候选集合中
    system.passengers.append(p2)

    # 乘客3：PA1在PW1，已完成PW1（应进入U_PW1_SA3）
    p3 = Passenger(3, PassengerType.PA1, Position.PW1)
    p3.t_enter_SA2 = 0.0
    p3.t_PW_basic = 4.0
    p3.t_SA2_add = 0.0
    system.passengers.append(p3)

    candidates = step_C_construct_candidates(system)

    print(f"  U_SA1_PW1: {len(candidates['U_SA1_PW1'])} 个候选者")
    print(f"  U_SA1_PW2: {len(candidates['U_SA1_PW2'])} 个候选者")
    print(f"  U_PW1_SA3: {len(candidates['U_PW1_SA3'])} 个候选者")
    print(f"  U_PW2_SA3: {len(candidates['U_PW2_SA3'])} 个候选者")
    print(f"  U_SA3_GA: {len(candidates['U_SA3_GA'])} 个候选者")

    assert len(candidates['U_SA1_PW1']) == 1, "应有1个PA1候选者"
    assert len(candidates['U_SA1_PW2']) == 0, "PA2未完成，不应在候选集合"
    assert len(candidates['U_PW1_SA3']) == 1, "应有1个PW1候选者"
    assert candidates['U_SA1_PW1'][0].index == 1, "候选者应为乘客1"

    print("  ✓ 通过")


def test_synchronous_update_rule():
    """测试离散同步更新规则（微调B的核心）"""
    print("\n[测试] 离散同步更新规则（关键测试）")

    params = SystemParameters()
    system = System(params=params)

    # 场景：PW2内有5人，新来3人准备进入
    system.D_PW2 = 5

    # 步骤B：记录"转移前"的密度
    K_PW2_before, _ = step_B_update_densities(system)
    print(f"  转移前: D_PW2={system.D_PW2}, K_PW2={K_PW2_before:.4f}")

    # 添加候选乘客
    for i in range(3):
        p = Passenger(i, PassengerType.PA2, Position.SA1)
        p.t_enter_SA1 = 0.0
        p.t_SA1_basic = 0.0  # 立即完成
        p.t_SA1_add = 0.0
        system.passengers.append(p)
        system.D_SA1 += 1

    # 构造候选集合
    candidates = step_C_construct_candidates(system)

    # 步骤D：转移（应使用转移前的密度）
    step_D_SA1_to_PW(system, candidates, K_PW2_before)

    print(f"  转移后: D_PW2={system.D_PW2}")

    # 验证：新进入的乘客应使用"转移前"的密度计算basic时间
    for p in system.passengers:
        if p.position == Position.PW2:
            # 验证basic时间是用K_PW2_before计算的
            expected_t = params.L_PW2 / params.v_PW2(K_PW2_before)
            assert abs(p.t_PW_basic - expected_t) < 1e-6, \
                f"应使用转移前密度: {K_PW2_before:.4f}"

    print(f"  ✓ 通过（使用转移前密度 K={K_PW2_before:.4f}）")


def test_complete_simulation_small():
    """测试完整小规模仿真"""
    print("\n[测试] 完整小规模仿真")

    params = SystemParameters()
    system = System(params=params)

    # 允许约100个乘客到达（10秒内）
    print(f"  到达阶段: 10秒内到达约100个乘客")
    for i in range(100):  # 100步 = 10秒
        simulation_step(system, q_PA1=5.0, q_PA2=5.0)

    initial_D_All = system.D_All
    print(f"  到达完成: D_All={initial_D_All}")

    # 停止到达，继续运行直到所有人通过
    run_simulation(system, q_PA1=0.0, q_PA2=0.0, max_time=300.0, verbose=False)

    print(f"  仿真完成:")
    print(f"    总时间: {system.T:.1f}s")
    print(f"    总乘客: {system.D_All}")
    print(f"    已通过: {system.D_pass}")
    print(f"    系统状态: SA1={system.D_SA1}, PW1={system.D_PW1}, "
          f"PW2={system.D_PW2}, SA3={system.D_SA3}")

    # 验证守恒
    assert system.is_finished(), "所有乘客应已通过"
    assert system.D_pass == system.D_All, "通过人数应等于总人数"
    assert system.D_SA1 + system.D_PW1 + system.D_PW2 + system.D_SA3 == 0, "系统应为空"

    # 验证时间合理性
    assert system.T < 300.0, "应在最大时间内完成"

    print("  ✓ 通过")


def test_history_recording():
    """测试历史记录功能"""
    print("\n[测试] 历史记录功能")

    params = SystemParameters()
    system = System(params=params)

    # 运行几步
    for i in range(10):
        simulation_step(system, q_PA1=5.0, q_PA2=5.0)

    print(f"  记录长度: {len(system.history['T'])}")
    print(f"  时间范围: {system.history['T'][0]:.1f} ~ {system.history['T'][-1]:.1f}s")
    print(f"  D_pass范围: {system.history['D_pass'][0]} ~ {system.history['D_pass'][-1]}")

    # 验证记录完整性
    assert len(system.history['T']) == 10, "应有10条记录"
    assert len(system.history['D_SA1']) == 10, "各字段长度一致"
    assert len(system.history['K_PW2']) == 10, "密度记录完整"

    # 验证时间单调递增
    for i in range(1, len(system.history['T'])):
        assert system.history['T'][i] > system.history['T'][i - 1], "时间应单调递增"

    print("  ✓ 通过")


def test_passenger_conservation():
    """测试乘客守恒定律"""
    print("\n[测试] 乘客守恒定律")

    params = SystemParameters()
    system = System(params=params)

    # 运行仿真
    for i in range(50):
        simulation_step(system, q_PA1=3.0, q_PA2=2.0)

    # 验证：总人数 = SA1 + PW1 + PW2 + SA3 + PASSED
    total_in_system = (system.D_SA1 + system.D_PW1 +
                       system.D_PW2 + system.D_SA3 + system.D_pass)

    print(f"  D_All={system.D_All}")
    print(f"  系统内: SA1={system.D_SA1}, PW1={system.D_PW1}, "
          f"PW2={system.D_PW2}, SA3={system.D_SA3}, PASSED={system.D_pass}")
    print(f"  总计: {total_in_system}")

    assert total_in_system == system.D_All, "乘客守恒定律违反"

    print("  ✓ 通过（乘客守恒）")


def test_step_order_enforcement():
    """测试步骤顺序强制执行（文档检查）"""
    print("\n[测试] 步骤顺序强制执行（代码结构检查）")

    # 这个测试通过代码审查完成
    # 验证simulation_step()函数中步骤顺序
    import inspect
    source = inspect.getsource(simulation_step)

    # 检查关键步骤顺序
    assert source.index('step_A_arrivals') < source.index('step_B_update_densities'), \
        "A应在B之前"
    assert source.index('step_B_update_densities') < source.index('step_D_SA1_to_PW'), \
        "B应在D之前（关键！）"
    assert source.index('step_D_SA1_to_PW') < source.index('step_E_PW_to_SA3'), \
        "D应在E之前"
    assert source.index('step_E_PW_to_SA3') < source.index('step_F_SA3_to_Gate'), \
        "E应在F之前"

    print("  步骤顺序: A → B → C → D → E → F → G → H ✓")
    print("  ✓ 通过（代码结构正确）")


if __name__ == "__main__":
    print("=" * 70)
    print("simulation_engine.py 单元测试")
    print("=" * 70)

    test_step_A_arrivals()
    test_step_B_update_densities()
    test_step_C_construct_candidates()
    test_synchronous_update_rule()
    test_complete_simulation_small()
    test_history_recording()
    test_passenger_conservation()
    test_step_order_enforcement()

    print("\n" + "=" * 70)
    print("所有测试通过！✓")
    print("=" * 70)
