import asyncio
from typing import Dict, Tuple
from mavsdk import System
from .autonomous_control import AutonomousController, PathPoint
from . import config
import logging

class VehicleController:
    def __init__(self, vehicle_type: str):
        self.vehicle_type = vehicle_type
        self.drone = System()
        self.autonomous_controller = AutonomousController()
        self.autonomous_controller.set_vehicle_type(vehicle_type)
        self.logger = logging.getLogger(__name__)
        
    async def connect(self, connection_uri: str):
        """连接到飞行控制器"""
        await self.drone.connect(system_address=connection_uri)
        self.logger.info(f"正在连接到{self.vehicle_type}: {connection_uri}")
        
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                self.logger.info(f"{self.vehicle_type}已连接")
                break
                
    async def initialize(self):
        """初始化控制系统"""
        if self.vehicle_type == 'drone':
            await self._initialize_drone()
        else:
            await self._initialize_car()
            
    async def _initialize_drone(self):
        """初始化无人机"""
        self.logger.info("初始化无人机系统...")
        # 等待GPS就绪
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok:
                self.logger.info("GPS就绪")
                break
                
        # 获取当前位置和航向
        async for position in self.drone.telemetry.position():
            current_pos = (position.latitude_deg,
                         position.longitude_deg,
                         position.relative_altitude_m)
            self.autonomous_controller.update_position(current_pos)
            break
            
        async for heading in self.drone.telemetry.heading():
            self.autonomous_controller.update_heading(heading.heading_deg)
            break
            
    async def _initialize_car(self):
        """初始化无人车"""
        self.logger.info("初始化无人车系统...")
        # 等待定位系统就绪
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok:
                self.logger.info("定位系统就绪")
                break
                
        # 获取当前位置和航向
        async for position in self.drone.telemetry.position():
            current_pos = (position.latitude_deg,
                         position.longitude_deg,
                         0.0)  # 无人车高度始终为0
            self.autonomous_controller.update_position(current_pos)
            break
            
        async for heading in self.drone.telemetry.heading():
            self.autonomous_controller.update_heading(heading.heading_deg)
            break
            
    async def execute_mission(self, target_position: Tuple[float, float, float]):
        """执行自主导航任务"""
        try:
            # 设置目标位置
            self.autonomous_controller.set_target(target_position)
            
            # 解锁并准备
            if self.vehicle_type == 'drone':
                await self.drone.action.arm()
                await self.drone.action.takeoff()
                self.logger.info("无人机已起飞")
            
            # 开始路径跟踪
            await self._start_path_following()
            
            # 完成任务
            if self.vehicle_type == 'drone':
                await self.drone.action.land()
                self.logger.info("无人机已降落")
            
        except Exception as e:
            self.logger.error(f"任务执行出错: {str(e)}")
            if self.vehicle_type == 'drone':
                await self.drone.action.return_to_launch()
                self.logger.info("无人机正在返航")
                
    async def _start_path_following(self):
        """开始路径跟踪"""
        # 生成路径
        path = self.autonomous_controller.generate_path()
        if not path:
            self.logger.error("无法生成有效路径")
            return
            
        self.logger.info(f"生成路径点数量: {len(path)}")
        
        # 跟踪每个路径点
        for point in path:
            await self._follow_waypoint(point)
            
    async def _follow_waypoint(self, waypoint: PathPoint):
        """跟踪单个航路点"""
        self.logger.info(f"正在前往航路点: {waypoint.position}")
        
        if self.vehicle_type == 'drone':
            await self._control_drone(waypoint)
        else:
            await self._control_car(waypoint)
            
    async def _control_drone(self, waypoint: PathPoint):
        """控制无人机到达航路点"""
        await self.drone.action.goto_location(
            waypoint.position[0],  # 纬度
            waypoint.position[1],  # 经度
            waypoint.position[2],  # 高度
            waypoint.heading       # 航向
        )
        
        # 等待到达目标点
        while True:
            async for position in self.drone.telemetry.position():
                current_pos = (position.latitude_deg,
                             position.longitude_deg,
                             position.relative_altitude_m)
                if self._is_position_reached(current_pos, waypoint.position):
                    return
                break
            await asyncio.sleep(0.1)
            
    async def _control_car(self, waypoint: PathPoint):
        """控制无人车到达航路点"""
        # 设置目标位置和航向
        await self.drone.action.goto_location(
            waypoint.position[0],  # 纬度
            waypoint.position[1],  # 经度
            0.0,                   # 高度始终为0
            waypoint.heading       # 航向
        )
        
        # 等待到达目标点
        while True:
            async for position in self.drone.telemetry.position():
                current_pos = (position.latitude_deg,
                             position.longitude_deg,
                             0.0)
                if self._is_position_reached(current_pos, waypoint.position):
                    return
                break
            await asyncio.sleep(0.1)
            
    def _is_position_reached(self, current: Tuple[float, float, float],
                            target: Tuple[float, float, float]) -> bool:
        """检查是否到达目标位置"""
        threshold = config.PATH_FOLLOWING['waypoint_threshold']
        distance = self.autonomous_controller.calculate_distance(current, target)
        return distance <= threshold