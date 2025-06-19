from typing import Dict, List, Optional
from datetime import datetime
import logging
from enum import Enum
import asyncio
import json
import websockets

class VehicleType(Enum):
    """车辆类型"""
    DRONE = 'drone'
    CAR = 'car'

class VehicleStatus(Enum):
    """车辆状态"""
    IDLE = 'idle'
    BUSY = 'busy'
    CHARGING = 'charging'
    MAINTENANCE = 'maintenance'
    ERROR = 'error'
    OFFLINE = 'offline'

class Vehicle:
    """车辆类"""
    def __init__(
        self,
        vehicle_id: str,
        vehicle_type: VehicleType,
        capabilities: List[str],
        max_payload: float,
        battery_capacity: float,
        connection_info: Dict
    ):
        self.id = vehicle_id
        self.type = vehicle_type
        self.capabilities = capabilities
        self.max_payload = max_payload
        self.battery_capacity = battery_capacity
        self.connection_info = connection_info
        
        self.status = VehicleStatus.IDLE
        self.location = {'lat': 0.0, 'lon': 0.0, 'alt': 0.0}
        self.battery_level = 100.0
        self.current_task = None
        self.error_message = None
        
        # 性能参数
        self.average_speed = 0.0
        self.distance_cost_factor = 1.0
        self.time_cost_factor = 1.0
        self.energy_cost_factor = 1.0
        self.payload_cost_factor = 1.0
        self.base_consumption_rate = 0.0
        self.low_battery_threshold = 20.0
        
        # 通信相关
        self.websocket = None
        self.last_heartbeat = None
        self.heartbeat_interval = 1.0  # 秒
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'type': self.type.value,
            'capabilities': self.capabilities,
            'max_payload': self.max_payload,
            'battery_capacity': self.battery_capacity,
            'connection_info': self.connection_info,
            'status': self.status.value,
            'location': self.location,
            'battery_level': self.battery_level,
            'current_task': self.current_task,
            'error_message': self.error_message,
            'average_speed': self.average_speed,
            'distance_cost_factor': self.distance_cost_factor,
            'time_cost_factor': self.time_cost_factor,
            'energy_cost_factor': self.energy_cost_factor,
            'payload_cost_factor': self.payload_cost_factor,
            'base_consumption_rate': self.base_consumption_rate,
            'low_battery_threshold': self.low_battery_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Vehicle':
        """从字典创建车辆对象"""
        vehicle = cls(
            vehicle_id=data['id'],
            vehicle_type=VehicleType(data['type']),
            capabilities=data['capabilities'],
            max_payload=data['max_payload'],
            battery_capacity=data['battery_capacity'],
            connection_info=data['connection_info']
        )
        
        vehicle.status = VehicleStatus(data['status'])
        vehicle.location = data['location']
        vehicle.battery_level = data['battery_level']
        vehicle.current_task = data['current_task']
        vehicle.error_message = data['error_message']
        vehicle.average_speed = data['average_speed']
        vehicle.distance_cost_factor = data['distance_cost_factor']
        vehicle.time_cost_factor = data['time_cost_factor']
        vehicle.energy_cost_factor = data['energy_cost_factor']
        vehicle.payload_cost_factor = data['payload_cost_factor']
        vehicle.base_consumption_rate = data['base_consumption_rate']
        vehicle.low_battery_threshold = data['low_battery_threshold']
        
        return vehicle
    
    async def connect(self):
        """建立与车辆的WebSocket连接"""
        try:
            self.websocket = await websockets.connect(
                self.connection_info['websocket_url']
            )
            self.last_heartbeat = datetime.now()
            return True
        except Exception as e:
            self.error_message = f'连接失败: {str(e)}'
            return False
    
    async def disconnect(self):
        """断开与车辆的连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    async def send_command(self, command: Dict) -> bool:
        """发送命令到车辆"""
        if not self.websocket:
            return False
        
        try:
            await self.websocket.send(json.dumps(command))
            response = await self.websocket.recv()
            response_data = json.loads(response)
            return response_data.get('success', False)
        except Exception as e:
            self.error_message = f'发送命令失败: {str(e)}'
            return False
    
    async def assign_task(self, task: Dict, path: List[Dict]) -> bool:
        """分配任务给车辆"""
        # 根据车辆类型构造路径消息
        waypoints = []
        for point in path:
            waypoint = {
                'lat': point['lat'],
                'lon': point['lon']
            }
            # 如果是无人机，添加高度信息
            if self.type == VehicleType.DRONE:
                waypoint['alt'] = point.get('alt', 30.0)  # 默认飞行高度30米
            waypoints.append(waypoint)
        
        command = {
            'type': 'task',
            'task_id': task['id'],
            'task_type': task['type'],
            'waypoints': waypoints,
            'params': {
                'max_speed': 40.0 if self.type == VehicleType.CAR else 10.0,  # 车辆最大速度40km/h，无人机10m/s
                'min_speed': 5.0 if self.type == VehicleType.CAR else 2.0,  # 最小速度
                'acceleration': 2.0,  # 加速度
                'deceleration': 3.0,  # 减速度
                'path_tracking': {
                    'look_ahead_distance': 20.0 if self.type == VehicleType.CAR else 10.0,  # 前瞻距离
                    'max_cross_track_error': 10.0 if self.type == VehicleType.CAR else 5.0,  # 最大横向误差
                    'waypoint_radius': 5.0 if self.type == VehicleType.CAR else 2.0  # 航点到达判定半径
                }
            }
        }
        return await self.send_command(command)
    
    async def update_status(self) -> bool:
        """更新车辆状态"""
        if not self.websocket:
            self.status = VehicleStatus.OFFLINE
            return False
        
        command = {'type': 'get_status'}
        success = await self.send_command(command)
        
        if not success:
            self.status = VehicleStatus.ERROR
            return False
        
        return True

class VehicleManager:
    """车辆管理器"""
    def __init__(self):
        self.vehicles: Dict[str, Vehicle] = {}
        self.logger = logging.getLogger('VehicleManager')
    
    async def initialize(self):
        """初始化车辆管理器"""
        self.logger.info('车辆管理器初始化')
        
        # 启动心跳检测
        asyncio.create_task(self.heartbeat_loop())
    
    async def register_vehicle(
        self,
        vehicle_type: VehicleType,
        capabilities: List[str],
        max_payload: float,
        battery_capacity: float,
        connection_info: Dict
    ) -> Vehicle:
        """注册新车辆"""
        # 生成车辆ID
        vehicle_id = f'{vehicle_type.value.upper()}_{len(self.vehicles) + 1}'
        
        # 创建车辆对象
        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            capabilities=capabilities,
            max_payload=max_payload,
            battery_capacity=battery_capacity,
            connection_info=connection_info
        )
        
        # 建立连接
        if await vehicle.connect():
            self.vehicles[vehicle_id] = vehicle
            self.logger.info(f'注册新车辆: {vehicle_id}')
            return vehicle
        else:
            self.logger.error(f'注册车辆失败: {vehicle.error_message}')
            return None
    
    def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        """获取指定车辆"""
        return self.vehicles.get(vehicle_id)
    
    def get_all_vehicles(self) -> List[Vehicle]:
        """获取所有车辆"""
        return list(self.vehicles.values())
    
    def get_available_vehicles(self, required_capabilities: List[str]) -> List[Vehicle]:
        """获取可用的车辆"""
        return [
            vehicle for vehicle in self.vehicles.values()
            if vehicle.status == VehicleStatus.IDLE
            and all(cap in vehicle.capabilities for cap in required_capabilities)
        ]
    
    async def update_vehicle_status(self):
        """更新所有车辆状态"""
        for vehicle in self.vehicles.values():
            await vehicle.update_status()
    
    async def stop_all_vehicles(self):
        """停止所有车辆"""
        for vehicle in self.vehicles.values():
            command = {'type': 'stop'}
            await vehicle.send_command(command)
            await vehicle.disconnect()
    
    async def heartbeat_loop(self):
        """心跳检测循环"""
        while True:
            try:
                for vehicle in self.vehicles.values():
                    if vehicle.websocket:
                        try:
                            await vehicle.websocket.ping()
                            vehicle.last_heartbeat = datetime.now()
                        except:
                            vehicle.status = VehicleStatus.OFFLINE
                            await vehicle.disconnect()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f'心跳检测异常: {str(e)}')
                await asyncio.sleep(5)
    
    def serialize(self) -> Dict:
        """序列化车辆数据"""
        return {
            vehicle_id: vehicle.to_dict()
            for vehicle_id, vehicle in self.vehicles.items()
        }
    
    def deserialize(self, data: Dict):
        """反序列化车辆数据"""
        self.vehicles = {
            vehicle_id: Vehicle.from_dict(vehicle_data)
            for vehicle_id, vehicle_data in data.items()
        }