#!/usr/bin/env python3
"""
步骤顺序修复 - 快速验证脚本

这个脚本会：
1. 检查simulation_engine.py中步骤E是否在步骤D之前
2. 运行简单的功能测试

用法：将此文件放在项目根目录，然后运行：
    python quick_test_step_order.py
"""

import os
import sys

def check_step_order():
    """检查simulation_engine.py中的步骤顺序"""
    print("=" * 70)
    print("步骤顺序检查")
    print("=" * 70)

    # 查找simulation_engine.py - 更智能的路径查找
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)

    possible_paths = [
        # 从项目根目录运行
        os.path.join(current_dir, 'src', 'simulation_engine.py'),
        # 从tests目录运行
        os.path.join(parent_dir, 'src', 'simulation_engine.py'),
        # 简单相对路径
        'src/simulation_engine.py',
        '../src/simulation_engine.py',
        # Windows路径
        'src\\simulation_engine.py',
        '..\\src\\simulation_engine.py'
    ]

    sim_engine_path = None
    for path in possible_paths:
        if os.path.exists(path):
            sim_engine_path = os.path.abspath(path)
            break

    if not sim_engine_path:
        print("❌ 错误：未找到simulation_engine.py文件")
        print("   尝试的路径：")
        for path in possible_paths[:4]:  # 只显示前4个
            print(f"     - {os.path.abspath(path)}")
        print("   请确保在项目根目录或tests目录运行此脚本")
        return False

    print(f"✓ 找到文件：{sim_engine_path}\n")

    # 读取文件内容
    with open(sim_engine_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 查找simulation_step函数中的步骤D和E
    in_simulation_step = False
    step_e_line = None
    step_d_line = None

    for i, line in enumerate(lines, 1):
        if 'def simulation_step' in line:
            in_simulation_step = True
        elif in_simulation_step:
            # 忽略注释行和函数定义
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            # 查找步骤E的调用（不是定义）
            if 'step_E_PW_to_SA3' in line and 'def ' not in line:
                if step_e_line is None:  # 只记录第一次出现
                    step_e_line = i
            # 查找步骤D的调用（不是定义）
            elif 'step_D_SA1_to_PW' in line and 'def ' not in line:
                if step_d_line is None:  # 只记录第一次出现
                    step_d_line = i
            # 遇到下一个函数定义，停止
            elif stripped.startswith('def ') and 'simulation_step' not in line:
                break

    print("步骤位置：")
    if step_e_line:
        print(f"  ✓ 步骤E（PW → SA3）: 第 {step_e_line} 行")
    else:
        print(f"  ✗ 步骤E（PW → SA3）: 未找到")

    if step_d_line:
        print(f"  ✓ 步骤D（SA1 → PW）: 第 {step_d_line} 行")
    else:
        print(f"  ✗ 步骤D（SA1 → PW）: 未找到")

    print()

    # 验证顺序
    if step_e_line and step_d_line:
        if step_e_line < step_d_line:
            print("✅ 正确：步骤E在步骤D之前执行")
            print("   （先让人离开PW，释放空间；再让人进入PW）")
            return True
        else:
            print("❌ 错误：步骤D在步骤E之前执行")
            print("   （这会导致性能退化和边界情况异常）")
            print()
            print("   修复建议：")
            print("   1. 在simulation_step函数中")
            print("   2. 将 step_E_PW_to_SA3(...) 移到 step_D_SA1_to_PW(...) 之前")
            return False
    else:
        print("⚠️  警告：无法找到步骤D或步骤E的调用")
        if not step_e_line:
            print("   未找到：step_E_PW_to_SA3")
        if not step_d_line:
            print("   未找到：step_D_SA1_to_PW")
        return False


def run_simple_test():
    """运行简单的功能测试"""
    print("\n" + "=" * 70)
    print("功能测试")
    print("=" * 70)

    # 尝试导入模块
    try:
        # 智能添加路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)

        # 尝试从项目根目录导入
        if os.path.exists(os.path.join(current_dir, 'src')):
            # 当前目录就是项目根目录
            sys.path.insert(0, current_dir)
        elif os.path.exists(os.path.join(parent_dir, 'src')):
            # 父目录是项目根目录（从tests/运行）
            sys.path.insert(0, parent_dir)

        from src.config import SystemParameters
        from src.data_structures import System
        from src.simulation_engine import simulation_step

        print("✓ 模块导入成功\n")

        # 创建测试系统
        params = SystemParameters()
        system = System(params=params)

        print("[测试1] 运行10步仿真")
        for i in range(10):
            simulation_step(system, q_PA1=5.0, q_PA2=5.0)

        print(f"  T={system.T:.1f}s, 到达人数={system.D_All}, SA1={system.D_SA1}")
        print("  ✓ 通过\n")

        print("[测试2] 人数守恒检查")
        total = system.D_SA1 + system.D_PW1 + system.D_PW2 + system.D_SA3 + system.D_pass
        print(f"  各区域人数和={total}, 总人数={system.D_All}")
        assert total == system.D_All, f"人数不守恒: {total} != {system.D_All}"
        print("  ✓ 通过")

        return True

    except ImportError as e:
        print(f"❌ 导入错误：{e}")
        print()
        print("   可能的原因：")
        print("   1. 不在项目根目录或tests目录运行")
        print("   2. src/目录结构不正确")
        print()
        print("   建议：")
        print("   1. 确保在项目根目录或tests目录运行此脚本")
        print("   2. 确保src/目录包含所有必要的模块")
        print()
        print("   当前目录：", os.getcwd())
        print("   脚本位置：", os.path.dirname(os.path.abspath(__file__)))
        return False
    except Exception as e:
        print(f"❌ 运行错误：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("步骤顺序修复 - 快速验证\n")

    # 1. 检查步骤顺序
    order_ok = check_step_order()

    # 2. 运行功能测试
    test_ok = run_simple_test()

    # 总结
    print("\n" + "=" * 70)
    print("验证总结")
    print("=" * 70)
    print(f"步骤顺序检查：{'✅ 通过' if order_ok else '❌ 失败'}")
    print(f"功能测试：    {'✅ 通过' if test_ok else '❌ 失败'}")

    if order_ok and test_ok:
        print("\n🎉 所有检查通过！步骤顺序修复成功。")
        sys.exit(0)
    else:
        print("\n⚠️  存在问题，请查看上方详细信息。")
        sys.exit(1)
