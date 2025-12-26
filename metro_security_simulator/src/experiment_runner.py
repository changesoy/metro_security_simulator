"""
实验执行器：负责批量运行仿真实验
对应设计书：完整仿真实验流程

功能：
1. 从YAML加载实验配置
2. 批量执行实验
3. 返回结果供报告生成使用
"""

import os
import yaml
from typing import List, Dict

# 条件导入：支持两种运行方式
try:
    from src.config import SystemParameters
    from src.data_structures import System
    from src.simulation_engine import run_simulation, simulation_step
except ModuleNotFoundError:
    from config import SystemParameters
    from data_structures import System
    from simulation_engine import run_simulation, simulation_step


def load_experiment_config(config_path: str = None) -> Dict:
    """从YAML文件加载实验配置

    Args:
        config_path: 配置文件路径，默认为 config/experiments.yaml

    Returns:
        dict: 包含实验组列表和输出设置的字典

    Raises:
        FileNotFoundError: 配置文件不存在
        yaml.YAMLError: YAML格式错误
    """
    # 默认配置路径
    if config_path is None:
        # 从当前文件位置推断项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)  # 上一级目录
        config_path = os.path.join(project_root, 'config', 'experiments.yaml')

    # 检查文件是否存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    # 加载YAML
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 验证必要字段
    if 'experiment_groups' not in config:
        raise ValueError("配置文件缺少 'experiment_groups' 字段")

    if not config['experiment_groups']:
        raise ValueError("实验组列表为空")

    return config


def run_single_experiment(group: Dict, verbose: bool = True) -> System:
    """运行单个实验组

    Args:
        group: 实验组参数字典，包含：
            - name: 实验组名称
            - description: 描述
            - q_PA1: PA1到达率
            - q_PA2: PA2到达率
            - arrival_duration: 到达持续时间
            - max_time: 最大仿真时间
        verbose: 是否显示详细信息

    Returns:
        System: 完成仿真的系统对象
    """
    if verbose:
        print(f"\n{'=' * 70}")
        print(f"运行实验: {group['name']}")
        print(f"描述: {group['description']}")
        print(f"{'=' * 70}")

    # 创建系统
    params = SystemParameters()
    system = System(params=params)

    # 阶段1：到达阶段
    q_PA1 = group['q_PA1']
    q_PA2 = group['q_PA2']
    arrival_duration = group['arrival_duration']
    arrival_steps = int(arrival_duration / params.dt)

    if verbose:
        print(f"\n[阶段1] 乘客到达")
        print(f"  到达率: q_PA1={q_PA1} ped/s, q_PA2={q_PA2} ped/s")
        print(f"  持续时间: {arrival_duration}s ({arrival_steps}步)")

    # 执行到达阶段
    for i in range(arrival_steps):
        simulation_step(system, q_PA1=q_PA1, q_PA2=q_PA2)

        # 每100步显示进度
        if verbose and (i + 1) % 100 == 0:
            print(f"  进度: {i + 1}/{arrival_steps}步, 已到达: {system.D_All}人", end='\r')

    if verbose:
        print(f"\n  到达阶段完成: 共{system.D_All}人到达")

    # 阶段2：疏散阶段（停止到达，让所有人通过）
    if verbose:
        print(f"\n[阶段2] 系统疏散")
        print(f"  停止新到达，运行直到所有人通过...")

    run_simulation(system, q_PA1=0.0, q_PA2=0.0,
                   max_time=group['max_time'], verbose=verbose)

    if verbose:
        print(f"\n[完成] 仿真结束")
        print(f"  总到达: {system.D_All}人")
        print(f"  已通过: {system.D_pass}人")
        print(f"  仿真时间: {system.T:.2f}s")

    return system


def run_all_experiments(config: Dict) -> Dict[str, System]:
    """运行所有实验组

    Args:
        config: 从YAML加载的完整配置

    Returns:
        dict: {group_name: System} 的字典
    """
    groups = config['experiment_groups']

    # 获取输出设置
    output_settings = config.get('output_settings', {})
    verbose = output_settings.get('verbose', True)

    results = {}

    print("\n" + "=" * 70)
    print("Metro Security Simulator - 批量实验")
    print("=" * 70)
    print(f"总实验组数: {len(groups)}")

    # 显示实验组列表
    print("\n实验组列表:")
    for i, g in enumerate(groups, 1):
        q_total = g['q_PA1'] + g['q_PA2']
        print(f"  {i}. {g['name']}: {g['description']} (q={q_total} ped/s)")

    # 批量执行
    for i, group in enumerate(groups, 1):
        print(f"\n{'=' * 70}")
        print(f"进度: [{i}/{len(groups)}]")
        print(f"{'=' * 70}")

        system = run_single_experiment(group, verbose=verbose)
        results[group['name']] = system

    print("\n" + "=" * 70)
    print("所有实验完成！")
    print("=" * 70)

    return results


# ==================== 模块测试函数 ====================

if __name__ == "__main__":
    """模块自测"""
    print("=" * 70)
    print("实验执行器自测")
    print("=" * 70)

    # 测试1：加载配置
    print("\n[测试1] 加载YAML配置")
    try:
        config = load_experiment_config()
        print(f"  ✓ 成功加载配置")
        print(f"  实验组数: {len(config['experiment_groups'])}")
        print(f"  第一组: {config['experiment_groups'][0]['name']}")
    except Exception as e:
        print(f"  ✗ 加载失败: {e}")
        import sys

        sys.exit(1)

    # 测试2：运行单个实验（只运行第一组）
    print("\n[测试2] 运行单个实验（测试模式）")
    test_group = config['experiment_groups'][0].copy()
    test_group['arrival_duration'] = 5.0  # 缩短时间用于测试
    test_group['max_time'] = 100.0

    system = run_single_experiment(test_group, verbose=True)

    print(f"\n  ✓ 实验完成")
    print(f"  到达人数: {system.D_All}")
    print(f"  通过人数: {system.D_pass}")

    print("\n" + "=" * 70)
    print("自测完成！实验执行器工作正常。")
    print("=" * 70)
