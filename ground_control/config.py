# ground_control 模块配置文件

# 串口配置 (与 Arduino 通信)
SERIAL_PORT = "/dev/ttyACM0"
BAUDRATE = 9600

# GPS模块配置
GPS_PORT = "/dev/ttyUSB1"  # GPS模块串口
GPS_BAUDRATE = 9600       # GPS波特率

# 地面车速度设置（0~255）
FORWARD_SPEED = 150
REVERSE_SPEED = 150
TURN_SPEED = 100

# 避障安全距离 (厘米)
SAFE_DISTANCE = 30
