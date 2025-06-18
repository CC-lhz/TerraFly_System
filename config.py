# 系统配置文件

# 无人机参数配置
DRONE = {
    # 通信参数
    'connection_uri': 'udp://:14540',  # MAVLink连接地址
    'mavlink_baudrate': 57600,         # MAVLink波特率
    
    # 机架参数
    'frame_type': 'quad_x',            # 四轴X型布局
    'frame_size': 450,                 # 轴距450mm
    
    # 电机参数
    'motor_kv': 920,                   # 电机KV值
    'motor_max_thrust': 1200,          # 最大推力（克）
    'motor_idle_thrust': 50,           # 怠速推力（克）
    'esc_pwm_min': 1000,              # 电调最小PWM
    'esc_pwm_max': 2000,              # 电调最大PWM
    
    # 飞行参数
    'max_velocity': 10.0,             # 最大水平速度（米/秒）
    'max_ascent_velocity': 3.0,       # 最大上升速度（米/秒）
    'max_descent_velocity': 2.0,      # 最大下降速度（米/秒）
    'max_yaw_rate': 90.0,             # 最大偏航角速度（度/秒）
    'hover_thrust': 0.5,              # 悬停推力比例
    
    # 负载参数
    'max_payload': 5000,              # 最大负载（克）
    'empty_weight': 1200,             # 空机重量（克）
    
    # 电池参数
    'battery_cells': 4,               # 电池节数（4S）
    'battery_capacity': 5200,         # 电池容量（mAh）
    'battery_warning': 20.0,          # 低电量警告（百分比）
    'battery_critical': 15.0,         # 紧急返航电量（百分比）
    
    # 安全参数
    'max_tilt_angle': 35.0,          # 最大倾斜角度（度）
    'max_altitude': 120.0,            # 最大飞行高度（米）
    'min_altitude': 2.0,              # 最小飞行高度（米）
    'max_distance': 1000.0,           # 最大飞行距离（米）
    'max_wind_speed': 8.0,            # 最大可飞风速（米/秒）
    'min_visibility': 1000.0,         # 最小能见度（米）
    
    # 视觉参数
    'camera_fov': 87,                 # 相机视场角（度）
    'camera_resolution': (1280, 720),  # 相机分辨率
    'camera_fps': 30,                 # 相机帧率
    'depth_range': (0.2, 10.0),       # 深度探测范围（米）
}

# 地面车参数配置
CAR = {
    # 通信参数
    'serial_port': 'COM3',            # Arduino串口
    'serial_baudrate': 115200,        # 串口波特率
    
    # 底盘参数
    'wheel_diameter': 0.15,           # 车轮直径（米）
    'wheel_base': 0.4,                # 轴距（米）
    'track_width': 0.35,              # 轮距（米）
    'ground_clearance': 0.1,          # 离地间隙（米）
    
    # 电机参数
    'motor_rated_voltage': 24,        # 电机额定电压（伏）
    'motor_rated_current': 5,         # 电机额定电流（安）
    'motor_max_rpm': 200,             # 电机最大转速
    'motor_reduction_ratio': 20,      # 减速比
    
    # 运动参数
    'max_velocity': 2.0,              # 最大速度（米/秒）
    'max_acceleration': 1.0,          # 最大加速度（米/秒²）
    'max_turning_radius': 0.5,        # 最小转弯半径（米）
    'max_slope': 15.0,                # 最大爬坡角度（度）
    
    # 负载参数
    'max_payload': 10000,             # 最大负载（克）
    'empty_weight': 8000,             # 空载重量（克）
    
    # 电池参数
    'battery_voltage': 48,            # 电池电压（伏）
    'battery_capacity': 20000,        # 电池容量（mAh）
    'battery_warning': 25.0,          # 低电量警告（百分比）
    'battery_critical': 20.0,         # 紧急充电电量（百分比）
    
    # 充电参数
    'charging_voltage': 48,           # 充电电压（伏）
    'charging_current': 4,            # 充电电流（安）
    'charging_efficiency': 0.85,      # 充电效率
    
    # 传感器参数
    'ultrasonic_range': 4.0,          # 超声波探测范围（米）
    'ultrasonic_angle': 15,           # 超声波探测角度（度）
    'lidar_range': 8.0,               # 激光雷达探测范围（米）
    'lidar_angle': 2,                 # 激光雷达探测角度（度）
    
    # 安全参数
    'obstacle_distance': 0.5,         # 避障距离（米）
    'emergency_stop_distance': 0.3,   # 紧急停车距离（米）
    'min_visibility': 50.0,           # 最小能见度（米）
}

# 控制参数配置
CONTROL = {
    # PID参数
    'position_p': 1.0,
    'position_i': 0.1,
    'position_d': 0.2,
    'velocity_p': 1.2,
    'velocity_i': 0.1,
    'velocity_d': 0.2,
    'attitude_p': 4.0,
    'attitude_i': 0.3,
    'attitude_d': 0.2,
    'yaw_p': 2.0,
    'yaw_i': 0.1,
    'yaw_d': 0.1,
    
    # 控制频率
    'position_control_freq': 50,      # 位置控制频率（Hz）
    'attitude_control_freq': 200,     # 姿态控制频率（Hz）
    'sensor_update_freq': 100,        # 传感器更新频率（Hz）
    'telemetry_freq': 10,             # 遥测数据频率（Hz）
    
    # 控制死区
    'position_deadband': 0.1,         # 位置控制死区（米）
    'velocity_deadband': 0.05,        # 速度控制死区（米/秒）
    'attitude_deadband': 1.0,         # 姿态控制死区（度）
    'yaw_deadband': 2.0,             # 偏航控制死区（度）
    
    # 平滑参数
    'position_smooth': 0.8,           # 位置命令平滑系数
    'velocity_smooth': 0.8,           # 速度命令平滑系数
    'attitude_smooth': 0.9,           # 姿态命令平滑系数
    'yaw_smooth': 0.8,                # 偏航命令平滑系数
}