import asyncio
from mavsdk import System
from typing import Dict, Tuple
import logging
from . import config
from ..common.gps_manager import GPSManager, GPSData

class DroneDriver:
    """无人机底层驱动类，负责与PX4飞控通信和基本控制"""
    
    def __init__(self):
        self.drone = System()
        self.logger = logging.getLogger(__name__)
        self.gps_manager = GPSManager(config.GPS_PORT, config.GPS_BAUDRATE)
        self.motor_status = [False] * 4  # 四个电机状态
        self.imu_data = {
            'acceleration': (0.0, 0.0, 0.0),
            'angular_velocity': (0.0, 0.0, 0.0),
            'attitude': (0.0, 0.0, 0.0)  # roll, pitch, yaw
        }
        self.gps_data = None  # 最新的GPS数据
        
    async def initialize(self):
        """初始化无人机系统"""
        try:
            # 连接到PX4
            await self.drone.connect(system_address=config.CONNECTION_URI)
            self.logger.info(f"正在连接到PX4: {config.CONNECTION_URI}")
            
            # 等待连接
            async for state in self.drone.core.connection_state():
                if state.is_connected:
                    self.logger.info("PX4连接成功")
                    break
            
            # 初始化GPS模块
            if not self.gps_manager.initialize():
                self.logger.error("GPS模块初始化失败")
                return False
                    
            # 开始传感器数据监控
            asyncio.create_task(self._monitor_imu())
            asyncio.create_task(self._monitor_motors())
            asyncio.create_task(self._monitor_gps())
            
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失败: {str(e)}")
            return False
            
    async def _monitor_imu(self):
        """监控IMU数据"""
        try:
            async for imu in self.drone.telemetry.imu():
                self.imu_data['acceleration'] = (
                    imu.acceleration_frd.forward_m_s2,
                    imu.acceleration_frd.right_m_s2,
                    imu.acceleration_frd.down_m_s2
                )
                self.imu_data['angular_velocity'] = (
                    imu.angular_velocity_frd.forward_rad_s,
                    imu.angular_velocity_frd.right_rad_s,
                    imu.angular_velocity_frd.down_rad_s
                )
                
            async for attitude in self.drone.telemetry.attitude_euler():
                self.imu_data['attitude'] = (
                    attitude.roll_deg,
                    attitude.pitch_deg,
                    attitude.yaw_deg
                )
                
        except Exception as e:
            self.logger.error(f"IMU数据监控错误: {str(e)}")
            
    async def _monitor_motors(self):
        """监控电机状态"""
        try:
            async for actuator in self.drone.telemetry.actuator_control_target():
                # 更新电机状态（简化处理，实际应该根据具体PWM值判断）
                for i in range(4):
                    self.motor_status[i] = actuator.controls[i] > 0.1
                    
        except Exception as e:
            self.logger.error(f"电机状态监控错误: {str(e)}")
            
    async def _monitor_gps(self):
        """监控GPS数据"""
        while True:
            try:
                self.gps_data = self.gps_manager.update()
                if self.gps_data:
                    self.logger.debug(f"GPS位置更新: {self.gps_data.latitude}, {self.gps_data.longitude}")
                await asyncio.sleep(1)  # 每秒更新一次GPS数据
            except Exception as e:
                self.logger.error(f"GPS数据监控错误: {str(e)}")
                await asyncio.sleep(5)  # 出错后等待5秒再重试
            
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
            
    async def arm(self) -> bool:
        """解锁无人机"""
        try:
            await self.drone.action.arm()
            self.logger.info("无人机已解锁")
            return True
        except Exception as e:
            self.logger.error(f"解锁失败: {str(e)}")
            return False
            
    async def disarm(self) -> bool:
        """上锁无人机"""
        try:
            await self.drone.action.disarm()
            self.logger.info("无人机已上锁")
            return True
        except Exception as e:
            self.logger.error(f"上锁失败: {str(e)}")
            return False
            
    async def takeoff(self, altitude: float) -> bool:
        """起飞到指定高度"""
        try:
            await self.drone.action.set_takeoff_altitude(altitude)
            await self.drone.action.takeoff()
            self.logger.info(f"正在起飞到{altitude}米高度")
            return True
        except Exception as e:
            self.logger.error(f"起飞失败: {str(e)}")
            return False