import yaml
import os

os.chdir(r'C:\Users\chang\PycharmProjects\metro_security_simulator')

with open('config/experiments.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 显示Group5配置
for g in config['experiment_groups']:
    if 'Group5' in g['name']:
        print("Group5配置:")
        for key, value in g.items():
            print(f"  {key}: {value}")
