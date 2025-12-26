"""
Metro Security Simulator - 主程序入口
地铁安检仿真系统

使用方法：
    python main.py

配置修改：
    编辑 config/experiments.yaml 文件
"""

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入功能模块
from src.experiment_runner import load_experiment_config, run_all_experiments
from src.report_generator import save_results


def main():
    """主函数 - 程序入口"""

    try:
        # 步骤1：加载配置
        print("\n" + "="*70)
        print("Metro Security Simulator")
        print("地铁安检仿真系统")
        print("="*70)

        config = load_experiment_config()

        # 步骤2：运行实验
        results = run_all_experiments(config)

        # 步骤3：生成报告
        save_results(results, config['experiment_groups'], config)

        # 完成
        print("\n" + "="*70)
        print("程序执行完成！")
        print("="*70)

        output_dir = config.get('output_settings', {}).get('output_dir', 'outputs')
        print(f"\n请查看输出目录: {output_dir}")
        print("  - reports/comparison_table.csv: 对比表格")
        print("  - figures/: 所有图表")
        print("  - data/: 原始数据")
        print("  - README.md: 结果说明\n")

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        print("请确保 config/experiments.yaml 文件存在。")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
