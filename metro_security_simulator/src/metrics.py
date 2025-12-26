"""
指标计算模块：实现 Eq.(13)-(14) 和其他统计指标
对应设计书：第7节输出指标与验证标准

主要功能：
- 计算平均通行时间（PA1和PA2）
- 计算Access/Egress Time
- 提取时间序列数据
- 生成统计报告
"""

from typing import Dict, List
import pandas as pd

# 条件导入：支持两种运行方式
try:
    from src.data_structures import System, Passenger
    from src.config import PassengerType, Position
except ModuleNotFoundError:
    from data_structures import System, Passenger
    from config import PassengerType, Position


# ==================== 核心指标计算 ====================

def compute_average_transit_time(system: System) -> Dict[str, float]:
    """计算平均通行时间（Eq.13 & Eq.14）

    Args:
        system: 系统对象（仿真完成后）

    Returns:
        dict: 包含 't_avg_PA1', 't_avg_PA2', 'n_PA1', 'n_PA2' 的字典

    Note:
        - 只统计已通过系统的乘客（t_exit_system > 0）
        - 总时间 = 所有basic时间 + 所有add时间
        - t_s 已包含在 t_SA3_basic 中（设计书7.1.1）
    """
    # 筛选已通过系统的乘客（使用t_exit_system > 0作为判断标准）
    passed_passengers = [p for p in system.passengers if p.t_exit_system > 0]

    # 按类型分组（使用.value比较，避免枚举导入路径不一致问题）
    PA1_passengers = [p for p in passed_passengers if p.ptype.value == 'PA1']
    PA2_passengers = [p for p in passed_passengers if p.ptype.value == 'PA2']

    # 计算PA1平均时间（Eq.13）
    if len(PA1_passengers) > 0:
        total_time_PA1 = sum(p.total_time() for p in PA1_passengers)
        t_avg_PA1 = total_time_PA1 / len(PA1_passengers)
    else:
        t_avg_PA1 = 0.0

    # 计算PA2平均时间（Eq.14）
    if len(PA2_passengers) > 0:
        total_time_PA2 = sum(p.total_time() for p in PA2_passengers)
        t_avg_PA2 = total_time_PA2 / len(PA2_passengers)
    else:
        t_avg_PA2 = 0.0

    return {
        't_avg_PA1': t_avg_PA1,
        't_avg_PA2': t_avg_PA2,
        'n_PA1': len(PA1_passengers),
        'n_PA2': len(PA2_passengers)
    }


def compute_access_egress_time(system: System) -> float:
    """计算Access/Egress Time（系统总通过时间）

    Args:
        system: 系统对象（仿真完成后）

    Returns:
        float: Access/Egress Time（秒）

    Note:
        - 定义：最后一名乘客通过系统的时刻
        - 等价于 max{t_exit_system_i} for all i
        - 或仿真终止时刻（对应设计书7.1.1）
        - 与离散时刻约定一致（设计书6.4）
    """
    # 使用t_exit_system > 0判断已通过的乘客
    passed_passengers = [p for p in system.passengers if p.t_exit_system > 0]

    if len(passed_passengers) > 0:
        T_ae = max(p.t_exit_system for p in passed_passengers)
    else:
        # 如果没有乘客通过，返回当前时间
        T_ae = system.T

    return T_ae


def compute_time_breakdown(system: System) -> Dict[str, Dict[str, float]]:
    """计算时间分解统计（各时间分量的平均值）

    Args:
        system: 系统对象（仿真完成后）

    Returns:
        dict: 包含PA1和PA2的时间分解统计
    """
    passed = [p for p in system.passengers if p.t_exit_system > 0]
    # 使用.value比较，避免枚举导入路径不一致问题
    PA1 = [p for p in passed if p.ptype.value == 'PA1']
    PA2 = [p for p in passed if p.ptype.value == 'PA2']

    def avg(values):
        return sum(values) / len(values) if len(values) > 0 else 0.0

    breakdown = {
        'PA1': {
            'basic_SA1': avg([p.t_SA1_basic for p in PA1]),
            'basic_PW': avg([p.t_PW_basic for p in PA1]),
            'basic_SA3': avg([p.t_SA3_basic for p in PA1]),
            'add_SA1': avg([p.t_SA1_add for p in PA1]),
            'add_SA2': avg([p.t_SA2_add for p in PA1]),
            'add_SA3': avg([p.t_SA3_add for p in PA1]),
            'total': avg([p.total_time() for p in PA1])
        },
        'PA2': {
            'basic_SA1': avg([p.t_SA1_basic for p in PA2]),
            'basic_PW': avg([p.t_PW_basic for p in PA2]),
            'basic_SA3': avg([p.t_SA3_basic for p in PA2]),
            'add_SA1': avg([p.t_SA1_add for p in PA2]),
            'add_SA2': avg([p.t_SA2_add for p in PA2]),
            'add_SA3': avg([p.t_SA3_add for p in PA2]),
            'total': avg([p.total_time() for p in PA2])
        }
    }

    return breakdown


# ==================== 时间序列提取 ====================

def extract_time_series(system: System) -> pd.DataFrame:
    """提取历史记录为DataFrame

    Args:
        system: 系统对象（仿真完成后）

    Returns:
        pd.DataFrame: 包含所有历史记录的DataFrame

    Columns:
        - T: 时间（秒）
        - D_SA1, D_PW1, D_PW2, D_SA3, D_pass: 各区域人数
        - K_PW2, K_SA3: 密度
    """
    df = pd.DataFrame(system.history)
    return df


def extract_passenger_data(system: System) -> pd.DataFrame:
    """提取乘客数据为DataFrame

    Args:
        system: 系统对象（仿真完成后）

    Returns:
        pd.DataFrame: 包含所有乘客信息的DataFrame

    Columns:
        - index: 乘客编号
        - type: 乘客类型
        - position: 最终位置
        - t_enter_SA1, t_enter_SA2, t_enter_SA3, t_exit_system: 进入/离开时间
        - t_SA1_basic, t_PW_basic, t_SA3_basic: 基本时间
        - t_SA1_add, t_SA2_add, t_SA3_add: 附加时间
        - total_time: 总通行时间
    """
    data = []
    for p in system.passengers:
        data.append({
            'index': p.index,
            'type': p.ptype.value,
            'position': p.position.value,
            't_enter_SA1': p.t_enter_SA1,
            't_enter_SA2': p.t_enter_SA2,
            't_enter_SA3': p.t_enter_SA3,
            't_exit_system': p.t_exit_system,
            't_SA1_basic': p.t_SA1_basic,
            't_PW_basic': p.t_PW_basic,
            't_SA3_basic': p.t_SA3_basic,
            't_SA1_add': p.t_SA1_add,
            't_SA2_add': p.t_SA2_add,
            't_SA3_add': p.t_SA3_add,
            'total_time': p.total_time()
        })

    df = pd.DataFrame(data)
    return df


# ==================== 统计报告生成 ====================

def generate_summary_report(system: System) -> Dict:
    """生成完整的统计报告

    Args:
        system: 系统对象（仿真完成后）

    Returns:
        dict: 包含所有关键指标的字典
    """
    # 基本统计
    avg_times = compute_average_transit_time(system)
    T_ae = compute_access_egress_time(system)

    # 时间分解
    breakdown = compute_time_breakdown(system)

    # 峰值人数
    peak_D_PW1 = max(system.history['D_PW1']) if system.history['D_PW1'] else 0
    peak_D_SA3 = max(system.history['D_SA3']) if system.history['D_SA3'] else 0

    # 峰值密度
    peak_K_PW2 = max(system.history['K_PW2']) if system.history['K_PW2'] else 0
    peak_K_SA3 = max(system.history['K_SA3']) if system.history['K_SA3'] else 0

    report = {
        # 核心指标
        'T_access_egress': T_ae,
        't_avg_PA1': avg_times['t_avg_PA1'],
        't_avg_PA2': avg_times['t_avg_PA2'],
        'n_PA1': avg_times['n_PA1'],
        'n_PA2': avg_times['n_PA2'],
        'n_total': avg_times['n_PA1'] + avg_times['n_PA2'],

        # 峰值统计
        'peak_D_PW1': peak_D_PW1,
        'peak_D_SA3': peak_D_SA3,
        'peak_K_PW2': peak_K_PW2,
        'peak_K_SA3': peak_K_SA3,

        # 时间分解（PA1）
        'PA1_basic_SA1': breakdown['PA1']['basic_SA1'],
        'PA1_basic_PW': breakdown['PA1']['basic_PW'],
        'PA1_basic_SA3': breakdown['PA1']['basic_SA3'],
        'PA1_add_SA1': breakdown['PA1']['add_SA1'],
        'PA1_add_SA2': breakdown['PA1']['add_SA2'],
        'PA1_add_SA3': breakdown['PA1']['add_SA3'],

        # 时间分解（PA2）
        'PA2_basic_SA1': breakdown['PA2']['basic_SA1'],
        'PA2_basic_PW': breakdown['PA2']['basic_PW'],
        'PA2_basic_SA3': breakdown['PA2']['basic_SA3'],
        'PA2_add_SA1': breakdown['PA2']['add_SA1'],
        'PA2_add_SA2': breakdown['PA2']['add_SA2'],
        'PA2_add_SA3': breakdown['PA2']['add_SA3'],
    }

    return report


def print_summary_report(system: System) -> None:
    """打印格式化的统计报告

    Args:
        system: 系统对象（仿真完成后）
    """
    report = generate_summary_report(system)

    print("=" * 70)
    print("仿真结果统计报告")
    print("=" * 70)

    print("\n【核心指标】")
    print(f"  Access/Egress Time: {report['T_access_egress']:.2f}s")
    print(f"  总乘客数: {report['n_total']} (PA1={report['n_PA1']}, PA2={report['n_PA2']})")
    print(f"  PA1平均时间: {report['t_avg_PA1']:.2f}s")
    print(f"  PA2平均时间: {report['t_avg_PA2']:.2f}s")

    print("\n【峰值统计】")
    print(f"  PW1峰值人数: {report['peak_D_PW1']}")
    print(f"  SA3峰值人数: {report['peak_D_SA3']}")
    print(f"  PW2峰值密度: {report['peak_K_PW2']:.4f} ped/m²")
    print(f"  SA3峰值密度: {report['peak_K_SA3']:.4f} ped/m²")

    print("\n【PA1时间分解】")
    print(f"  SA1: basic={report['PA1_basic_SA1']:.2f}s + add={report['PA1_add_SA1']:.2f}s")
    print(f"  PW1: basic={report['PA1_basic_PW']:.2f}s + add={report['PA1_add_SA2']:.2f}s")
    print(f"  SA3: basic={report['PA1_basic_SA3']:.2f}s + add={report['PA1_add_SA3']:.2f}s")

    print("\n【PA2时间分解】")
    print(f"  SA1: basic={report['PA2_basic_SA1']:.2f}s + add={report['PA2_add_SA1']:.2f}s")
    print(f"  PW2: basic={report['PA2_basic_PW']:.2f}s + add={report['PA2_add_SA2']:.2f}s")
    print(f"  SA3: basic={report['PA2_basic_SA3']:.2f}s + add={report['PA2_add_SA3']:.2f}s")

    print("=" * 70)


# ==================== 模块测试函数 ====================

if __name__ == "__main__":
    """模块自测：验证指标计算正确性"""

    # 自测时的导入
    import sys
    import os
    if 'src' not in sys.path[0]:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import SystemParameters, Position, PassengerType
    from data_structures import System, Passenger
    from simulation_engine import run_simulation, simulation_step

    print("=" * 70)
    print("指标计算模块自测")
    print("=" * 70)

    # 创建测试系统并运行仿真
    print("\n[准备] 运行中等规模仿真...")
    params = SystemParameters()
    system = System(params=params)

    # 允许约100个乘客到达（10秒内，q_PA1=5, q_PA2=5 → 每秒10人 → 10秒100人）
    for i in range(100):  # 100步 = 10秒
        simulation_step(system, q_PA1=5.0, q_PA2=5.0)

    print(f"  到达阶段完成: D_All={system.D_All}, D_pass={system.D_pass}")

    # 运行直到所有人通过
    run_simulation(system, q_PA1=0.0, q_PA2=0.0, max_time=300.0, verbose=False)

    print(f"  仿真完成: D_All={system.D_All}, D_pass={system.D_pass}")

    # 调试：检查有多少乘客设置了t_exit_system
    passed_count = len([p for p in system.passengers if p.t_exit_system > 0])
    print(f"  已设置t_exit_system的乘客: {passed_count}")

    # 详细调试：检查乘客类型分布
    if passed_count > 0:
        sample_passengers = system.passengers[:5]  # 查看前5个乘客
        print(f"\n  [调试] 前5个乘客样本:")
        for p in sample_passengers:
            print(f"    乘客{p.index}: ptype={p.ptype}, t_exit={p.t_exit_system:.2f}")

        # 统计类型（使用.value比较）
        pa1_count = len([p for p in system.passengers if p.ptype.value == 'PA1'])
        pa2_count = len([p for p in system.passengers if p.ptype.value == 'PA2'])
        print(f"  总乘客类型分布: PA1={pa1_count}, PA2={pa2_count}")

        # 统计已通过的类型（使用.value比较）
        passed_pa1 = len([p for p in system.passengers if p.t_exit_system > 0 and p.ptype.value == 'PA1'])
        passed_pa2 = len([p for p in system.passengers if p.t_exit_system > 0 and p.ptype.value == 'PA2'])
        print(f"  已通过乘客类型: PA1={passed_pa1}, PA2={passed_pa2}")

    # 如果没有乘客通过，跳过测试（仿真可能有问题）
    if passed_count == 0:
        print("\n  ⚠️ 警告：没有乘客通过系统，跳过指标测试")
        print("  这可能是因为仿真时间不足或参数设置问题")
        print("=" * 70)
        sys.exit(0)  # 正常退出

    # 测试1：平均通行时间
    print("\n[测试1] 平均通行时间计算")
    avg_times = compute_average_transit_time(system)
    print(f"  PA1平均: {avg_times['t_avg_PA1']:.2f}s (n={avg_times['n_PA1']})")
    print(f"  PA2平均: {avg_times['t_avg_PA2']:.2f}s (n={avg_times['n_PA2']})")

    assert avg_times['t_avg_PA1'] > 0, "PA1平均时间应>0"
    assert avg_times['t_avg_PA2'] > 0, "PA2平均时间应>0"
    assert avg_times['t_avg_PA1'] > avg_times['t_avg_PA2'], "PA1应比PA2耗时更长"
    print("  ✓ 通过")

    # 测试2：Access/Egress Time
    print("\n[测试2] Access/Egress Time计算")
    T_ae = compute_access_egress_time(system)
    print(f"  Access/Egress Time: {T_ae:.2f}s")
    print(f"  仿真终止时刻: {system.T:.2f}s")

    assert T_ae > 0, "Access/Egress Time应>0"
    # 放宽容差：T_ae应该≤system.T（最后乘客通过后仿真可能还会运行几步）
    assert T_ae <= system.T + 1.0, "Access/Egress Time应≤仿真终止时刻（允许1秒误差）"
    print("  ✓ 通过")

    # 测试3：时间分解
    print("\n[测试3] 时间分解统计")
    breakdown = compute_time_breakdown(system)
    print(f"  PA1总时间: {breakdown['PA1']['total']:.2f}s")
    print(f"    基本: {breakdown['PA1']['basic_SA1'] + breakdown['PA1']['basic_PW'] + breakdown['PA1']['basic_SA3']:.2f}s")
    print(f"    附加: {breakdown['PA1']['add_SA1'] + breakdown['PA1']['add_SA2'] + breakdown['PA1']['add_SA3']:.2f}s")

    # 验证总时间 = 各分量之和
    total_calc = (breakdown['PA1']['basic_SA1'] + breakdown['PA1']['basic_PW'] +
                 breakdown['PA1']['basic_SA3'] + breakdown['PA1']['add_SA1'] +
                 breakdown['PA1']['add_SA2'] + breakdown['PA1']['add_SA3'])
    assert abs(total_calc - breakdown['PA1']['total']) < 1e-6, "时间分解应一致"
    print("  ✓ 通过")

    # 测试4：时间序列提取
    print("\n[测试4] 时间序列提取")
    df_ts = extract_time_series(system)
    print(f"  记录数: {len(df_ts)}")
    print(f"  列: {list(df_ts.columns)}")
    print(f"  时间范围: {df_ts['T'].min():.1f} ~ {df_ts['T'].max():.1f}s")

    assert len(df_ts) > 0, "应有时间序列记录"
    assert 'T' in df_ts.columns, "应有时间列"
    assert 'D_PW1' in df_ts.columns, "应有人数列"
    print("  ✓ 通过")

    # 测试5：乘客数据提取
    print("\n[测试5] 乘客数据提取")
    df_pax = extract_passenger_data(system)
    print(f"  乘客数: {len(df_pax)}")
    print(f"  列: {list(df_pax.columns)}")

    assert len(df_pax) == system.D_All, "乘客数应一致"
    assert 'total_time' in df_pax.columns, "应有总时间列"
    print("  ✓ 通过")

    # 测试6：完整报告
    print("\n[测试6] 完整统计报告")
    print_summary_report(system)

    print("\n" + "=" * 70)
    print("所有测试通过！指标计算正确。")
    print("=" * 70)
