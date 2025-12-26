"""
报告生成器：负责生成统计报告和可视化结果
对应设计书：第7节输出指标与验证标准

功能：
1. 生成对比表格（CSV）
2. 生成可视化图表（PNG）
3. 保存原始数据
4. 生成结果说明文档
"""

import os
import pandas as pd
import datetime
from typing import Dict, List

# 条件导入：支持两种运行方式
try:
    from src.data_structures import System
    from src.metrics import (
        compute_average_transit_time,
        compute_access_egress_time,
        generate_summary_report,
        extract_time_series,
        extract_passenger_data
    )
    from src.visualization import plot_all_metrics, plot_comparison
except ModuleNotFoundError:
    from data_structures import System
    from metrics import (
        compute_average_transit_time,
        compute_access_egress_time,
        generate_summary_report,
        extract_time_series,
        extract_passenger_data
    )
    from visualization import plot_all_metrics, plot_comparison


def generate_comparison_table(results: Dict[str, System], groups: List[Dict]) -> pd.DataFrame:
    """生成对比表格（对应论文Table 5）

    Args:
        results: 实验结果字典 {group_name: System}
        groups: 实验组参数列表

    Returns:
        pd.DataFrame: 对比表格
    """
    data = []

    for group in groups:
        name = group['name']
        system = results[name]

        # 计算指标
        avg_times = compute_average_transit_time(system)
        T_ae = compute_access_egress_time(system)

        # 峰值统计
        peak_D_PW1 = max(system.history['D_PW1']) if system.history['D_PW1'] else 0
        peak_D_SA3 = max(system.history['D_SA3']) if system.history['D_SA3'] else 0
        peak_K_PW2 = max(system.history['K_PW2']) if system.history['K_PW2'] else 0
        peak_K_SA3 = max(system.history['K_SA3']) if system.history['K_SA3'] else 0

        data.append({
            'Group': name,
            'Description': group['description'],
            'q_total (ped/s)': group['q_PA1'] + group['q_PA2'],
            'q_PA1 (ped/s)': group['q_PA1'],
            'q_PA2 (ped/s)': group['q_PA2'],
            'n_PA1': avg_times['n_PA1'],
            'n_PA2': avg_times['n_PA2'],
            'n_total': avg_times['n_PA1'] + avg_times['n_PA2'],
            't_avg_PA1 (s)': round(avg_times['t_avg_PA1'], 2),
            't_avg_PA2 (s)': round(avg_times['t_avg_PA2'], 2),
            'T_access_egress (s)': round(T_ae, 2),
            'peak_D_PW1': peak_D_PW1,
            'peak_D_SA3': peak_D_SA3,
            'peak_K_PW2 (ped/m²)': round(peak_K_PW2, 4),
            'peak_K_SA3 (ped/m²)': round(peak_K_SA3, 4)
        })

    df = pd.DataFrame(data)
    return df


def save_results(results: Dict[str, System], groups: List[Dict],
                 config: Dict, output_dir: str = None) -> None:
    """保存所有结果

    Args:
        results: 实验结果字典
        groups: 实验组参数列表
        config: 完整配置字典（含output_settings）
        output_dir: 输出目录（可选，优先使用配置文件中的设置）
    """
    # 获取输出设置
    output_settings = config.get('output_settings', {})

    # 确定输出目录
    if output_dir is None:
        output_dir = output_settings.get('output_dir', 'outputs')

    generate_figures = output_settings.get('generate_figures', True)
    save_raw_data = output_settings.get('save_raw_data', True)

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "figures"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "data"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "reports"), exist_ok=True)

    print(f"\n{'=' * 70}")
    print(f"保存结果到: {output_dir}")
    print(f"{'=' * 70}")

    # 1. 保存对比表格
    print("\n[1/4] 生成对比表格...")
    comparison_table = generate_comparison_table(results, groups)
    comparison_table.to_csv(os.path.join(output_dir, "reports", "comparison_table.csv"),
                            index=False, encoding='utf-8-sig')
    print(f"  ✓ 保存到: reports/comparison_table.csv")

    # 打印到控制台
    print("\n" + "=" * 70)
    print("实验对比表格")
    print("=" * 70)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(comparison_table.to_string(index=False))
    print("=" * 70)

    # 2. 保存各组详细报告
    print("\n[2/4] 生成各组详细报告...")
    for group in groups:
        name = group['name']
        system = results[name]

        # 统计报告
        report = generate_summary_report(system)
        report_df = pd.DataFrame([report])
        report_df.to_csv(os.path.join(output_dir, "reports", f"{name}_report.csv"),
                         index=False, encoding='utf-8-sig')

        # 原始数据（可选）
        if save_raw_data:
            # 时间序列数据
            ts_data = extract_time_series(system)
            ts_data.to_csv(os.path.join(output_dir, "data", f"{name}_timeseries.csv"),
                           index=False, encoding='utf-8-sig')

            # 乘客数据
            pax_data = extract_passenger_data(system)
            pax_data.to_csv(os.path.join(output_dir, "data", f"{name}_passengers.csv"),
                            index=False, encoding='utf-8-sig')

    print(f"  ✓ 保存了 {len(groups)} 个组的详细报告")
    if save_raw_data:
        print(f"  ✓ 保存了原始数据（时间序列和乘客数据）")

    # 3. 生成可视化图表
    if generate_figures:
        print("\n[3/4] 生成可视化图表...")
        figures_dir = os.path.join(output_dir, "figures")

        # 各组单独的图表
        for group in groups:
            name = group['name']
            system = results[name]
            plot_all_metrics(system, group_name=name, save_dir=figures_dir, show=False)

        # 对比图表
        systems_list = [results[g['name']] for g in groups]
        names_list = [g['name'] for g in groups]

        plot_comparison(systems_list, names_list, metric='D_PW1',
                        save_path=os.path.join(figures_dir, 'comparison_PW1_queue.png'),
                        show=False)

        plot_comparison(systems_list, names_list, metric='K_SA3',
                        save_path=os.path.join(figures_dir, 'comparison_SA3_density.png'),
                        show=False)

        plot_comparison(systems_list, names_list, metric='D_pass',
                        save_path=os.path.join(figures_dir, 'comparison_passed.png'),
                        show=False)

        print(f"  ✓ 保存了 {len(groups) * 3 + 3} 张图表")
    else:
        print("\n[3/4] 跳过图表生成（配置中禁用）")

    # 4. 生成README
    print("\n[4/4] 生成结果说明...")
    generate_readme(output_dir, groups, config)
    print(f"  ✓ 保存结果说明文件: README.md")

    print("\n" + "=" * 70)
    print("所有结果已保存！")
    print("=" * 70)


def generate_readme(output_dir: str, groups: List[Dict], config: Dict) -> None:
    """生成README说明文档

    Args:
        output_dir: 输出目录
        groups: 实验组列表
        config: 完整配置
    """
    output_settings = config.get('output_settings', {})
    save_raw_data = output_settings.get('save_raw_data', True)
    generate_figures = output_settings.get('generate_figures', True)

    readme_content = f"""# Metro Security Simulator - 实验结果

## 实验概述

- **实验组数**: {len(groups)}
- **生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **输出目录**: `{output_dir}`

## 实验组列表

"""

    for i, group in enumerate(groups, 1):
        q_total = group['q_PA1'] + group['q_PA2']
        readme_content += f"{i}. **{group['name']}**: {group['description']} (q={q_total} ped/s)\n"

    readme_content += f"""

## 文件结构

```
{os.path.basename(output_dir)}/
├── reports/
│   ├── comparison_table.csv          # 📊 所有组对比表格（关键）
│   └── Group*_report.csv              # 📋 各组详细统计报告
"""

    if save_raw_data:
        readme_content += """├── data/
│   ├── Group*_timeseries.csv          # 📈 时间序列数据（密度、人数变化）
│   └── Group*_passengers.csv          # 👥 乘客详细数据（每个乘客的时间记录）
"""

    if generate_figures:
        readme_content += """├── figures/
│   ├── Group*_PW1_queue.png           # 📉 PW1排队长度曲线
│   ├── Group*_PW2_density.png         # 📉 PW2密度曲线
│   ├── Group*_SA3_density.png         # 📉 SA3密度曲线
│   ├── comparison_PW1_queue.png       # 📊 多组对比：PW1排队
│   ├── comparison_SA3_density.png     # 📊 多组对比：SA3密度
│   └── comparison_passed.png          # 📊 多组对比：通过人数
"""

    readme_content += """└── README.md                           # 📄 本文件
```

## 主要指标说明

### 核心指标
- **t_avg_PA1/PA2**: 平均通行时间（秒）- 乘客从进入SA1到通过闸机的平均时间
- **T_access_egress**: 系统总通过时间（秒）- 最后一名乘客离开系统的时刻
- **n_PA1/PA2**: 通过人数 - 各类型乘客的总数

### 峰值指标
- **peak_D_PW1**: PW1峰值排队人数 - PW1区域的最大人数（反映安检瓶颈）
- **peak_D_SA3**: SA3峰值排队人数 - SA3区域的最大人数
- **peak_K_PW2**: PW2峰值密度（ped/m²）- PW2区域的最大密度
- **peak_K_SA3**: SA3峰值密度（ped/m²）- SA3区域的最大密度

## 使用建议

### 1. 快速查看结果
打开 `reports/comparison_table.csv` 查看所有实验组的对比数据。

### 2. 深度分析
"""

    if generate_figures:
        readme_content += """- 查看 `figures/comparison_*.png` 了解不同负载下的系统动态
- 查看 `figures/Group*_*.png` 了解单个实验组的详细演化过程
"""

    if save_raw_data:
        readme_content += """- 使用 `data/*_timeseries.csv` 进行自定义时间序列分析
- 使用 `data/*_passengers.csv` 分析个体乘客的通行特征
"""

    readme_content += """
### 3. 与论文对比
将 `reports/comparison_table.csv` 中的数据与论文 Table 5 对比，验证仿真准确性。

## 修改实验参数

编辑 `config/experiments.yaml` 文件，然后重新运行 `python main.py` 即可。

## 技术支持

- 查看项目文档：`docs/`
- 查看源代码：`src/`
- 运行测试：`python -m pytest tests/`
"""

    with open(os.path.join(output_dir, "README.md"), 'w', encoding='utf-8') as f:
        f.write(readme_content)


# ==================== 模块测试函数 ====================

if __name__ == "__main__":
    """模块自测"""
    print("=" * 70)
    print("报告生成器自测")
    print("=" * 70)

    print("\n模块功能正常，实际测试需要完整的实验结果。")
    print("请运行 main.py 进行完整测试。")

    print("\n" + "=" * 70)
    print("自测完成！")
    print("=" * 70)
