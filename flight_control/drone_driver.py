import asyncio
from mavsdk import System
from typing import Dict, Tuple
import logging
from . import config

class DroneDriver:
    """无人机底层驱动类，负责与PX4飞控通信和基本控制"""
    
    def __init__(self):
        self.drone = System()
        self.logger = logging.getLogger(__name__)
        self.motor_status = [False] * 4  # 四个电机状态
        self.imu_data = {
            'acceleration': (0.0, 0.0, 0.0),
            'angular_velocity': (0.0, 0.0, 0.0),
            'attitude': (0.0, 0.0, 0.0)  # roll, pitch, yaw
        }
        
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
                    
            # 开始传感器数据监控
            asyncio.create_task(self._monitor_imu())
            asyncio.create_task(self._monitor_motors())
            
        except Exception as e:
            self.logger.error(f"初始化失败: {str(e)}")
            raise
            
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
            
    async def land(self) -> bool:
        """降落"""
        try:
            await self.drone.action.land()
            self.logger.info("正在执行降落")
            return True
        except Exception as e:
            self.logger.error(f"降落失败: {str(e)}")
            return False
            
    async def set_attitude(self, roll: float, pitch: float,
                          yaw: float, thrust: float) -> bool:
        """设置姿态（角度和推力）"""
        try:
            await self.drone.offboard.set_attitude({
                'roll_deg': roll,
                'pitch_deg': pitch,
                'yaw_deg': yaw,
                'thrust_value': thrust
            })
            return True
        except Exception as e:
            self.logger.error(f"姿态控制失败: {str(e)}")
            return False
            
    async def set_velocity(self, vx: float, vy: float,
                          vz: float, yaw_rate: float) -> bool:
        """设置速度（体坐标系，米/秒）"""
        try:
            await self.drone.offboard.set_velocity_body({
                'forward_m_s': vx,
                'right_m_s': vy,
                'down_m_s': vz,
                'yawspeed_deg_s': yaw_rate
            })
            return True
        except Exception as e:
            self.logger.error(f"速度控制失败: {str(e)}")
            return False
            
    async def goto_position(self, latitude: float, longitude: float,
                           altitude: float, yaw: float) -> bool:
        """飞到指定位置（全球坐标，度）"""
        try:
            await self.drone.action.goto_location(latitude,
                                                 longitude,
                                                 altitude,
                                                 yaw)
            return True
        except Exception as e:
            self.logger.error(f"位置控制失败: {str(e)}")
            return False
            
    async def get_position(self) -> Tuple[float, float, float]:
        """获取当前位置（纬度、经度、高度）"""
        try:
            async for position in self.drone.telemetry.position():
                return (position.latitude_deg,
                        position.longitude_deg,
                        position.relative_altitude_m)
        except Exception as e:
            self.logger.error(f"获取位置失败: {str(e)}")
            return (0.0, 0.0, 0.0)
            
    async def get_battery(self) -> float:
        """获取电池电量百分比"""
        try:
            async for battery in self.drone.telemetry.battery():
                return battery.remaining_percent
        except Exception as e:
            self.logger.error(f"获取电池状态失败: {str(e)}")
            return 0.0
            
    def get_imu_data(self) -> Dict:
        """获取IMU数据"""
        return self.imu_data.copy()
        
    def get_motor_status(self) -> List[bool]:
        """获取电机状态"""
        return self.motor_status.copy()