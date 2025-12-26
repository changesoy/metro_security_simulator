"""
单元测试：data_structures.py
测试 Passenger 和 System 类
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_structures import Passenger, System
from src.config import PassengerType, Position, SystemParameters


def test_passenger_creation():
    """测试 Passenger 对象创建"""
    print("\n[测试] Passenger 对象创建")

    p1 = Passenger(index=1, ptype=PassengerType.PA1, position=Position.SA1)

    print(f"  创建乘客: {p1}")
    assert p1.index == 1
    assert p1.ptype == PassengerType.PA1
    assert p1.position == Position.SA1
    assert p1.total_time() == 0.0

    # 验证所有时间字段默认为0
    assert p1.t_enter_SA1 == 0.0
    assert p1.t_enter_SA2 == 0.0
    assert p1.t_enter_SA3 == 0.0
    assert p1.t_exit_system == 0.0
    assert p1.t_SA1_basic == 0.0
    assert p1.t_PW_basic == 0.0
    assert p1.t_SA3_basic == 0.0
    assert p1.t_SA1_add == 0.0
    assert p1.t_SA2_add == 0.0
    assert p1.t_SA3_add == 0.0

    print("  ✓ 通过")


def test_passenger_total_time():
    """测试 Passenger.total_time() 计算"""
    print("\n[测试] Passenger.total_time() 计算")

    p = Passenger(index=1, ptype=PassengerType.PA1, position=Position.PASSED)

    # 设置各时间分量
    p.t_SA1_basic = 3.0
    p.t_PW_basic = 15.5
    p.t_SA3_basic = 6.5  # 已含t_s=3.5
    p.t_SA1_add = 1.0
    p.t_SA2_add = 2.0
    p.t_SA3_add = 0.5

    total = p.total_time()
    expected = 3.0 + 15.5 + 6.5 + 1.0 + 2.0 + 0.5  # = 28.5

    print(f"  基本时间: SA1={p.t_SA1_basic}, PW={p.t_PW_basic}, SA3={p.t_SA3_basic}")
    print(f"  附加时间: SA1={p.t_SA1_add}, SA2={p.t_SA2_add}, SA3={p.t_SA3_add}")
    print(f"  总时间: {total:.2f}s (期望: {expected:.2f}s)")

    assert abs(total - expected) < 1e-6, f"总时间计算错误: {total} != {expected}"

    # 验证t_s不需要单独相加（已在t_SA3_basic中）
    print(f"  注意: t_SA3_basic={p.t_SA3_basic}s 已包含 t_s=3.5s")
    print("  ✓ 通过")


def test_system_initialization():
    """测试 System 对象初始化"""
    print("\n[测试] System 对象初始化")

    params = SystemParameters()
    sys = System(params=params)

    print(f"  系统状态: {sys}")

    # 验证初始状态
    assert sys.T == 0.0, "时间初始化错误"
    assert sys.D_pass == 0, "通过人数初始化错误"
    assert sys.D_SA1 == 0, "SA1人数初始化错误"
    assert sys.D_PW1 == 0, "PW1人数初始化错误"
    assert sys.D_PW2 == 0, "PW2人数初始化错误"
    assert sys.D_SA3 == 0, "SA3人数初始化错误"
    assert len(sys.passengers) == 0, "乘客列表初始化错误"
    assert sys.next_passenger_id == 0, "乘客编号生成器初始化错误"

    # 验证历史记录初始化
    assert 'T' in sys.history
    assert 'D_SA1' in sys.history
    assert 'K_PW2' in sys.history
    assert len(sys.history['T']) == 0, "历史记录应为空列表"

    print("  ✓ 通过")


def test_system_passenger_queries():
    """测试 System 乘客查询方法"""
    print("\n[测试] System 乘客查询方法")

    params = SystemParameters()
    sys = System(params=params)

    # 添加测试乘客
    sys.passengers.append(Passenger(1, PassengerType.PA1, Position.SA1))
    sys.passengers.append(Passenger(2, PassengerType.PA2, Position.SA1))
    sys.passengers.append(Passenger(3, PassengerType.PA1, Position.PW1))
    sys.passengers.append(Passenger(4, PassengerType.PA2, Position.SA3))

    # 测试按位置查询
    sa1_passengers = sys.get_passengers_by_position(Position.SA1)
    print(f"  SA1中的乘客: {[p.index for p in sa1_passengers]} (期望: [1, 2])")
    assert len(sa1_passengers) == 2
    assert all(p.position == Position.SA1 for p in sa1_passengers)

    # 测试按类型查询
    pa1_passengers = sys.get_passengers_by_type(PassengerType.PA1)
    print(f"  PA1类型乘客: {[p.index for p in pa1_passengers]} (期望: [1, 3])")
    assert len(pa1_passengers) == 2
    assert all(p.ptype == PassengerType.PA1 for p in pa1_passengers)

    # 测试按编号查询
    p2 = sys.get_passenger_by_index(2)
    assert p2 is not None
    assert p2.index == 2
    assert p2.ptype == PassengerType.PA2
    print(f"  按编号查询: passenger[2] = {p2}")

    # 测试不存在的编号
    p_none = sys.get_passenger_by_index(999)
    assert p_none is None
    print(f"  按编号查询: passenger[999] = None (正确)")

    print("  ✓ 通过")


def test_system_density_calculation():
    """测试 System 密度计算方法"""
    print("\n[测试] System 密度计算")

    params = SystemParameters()
    sys = System(params=params)

    # 设置区域人数
    sys.D_PW2 = 5
    sys.D_SA3 = 10

    # 计算密度
    K_pw2 = sys.current_density_PW2()
    K_sa3 = sys.current_density_SA3()

    # 期望值
    expected_K_pw2 = 5 / params.A_PW2  # 5 / 10.2
    expected_K_sa3 = 10 / params.A_SA3  # 10 / 29.7

    print(f"  PW2: D={sys.D_PW2}, A={params.A_PW2} m² → K={K_pw2:.4f} ped/m²")
    print(f"       期望: {expected_K_pw2:.4f} ped/m²")
    print(f"  SA3: D={sys.D_SA3}, A={params.A_SA3} m² → K={K_sa3:.4f} ped/m²")
    print(f"       期望: {expected_K_sa3:.4f} ped/m²")

    assert abs(K_pw2 - expected_K_pw2) < 1e-6
    assert abs(K_sa3 - expected_K_sa3) < 1e-6

    print("  ✓ 通过")


def test_system_termination_condition():
    """测试 System 终止条件判断"""
    print("\n[测试] System 终止条件判断")

    params = SystemParameters()
    sys = System(params=params)

    # 场景1：未完成
    sys.D_All = 100
    sys.D_pass = 50
    assert sys.is_finished() == False
    print(f"  未完成: D_pass={sys.D_pass} < D_All={sys.D_All} → {sys.is_finished()}")

    # 场景2：刚好完成
    sys.D_pass = 100
    assert sys.is_finished() == True
    print(f"  已完成: D_pass={sys.D_pass} == D_All={sys.D_All} → {sys.is_finished()}")

    # 场景3：超额完成（不应该发生，但需要处理）
    sys.D_pass = 101
    assert sys.is_finished() == True
    print(f"  超额完成: D_pass={sys.D_pass} > D_All={sys.D_All} → {sys.is_finished()}")

    print("  ✓ 通过")


def test_passenger_field_naming():
    """测试字段命名规范（设计书v1.1要求）"""
    print("\n[测试] 字段命名规范")

    p = Passenger(1, PassengerType.PA1, Position.SA1)

    # 验证关键字段存在且命名正确
    assert hasattr(p, 't_enter_SA2'), "缺少t_enter_SA2字段"
    assert hasattr(p, 't_SA2_add'), "缺少t_SA2_add字段"

    # 验证不存在误命名字段
    assert not hasattr(p, 't_enter_PW'), "不应存在t_enter_PW（应为t_enter_SA2）"

    print(f"  ✓ t_enter_SA2 字段存在（进入PW1/PW2时刻）")
    print(f"  ✓ t_SA2_add 字段存在（PW末端等待时间）")
    print("  ✓ 通过")


if __name__ == "__main__":
    print("=" * 60)
    print("data_structures.py 单元测试")
    print("=" * 60)

    test_passenger_creation()
    test_passenger_total_time()
    test_system_initialization()
    test_system_passenger_queries()
    test_system_density_calculation()
    test_system_termination_condition()
    test_passenger_field_naming()

    print("\n" + "=" * 60)
    print("所有测试通过！✓")
    print("=" * 60)
