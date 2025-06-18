# docking 模块配置文件
import cv2

# 与 Pixhawk 的 MAVSDK 连接 URI
CONNECTION_URI = "serial:///dev/ttyAMA0:57600"

# 摄像头索引（0为第一个摄像头）
CAMERA_ID = 0

# ArUco 标记检测参数
ARUCO_DICT = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
ARUCO_PARAMS = cv2.aruco.DetectorParameters_create()

# 对接中对齐阈值（像素）
CENTER_THRESHOLD = 20

# 控制增益（速度调整比例系数）
P_GAIN = 0.005
