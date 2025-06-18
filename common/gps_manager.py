import serial
import pynmea2
import logging
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class GPSData:
    """GPS数据类"""
    latitude: float = 0.0    # 纬度
    longitude: float = 0.0   # 经度
    altitude: float = 0.0    # 海拔高度(米)
    speed: float = 0.0       # 地面速度(米/秒)
    heading: float = 0.0     # 航向角(度)
    satellites: int = 0      # 卫星数量
    fix_quality: int = 0     # 定位质量
    timestamp: str = ''      # 时间戳

class GPSManager:
    """GPS管理器，用于处理GPS模块的数据读取和解析"""
    
    def __init__(self, port: str, baudrate: int = 9600):
        self.logger = logging.getLogger(__name__)
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.gps_data = GPSData()
        
    def initialize(self) -> bool:
        """初始化GPS模块"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.logger.info(f"GPS模块已连接: {self.port}")
            return True
        except Exception as e:
            self.logger.error(f"GPS模块连接失败: {str(e)}")
            return False
            
    def close(self):
        """关闭GPS连接"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.logger.info("GPS连接已关闭")
            
    def update(self) -> Optional[GPSData]:
        """更新GPS数据
        Returns:
            GPSData: 更新后的GPS数据，如果读取失败则返回None
        """
        try:
            if not (self.serial and self.serial.is_open):
                return None
                
            # 读取GPS数据直到获取到有效的GPRMC或GPGGA语句
            while True:
                line = self.serial.readline().decode('ascii', errors='replace')
                if line.startswith('$GPRMC'):
                    msg = pynmea2.parse(line)
                    if msg.status == 'A':  # 数据有效
                        self.gps_data.latitude = msg.latitude
                        self.gps_data.longitude = msg.longitude
                        self.gps_data.speed = msg.spd_over_grnd * 0.514444  # 节转米/秒
                        self.gps_data.heading = msg.true_course or 0.0
                        self.gps_data.timestamp = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                        
                elif line.startswith('$GPGGA'):
                    msg = pynmea2.parse(line)
                    self.gps_data.altitude = msg.altitude
                    self.gps_data.satellites = msg.num_sats
                    self.gps_data.fix_quality = msg.gps_qual
                    return self.gps_data
                    
        except Exception as e:
            self.logger.error(f"GPS数据更新失败: {str(e)}")
            return None
            
    def get_position(self) -> Tuple[float, float, float]:
        """获取当前位置
        Returns:
            Tuple[float, float, float]: (纬度, 经度, 海拔)
        """
        return (self.gps_data.latitude, self.gps_data.longitude, self.gps_data.altitude)
        
    def get_speed_heading(self) -> Tuple[float, float]:
        """获取当前速度和航向
        Returns:
            Tuple[float, float]: (速度, 航向角)
        """
        return (self.gps_data.speed, self.gps_data.heading)
        
    def get_fix_info(self) -> Tuple[int, int]:
        """获取定位信息
        Returns:
            Tuple[int, int]: (卫星数量, 定位质量)
        """
        return (self.gps_data.satellites, self.gps_data.fix_quality)