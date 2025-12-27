============================================================
PAPER REPRODUCTION EXPERIMENT OUTPUTS
============================================================

This directory contains the results of experiments reproducing
the paper's analysis of metro security checkpoint congestion.

============================================================
DIRECTORY STRUCTURE
============================================================

figures/
    queue_pw1_continuous.png - PW1 queue, Groups 1-5 (5 colors)
    queue_pw1_discontinuous.png - PW1 queue, Groups 6-10 (5 colors)
    queue_pw1_comparison.png - Blue=continuous, Red=discontinuous
    
    fig4_queue_pw1_bar.png - Bar chart for Group 1 (paper Fig.4)
    fig5_pw2_density_comparison.png - PW2 density (paper Fig.5)
    fig6_sa3_density_boxplot.png - SA3 boxplot (paper Fig.6)
    
    evolution_GroupX.png - Congestion dynamics (4 subplots)
    time_decomp_GroupX.png - Time breakdown (basic vs extra)

data/
    results_summary.csv - Complete results in CSV format
    results_table.txt - Formatted results table

============================================================
EXPERIMENT GROUPS
============================================================

Continuous Arrival (Group 1-5):
    - Uniform arrival rate for 60 seconds
    - Group 1: PA1=1, PA2=5 ped/s
    - Group 2: PA1=2, PA2=4 ped/s
    - Group 3: PA1=3, PA2=3 ped/s
    - Group 4: PA1=4, PA2=2 ped/s
    - Group 5: PA1=5, PA2=1 ped/s

Discontinuous Arrival (Group 6-10):
    - Arrival in 0-25s and 36-70s, gap in 25-36s
    - Same PA1/PA2 rates as Groups 1-5

============================================================
