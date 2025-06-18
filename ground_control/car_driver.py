import serial
import time
from typing import Dict, List, Tuple
import logging
from . import config

class CarDriver:
    """地面车底层驱动类，负责与Arduino通信和基本控制"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.serial = None
        self.sensor_data = {
            'ultrasonic': [0.0] * 4,  # 4个超声波传感器数据
            'lidar': 0.0,             # TFLuna激光测距数据
            'battery': 0.0,           # 电池电量
            'charging': False          # 是否在充电
        }
        self.motor_speed = [0] * 4    # 4个电机的当前速度
        
    def initialize(self) -> bool:
        """初始化串口连接"""
        try:
            self.serial = serial.Serial(
                port=config.SERIAL_PORT,
                baudrate=config.BAUDRATE,
                timeout=1
            )
            time.sleep(2)  # 等待Arduino重置
            self.logger.info(f"已连接到Arduino: {config.SERIAL_PORT}")
            return True
        except Exception as e:
            self.logger.error(f"串口连接失败: {str(e)}")
            return False
            
    def close(self):
        """关闭串口连接"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.logger.info("串口连接已关闭")
            
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
            self.logger.error(f"未知移动方向: {direction}")
            return False
            
        return self.set_motor_speed(speeds)
        
    def turn(self, angle: float, speed: int) -> bool:
        """原地转向指定角度
        Args:
            angle: 转向角度，正值顺时针，负值逆时针
            speed: 转向速度，0~255
        """
        speed = max(0, min(255, speed))
        
        if angle > 0:  # 顺时针
            speeds = [-speed, speed, -speed, speed]
        else:  # 逆时针
            speeds = [speed, -speed, speed, -speed]
            
        # 根据角度计算转向时间
        turn_time = abs(angle) / (360.0 / config.TURN_TIME_360)
        
        if self.set_motor_speed(speeds):
            time.sleep(turn_time)
            return self.stop()
        return False
        
    def update_sensors(self) -> bool:
        """更新传感器数据"""
        try:
            # 请求传感器数据
            if not self._send_command("S"):
                return False
                
            # 读取响应
            response = self._read_response()
            if not response.startswith("DATA:"):
                return False
                
            # 解析数据
            # 格式: "DATA:u1,u2,u3,u4,l,b,c"
            # u1-u4: 超声波数据, l: 激光测距, b: 电池电量, c: 充电状态
            data = response[5:].split(',')
            if len(data) != 7:
                return False
                
            self.sensor_data['ultrasonic'] = [float(x) for x in data[:4]]
            self.sensor_data['lidar'] = float(data[4])
            self.sensor_data['battery'] = float(data[5])
            self.sensor_data['charging'] = (data[6] == '1')
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新传感器数据失败: {str(e)}")
            return False
            
    def get_sensor_data(self) -> Dict:
        """获取传感器数据"""
        return self.sensor_data.copy()
        
    def get_motor_speed(self) -> List[int]:
        """获取电机速度"""
        return self.motor_speed.copy()
        
    def start_charging(self) -> bool:
        """开始无线充电"""
        return self._send_command("C,1")
        
    def stop_charging(self) -> bool:
        """停止无线充电"""
        return self._send_command("C,0")