"""
Metro Security Simulator - 主程序入口
地铁安检仿真系统

论文复现：Passenger Queuing Analysis Method of Security Inspection 
          and Ticket-Checking Area of Metro Stations

使用方法：
    python main.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.experiment_runner import load_experiment_config, run_all_experiments, save_results


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Metro Security Simulator")
    print("地铁安检仿真系统 - 论文复现")
    print("="*60)
    
    try:
        # 加载配置
        config = load_experiment_config()
        
        # 运行实验
        results = run_all_experiments(config)
        
        # 保存结果
        save_results(results, config['experiment_groups'], config)
        
        # 打印对比
        print("\n" + "="*60)
        print("与论文Table 5对比")
        print("="*60)
        print("\n论文预期结果：")
        print("  Group1: Access/Egress=83.0s,  PA1=25.5s,  PA2=12.5s")
        print("  Group2: Access/Egress=138.4s, PA1=53.0s,  PA2=11.8s")
        print("  Group3: Access/Egress=197.8s, PA1=82.9s,  PA2=11.7s")
        print("  Group4: Access/Egress=259.2s, PA1=113.5s, PA2=11.7s")
        print("  Group5: Access/Egress=320.6s, PA1=144.3s, PA2=11.7s")
        
        print("\n" + "="*60)
        print("程序执行完成！")
        print("="*60)
        print(f"\n请查看输出目录: outputs")
        print("  - reports/comparison_table.csv: 对比表格")
        print("  - reports/experiment_summary.txt: 详细报告")
        print("  - figures/: 可视化图表")
        print("  - data/: 原始数据")
        
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
