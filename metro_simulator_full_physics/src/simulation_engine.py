"""
仿真引擎模块
严格实现论文 Figure 3 流程图

核心原则：
1. 时间步长固定为0.1s
2. 同一时间步内使用"步开始时的状态"进行所有判断
3. 按"上游→下游"顺序处理转移（SA1→PW→SA3→Gate）
4. 仅处理"离开时间==T"的乘客
5. 不能转移的乘客：附加时间+0.1s，离开时间同步+0.1s
"""

from typing import List, Tuple
from src.config import PassengerType, Position, SystemParameters
from src.data_structures import Passenger, SystemState
from src.transit_time import (
    compute_t_SA1_basic,
    compute_t_PW1_basic,
    compute_t_PW2_basic,
    compute_t_SA3_basic
)
from src.admission_control import (
    check_PW1_admission,
    check_PW2_admission,
    check_SA3_admission,
    check_gate_admission
)


def generate_arrivals(state: SystemState, q_PA1: float, q_PA2: float) -> None:
    """生成新到达乘客
    
    使用累积器方法处理浮点到达率，采用Strategy 1交替编号。
    
    Args:
        state: 系统状态
        q_PA1: PA1到达率 (ped/s)
        q_PA2: PA2到达率 (ped/s)
    """
    params = state.params
    
    # 累积到达人数
    state.arrival_acc_PA1 += q_PA1 * params.dt
    state.arrival_acc_PA2 += q_PA2 * params.dt
    
    # 提取整数部分
    n_PA1 = int(state.arrival_acc_PA1)
    n_PA2 = int(state.arrival_acc_PA2)
    
    # 扣除已生成的
    state.arrival_acc_PA1 -= n_PA1
    state.arrival_acc_PA2 -= n_PA2
    
    # Strategy 1：交替编号
    # 例如：3个PA1 + 2个PA2 → [PA1, PA2, PA1, PA2, PA1]
    arrivals = []
    for i in range(max(n_PA1, n_PA2)):
        if i < n_PA1:
            arrivals.append(PassengerType.PA1)
        if i < n_PA2:
            arrivals.append(PassengerType.PA2)
    
    # 创建乘客对象
    for ptype in arrivals:
        p = Passenger(
            index=state.next_passenger_id,
            ptype=ptype,
            position=Position.SA1
        )
        
        # 设置进入时间和基本时间
        p.t_enter_SA1 = state.T
        p.t_SA1_basic = compute_t_SA1_basic(p, params)
        p.t_SA1_add = 0.0
        
        # 设置预计离开时刻
        p.t_leave_current = p.t_enter_SA1 + p.t_SA1_basic
        
        state.passengers.append(p)
        state.next_passenger_id += 1


def get_candidates_SA1_to_PW(state: SystemState) -> Tuple[List[Passenger], List[Passenger]]:
    """获取SA1中准备转移到PW的乘客
    
    筛选条件：
    - 位置在SA1
    - 预计离开时刻 <= 当前时刻T（已到达离开时间点）
    
    Returns:
        (PA1候选列表, PA2候选列表)，均按index排序
    """
    eps = 1e-6
    T = state.T
    
    candidates_PA1 = []
    candidates_PA2 = []
    
    for p in state.passengers:
        if p.position == Position.SA1:
            # 使用 <= 判断：离开时刻已到或已过
            if p.t_leave_current <= T + eps:
                if p.ptype == PassengerType.PA1:
                    candidates_PA1.append(p)
                else:
                    candidates_PA2.append(p)
    
    # 按index排序（先编号先优先）
    candidates_PA1.sort(key=lambda x: x.index)
    candidates_PA2.sort(key=lambda x: x.index)
    
    return candidates_PA1, candidates_PA2


def get_candidates_PW_to_SA3(state: SystemState) -> List[Passenger]:
    """获取PW中准备转移到SA3的乘客
    
    筛选条件：
    - 位置在PW1或PW2
    - 预计离开时刻 <= 当前时刻T
    
    Returns:
        候选列表，按index排序
    """
    eps = 1e-6
    T = state.T
    
    candidates = []
    for p in state.passengers:
        if p.position in (Position.PW1, Position.PW2):
            if p.t_leave_current <= T + eps:
                candidates.append(p)
    
    candidates.sort(key=lambda x: x.index)
    return candidates


def get_candidates_SA3_to_gate(state: SystemState) -> List[Passenger]:
    """获取SA3中准备转移到闸机的乘客
    
    筛选条件：
    - 位置在SA3
    - 预计离开时刻 <= 当前时刻T
    
    Returns:
        候选列表，按index排序
    """
    eps = 1e-6
    T = state.T
    
    candidates = []
    for p in state.passengers:
        if p.position == Position.SA3:
            if p.t_leave_current <= T + eps:
                candidates.append(p)
    
    candidates.sort(key=lambda x: x.index)
    return candidates


def simulation_step(state: SystemState, q_PA1: float = 0.0, q_PA2: float = 0.0) -> None:
    """执行一个仿真步骤
    
    严格按照Figure 3流程：
    1. 生成新到达乘客
    2. 获取当前状态快照（用于所有判断）
    3. 按上游→下游顺序处理转移
    4. 记录历史
    5. 时间推进
    
    Args:
        state: 系统状态
        q_PA1: PA1到达率 (ped/s)
        q_PA2: PA2到达率 (ped/s)
    """
    params = state.params
    dt = params.dt
    
    # ========== Step 1: 生成新到达乘客 ==========
    generate_arrivals(state, q_PA1, q_PA2)
    
    # ========== Step 2: 获取状态快照（时间步开始时） ==========
    D_PW1 = state.get_D_PW1()
    D_PW2 = state.get_D_PW2()
    D_SA3 = state.get_D_SA3()
    K_PW2 = state.get_K_PW2()
    K_SA3 = state.get_K_SA3()
    free_gates = state.get_free_gates()
    
    # ========== Step 3: 计算各区域准入限额 ==========
    limit_PW1 = check_PW1_admission(D_PW1, params)
    limit_PW2 = check_PW2_admission(D_PW2, K_PW2, params)
    limit_SA3 = check_SA3_admission(D_SA3, K_SA3, params)
    limit_gate = check_gate_admission(free_gates)
    
    # ========== Step 4: 按上游→下游顺序处理转移 ==========
    
    # --- 4.1 SA1 → PW (PA1→PW1, PA2→PW2) ---
    candidates_PA1, candidates_PA2 = get_candidates_SA1_to_PW(state)
    
    # 处理PA1 → PW1
    admitted_PW1 = 0
    for p in candidates_PA1:
        if admitted_PW1 < limit_PW1:
            # 允许进入PW1
            p.position = Position.PW1
            p.t_enter_PW = state.T
            p.t_PW_basic = compute_t_PW1_basic(params)  # 15.5s
            p.t_SA2_add = 0.0
            p.t_leave_current = p.t_enter_PW + p.t_PW_basic
            admitted_PW1 += 1
        else:
            # 不能进入，累加附加时间
            p.t_SA1_add += dt
            p.t_leave_current += dt
    
    # 处理PA2 → PW2
    admitted_PW2 = 0
    for p in candidates_PA2:
        if admitted_PW2 < limit_PW2:
            # 允许进入PW2
            p.position = Position.PW2
            p.t_enter_PW = state.T
            # 使用进入时刻的密度计算基本时间 - 公式(4)(5)
            p.t_PW_basic = compute_t_PW2_basic(K_PW2, params)
            p.t_SA2_add = 0.0
            p.t_leave_current = p.t_enter_PW + p.t_PW_basic
            admitted_PW2 += 1
        else:
            # 不能进入，累加附加时间
            p.t_SA1_add += dt
            p.t_leave_current += dt
    
    # --- 4.2 PW → SA3 ---
    candidates_PW_SA3 = get_candidates_PW_to_SA3(state)
    
    admitted_SA3 = 0
    for p in candidates_PW_SA3:
        if admitted_SA3 < limit_SA3:
            # 允许进入SA3
            p.position = Position.SA3
            p.t_enter_SA3 = state.T
            # 使用进入时刻的密度计算基本时间 - 公式(6)(7)(8)
            p.t_SA3_basic = compute_t_SA3_basic(p, K_SA3, params)
            p.t_SA3_add = 0.0
            p.t_leave_current = p.t_enter_SA3 + p.t_SA3_basic
            admitted_SA3 += 1
        else:
            # 不能进入，累加附加时间（在PW区域等待）
            p.t_SA2_add += dt
            p.t_leave_current += dt
    
    # --- 4.3 SA3 → Gate (直接通过) ---
    # 注意：t_s已包含在SA3基本时间中
    # 闸机约束的是"同时通过人数"，不是额外服务时间
    candidates_SA3_gate = get_candidates_SA3_to_gate(state)
    
    admitted_gate = 0
    for p in candidates_SA3_gate:
        if admitted_gate < params.N_G:  # 直接用闸机数量作为限制
            # 允许通过闸机，直接离开系统
            p.position = Position.PASSED
            p.t_exit_system = state.T
            admitted_gate += 1
        else:
            # 不能通过，累加附加时间
            p.t_SA3_add += dt
            p.t_leave_current += dt
    
    # ========== Step 5: 记录历史 ==========
    state.record_history()
    
    # ========== Step 6: 时间推进 ==========
    state.T = round(state.T + dt, 6)  # 避免浮点累积误差


def run_simulation(params: SystemParameters, q_PA1: float, q_PA2: float,
                   arrival_duration: float, max_time: float = 1000.0) -> SystemState:
    """运行完整仿真
    
    阶段1：到达阶段（0到arrival_duration）
    阶段2：疏散阶段（停止到达，直到所有乘客离开）
    
    Args:
        params: 系统参数
        q_PA1: PA1到达率 (ped/s)
        q_PA2: PA2到达率 (ped/s)
        arrival_duration: 到达持续时间 (s)
        max_time: 最大仿真时间 (s)，防止死循环
        
    Returns:
        仿真完成后的系统状态
    """
    state = SystemState(params=params)
    
    arrival_steps = int(arrival_duration / params.dt)
    
    # 阶段1：到达阶段
    for _ in range(arrival_steps):
        simulation_step(state, q_PA1, q_PA2)
    
    # 阶段2：疏散阶段
    while state.T < max_time:
        # 检查是否所有乘客都已通过
        if state.get_D_pass() >= state.get_D_all():
            break
        
        simulation_step(state, 0.0, 0.0)
    
    return state
