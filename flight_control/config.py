# 低空物流系统配置文件

# 无人机连接配置
CONNECTION_URI = "serial:///dev/ttyAMA0:57600"  # Pixhawk 连接

# 飞行参数配置
TAKEOFF_ALTITUDE = 30.0  # 起飞高度 (米)
CRUISE_ALTITUDE = 25.0   # 巡航高度 (米)
TARGET_ALTITUDE = 20.0   # 投放高度 (米)
MAX_SPEED = 10.0         # 最大飞行速度 (米/秒)

# 示例配送点位置
TARGET_LATITUDE = 22.5   # 配送点纬度
TARGET_LONGITUDE = 113.4 # 配送点经度

# 安全参数配置
MIN_BATTERY_PERCENT = 20.0  # 最低电量百分比
MAX_PAYLOAD_WEIGHT = 5.0    # 最大负载重量(kg)
MIN_SAFE_DISTANCE = 10.0    # 最小安全距离(米)

# 任务超时配置（秒）
TAKEOFF_TIMEOUT = 60     # 起飞超时
LANDING_TIMEOUT = 60     # 着陆超时
WAYPOINT_TIMEOUT = 300   # 航点到达超时

# 天气限制
MAX_WIND_SPEED = 8.0     # 最大风速 (米/秒)
MIN_VISIBILITY = 1000    # 最小能见度 (米)
