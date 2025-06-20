# 统一调度系统配置文件

# 系统配置
config = {
    # 地图配置
    'map_center': (22.5, 113.4),  # 默认中心位置
    'zoom_start': 13,
    'map_center': [39.9042, 116.4074],  # 地图中心点（北京）
    'zoom_start': 13,  # 初始缩放级别
    'map_update_interval': 1.0,  # 地图更新间隔（秒）
    'path_cache_time': 300,  # 路径缓存时间（秒）
    'min_drone_distance': 50.0,  # 无人机最小安全距离（米）
    'max_drones_per_zone': 5,  # 每个空域最大无人机数量
    
    # 任务优先级
    'priority_levels': {
        'emergency': 5,  # 紧急任务
        'high': 4,      # 高优先级
        'normal': 3,    # 普通优先级
        'low': 2,       # 低优先级
        'background': 1 # 后台任务
    },
    
    # 车辆通用参数
    'min_battery_level': 15.0,  # 最低电量阈值（百分比）
    'low_battery_threshold': 30.0,  # 低电量警告阈值（百分比）
    'vehicle_timeout': 30.0,  # 车辆状态更新超时时间（秒）
    
    # 无人机参数
    'drone': {
        'max_payload': 5.0,      # 最大负载（kg）
        'max_speed': 15.0,       # 最大速度（m/s）
        'min_altitude': 30.0,    # 最低飞行高度（米）
        'max_altitude': 120.0,   # 最高飞行高度（米）
        'battery_consumption_rate': 0.5,  # 电量消耗率（百分比/分钟）
        'max_wind_speed': 8.0,   # 最大可飞行风速（m/s）
        'min_visibility': 1000,  # 最小能见度（米）
    },
    
    # 无人车参数
    'car': {
        'max_payload': 20.0,     # 最大负载（kg）
        'max_speed': 10.0,       # 最大速度（m/s）,
        'battery_consumption_rate': 0.3,  # 电量消耗率（百分比/分钟）
    },

    # 安全参数
    'safety': {
        'min_vehicle_distance': 10.0,  # 车辆间最小安全距离（米）
        'obstacle_safety_margin': 5.0,  # 障碍物安全边距（米）
        'weather_limits': {  # 天气限制
            'max_wind_speed': 8.0,      # 最大风速（米/秒）
            'min_visibility': 1000.0,   # 最低能见度（米）
            'max_precipitation': 10.0,  # 最大降水量（毫米/小时）
        }
    },
    
    # 补给任务配置
    'resupply': {
        'task_timeout': 600,          # 补给任务超时时间（秒）
        'min_distance': 50.0,         # 最小补给距离（米）
        'max_distance': 5000.0,       # 最大补给距离（米）
        'wait_time': 300,             # 补给等待时间（秒）
        'charge_rate': 2.0,           # 充电速率（百分比/分钟）
        'target_level': 90.0,         # 补给目标电量（百分比）
        'speed': 8.0                  # 补给速度（米/秒）
    },
    
    # 任务调度参数
    'scheduler': {
        'interval': 5.0,             # 调度间隔（秒）
        'task_retry_limit': 3,        # 任务重试次数限制
        'task_timeout': 3600,         # 任务超时时间（秒）
        'priority_aging_factor': 0.1,  # 优先级老化因子（每小时）
        'max_concurrent_tasks': 100,   # 最大并发任务数
        'queue_size_limit': 1000      # 队列大小限制
    },
    
    # 路径规划参数
    'path_planning': {
        'update_interval': 30.0,      # 路径更新间隔（秒）
        'reroute_threshold': 100.0,    # 重新规划路径的偏离阈值（米）
        'local_planner_range': 200.0   # 局部规划器范围（米）
    },
    
    # 系统监控参数
    'monitoring': {
        'status_update_interval': 1.0,  # 状态更新间隔（秒）
        'log_level': 'INFO',            # 日志级别
        'metrics': [                    # 需要监控的指标
            'battery_level',
            'location',
            'task_status',
            'system_load',
            'network_status'
        ]
    },
    
    # 地图显示设置
    'map_display': {
        'drone_color': 'red',          # 无人机标记颜色
        'car_color': 'blue',           # 无人车标记颜色
        'task_color': 'gray',          # 任务路线颜色
        'assigned_opacity': 1.0,        # 已分配任务透明度
        'pending_opacity': 0.6          # 待分配任务透明度
    },
    
    # 数据存储参数
    'storage': {
        'state_save_interval': 300,    # 状态保存间隔（秒）
        'state_file_path': 'system_state.json',  # 状态文件路径
        'max_state_files': 10,         # 最大状态文件数量
        'map_save_interval': 60,       # 地图保存间隔（秒）
        'map_filename': 'delivery_map.html'  # 地图文件名
    },
    
    # 通信参数
    'communication': {
        'heartbeat_interval': 5.0,     # 心跳包间隔（秒）
        'connection_timeout': 15.0,     # 连接超时时间（秒）
        'retry_interval': 3.0          # 重试间隔（秒）
    },
    
    # 应急处理配置
    'emergency': {
        'reserve_vehicles': 2,         # 应急预留车辆数量
        'response_timeout': 300,        # 应急响应超时时间（秒）
        'fallback_strategies': [        # 故障转移策略
            'retry_assignment',
            'reduce_payload',
            'alternative_route',
            'manual_intervention'
        ]
    }
}