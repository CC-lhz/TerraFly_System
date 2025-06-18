# 自动驾驶系统配置文件

# 路径规划参数
PATH_PLANNING = {
    'drone': {
        'step_size': 5.0,         # 路径点间距（米）
        'search_angles': 5,        # 搜索角度数量
        'angle_range': 60,         # 搜索角度范围（度）
        'max_velocity': 10.0,      # 最大速度（米/秒）
        'min_velocity': 2.0,       # 最小速度（米/秒）
        'max_altitude': 100.0,     # 最大飞行高度（米）
        'min_altitude': 10.0,      # 最小飞行高度（米）
        'obstacle_margin': 5.0     # 障碍物安全边距（米）
    },
    'car': {
        'step_size': 3.0,         # 路径点间距（米）
        'search_angles': 7,        # 搜索角度数量
        'angle_range': 90,         # 搜索角度范围（度）
        'max_velocity': 5.0,       # 最大速度（米/秒）
        'min_velocity': 1.0,       # 最小速度（米/秒）
        'turning_radius': 5.0,     # 最小转弯半径（米）
        'obstacle_margin': 2.0     # 障碍物安全边距（米）
    }
}

# 控制参数
CONTROL = {
    'drone': {
        'pos_p_gain': 0.5,        # 位置比例增益
        'heading_p_gain': 0.5,     # 航向比例增益
        'altitude_p_gain': 0.5,    # 高度比例增益
        'max_heading_rate': 45.0,  # 最大航向角速度（度/秒）
        'max_climb_rate': 3.0,     # 最大爬升速率（米/秒）
        'hover_precision': 0.5     # 悬停精度（米）
    },
    'car': {
        'pos_p_gain': 0.3,        # 位置比例增益
        'heading_p_gain': 0.4,     # 航向比例增益
        'max_heading_rate': 30.0,  # 最大航向角速度（度/秒）
        'stop_precision': 0.3      # 停车精度（米）
    }
}

# 避障参数
OBSTACLE_AVOIDANCE = {
    'max_detection_range': 50.0,   # 最大探测范围（米）
    'update_frequency': 10,        # 障碍物更新频率（赫兹）
    'emergency_distance': 3.0,     # 紧急避障距离（米）
    'avoidance_velocity': 2.0      # 避障速度（米/秒）
}

# 路径跟踪参数
PATH_FOLLOWING = {
    'waypoint_threshold': 0.5,    # 航点到达阈值（米）
    'path_tolerance': 1.0,         # 路径跟踪容差（米）
    'control_frequency': 10,       # 控制频率（赫兹）
    'replanning_threshold': 5.0    # 重规划触发距离（米）
}

# 安全参数
SAFETY = {
    'drone': {
        'min_battery': 20.0,      # 最低电量（百分比）
        'return_battery': 30.0,    # 返航电量（百分比）
        'max_wind_speed': 8.0,     # 最大风速（米/秒）
        'min_visibility': 1000.0   # 最小能见度（米）
    },
    'car': {
        'min_battery': 15.0,      # 最低电量（百分比）
        'return_battery': 25.0,    # 返航电量（百分比）
        'max_slope': 15.0,         # 最大坡度（度）
        'min_visibility': 50.0     # 最小能见度（米）
    }
}