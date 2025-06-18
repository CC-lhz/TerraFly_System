import serial
import time
from typing import Dict, List, Tuple
import logging
from . import config
from ..common.gps_manager import GPSManager, GPSData

class CarDriver:
    """地面车底层驱动类，负责与Arduino通信和基本控制"""
    
    def __init__(self, use_ultrasonic=True, use_lidar=True):
        self.logger = logging.getLogger(__name__)
        self.serial = None
        self.gps_manager = GPSManager(config.GPS_PORT, config.GPS_BAUDRATE)
        self.use_ultrasonic = use_ultrasonic
        self.use_lidar = use_lidar
        
        self.sensor_data = {
            'ultrasonic': [0.0] * 4 if use_ultrasonic else None,  # 超声波传感器数据（可选）
            'lidar': 0.0 if use_lidar else None,                   # TFLuna激光测距数据（可选）
            'battery': 0.0,                                        # 电池电量
            'charging': False                                      # 是否在充电
        }
        self.motor_speed = [0] * 4    # 4个电机的当前速度
        self.obstacle_detected = False # 障碍物检测状态
        self.gps_data = None          # 最新的GPS数据
        
    def initialize(self) -> bool:
        """初始化串口连接和GPS模块"""
        try:
            # 初始化Arduino串口
            self.serial = serial.Serial(
                port=config.SERIAL_PORT,
                baudrate=config.BAUDRATE,
                timeout=1
            )
            time.sleep(2)  # 等待Arduino重置
            self.logger.info(f"已连接到Arduino: {config.SERIAL_PORT}")
            
            # 初始化GPS模块
            if not self.gps_manager.initialize():
                self.logger.error("GPS模块初始化失败")
                return False
                
            # 启动GPS数据更新线程
            import threading
            self.gps_thread = threading.Thread(target=self._update_gps, daemon=True)
            self.gps_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失败: {str(e)}")
            return False
            
    def close(self):
        """关闭串口连接和GPS模块"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.logger.info("串口连接已关闭")
        self.gps_manager.close()
            
    def _send_command(self, cmd: str) -> bool:
        """发送命令到Arduino"""
        try:
            if self.serial and self.serial.is_open:
                self.serial.write(f"{cmd}\n".encode())
                return True
            return False
        except Exception as e:
            self.logger.error(f"发送命令失败: {str(e)}")
            return False
            
    def _read_response(self) -> str:
        """读取Arduino响应"""
        try:
            if self.serial and self.serial.is_open:
                return self.serial.readline().decode('utf-8').strip()
            return ""
        except Exception as e:
            self.logger.error(f"读取响应失败: {str(e)}")
            return ""
            
    def _update_gps(self):
        """GPS数据更新线程"""
        while True:
            try:
                self.gps_data = self.gps_manager.update()
                if self.gps_data:
                    self.logger.debug(f"GPS位置更新: {self.gps_data.latitude}, {self.gps_data.longitude}")
                time.sleep(1)  # 每秒更新一次GPS数据
            except Exception as e:
                self.logger.error(f"GPS数据更新错误: {str(e)}")
                time.sleep(5)  # 出错后等待5秒再重试
                
    def get_position(self) -> Tuple[float, float, float]:
        """获取当前位置
        Returns:
            Tuple[float, float, float]: (纬度, 经度, 海拔)
        """
        if self.gps_data:
            return self.gps_manager.get_position()
        return (0.0, 0.0, 0.0)
        
    def get_speed_heading(self) -> Tuple[float, float]:
        """获取当前速度和航向
        Returns:
            Tuple[float, float]: (速度, 航向角)
        """
        if self.gps_data:
            return self.gps_manager.get_speed_heading()
        return (0.0, 0.0)
        
    def get_fix_info(self) -> Tuple[int, int]:
        """获取GPS定位信息
        Returns:
            Tuple[int, int]: (卫星数量, 定位质量)
        """
        if self.gps_data:
            return self.gps_manager.get_fix_info()
        return (0, 0)
            
    def set_motor_speed(self, speeds: List[int]) -> bool:
        """设置电机速度
        Args:
            speeds: 4个电机的速度值列表，范围-255~255
        """
        if len(speeds) != 4:
            self.logger.error("电机速度参数错误")
            return False
            
        # 限制速度范围
        speeds = [max(-255, min(255, s)) for s in speeds]
        cmd = f"M,{speeds[0]},{speeds[1]},{speeds[2]},{speeds[3]}"
        
        if self._send_command(cmd):
            self.motor_speed = speeds.copy()
            return True
        return False
        
    def stop(self) -> bool:
        """停止所有电机"""
        return self.set_motor_speed([0, 0, 0, 0])
        
    def move(self, direction: str, speed: int) -> bool:
        """控制车辆移动
        Args:
            direction: 移动方向，'forward', 'backward', 'left', 'right'
            speed: 速度值，0~255
        """
        speed = max(0, min(255, speed))
        
        # 根据方向设置各电机速度
        if direction == 'forward':
            speeds = [speed] * 4
        elif direction == 'backward':
            speeds = [-speed] * 4
        elif direction == 'left':
            speeds = [speed, -speed, speed, -speed]
        elif direction == 'right':
            speeds = [-speed, speed, -speed, speed]
        else:
            self.logger.error(f"无效的移动方向: {direction}")
            return False
            
        return self.set_motor_speed(speeds)