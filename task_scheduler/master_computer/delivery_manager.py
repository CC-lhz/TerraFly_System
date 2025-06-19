from typing import Dict, List, Optional
from datetime import datetime
import logging
from enum import Enum

class DeliveryPointStatus(Enum):
    """配送点状态"""
    AVAILABLE = 'available'
    BUSY = 'busy'
    MAINTENANCE = 'maintenance'
    OFFLINE = 'offline'

class DeliveryPoint:
    """配送点类"""
    def __init__(
        self,
        point_id: str,
        location: Dict,
        capacity: int,
        capabilities: List[str]
    ):
        self.id = point_id
        self.location = location  # {'lat': float, 'lon': float, 'alt': float}
        self.capacity = capacity  # 最大容量
        self.capabilities = capabilities  # 支持的服务类型
        
        self.status = DeliveryPointStatus.AVAILABLE
        self.current_load = 0  # 当前负载
        self.pending_tasks = []  # 待处理任务
        self.completed_tasks = []  # 已完成任务
        self.last_update = datetime.now()
        self.error_message = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'location': self.location,
            'capacity': self.capacity,
            'capabilities': self.capabilities,
            'status': self.status.value,
            'current_load': self.current_load,
            'pending_tasks': self.pending_tasks,
            'completed_tasks': self.completed_tasks,
            'last_update': self.last_update.isoformat(),
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DeliveryPoint':
        """从字典创建配送点对象"""
        point = cls(
            point_id=data['id'],
            location=data['location'],
            capacity=data['capacity'],
            capabilities=data['capabilities']
        )
        
        point.status = DeliveryPointStatus(data['status'])
        point.current_load = data['current_load']
        point.pending_tasks = data['pending_tasks']
        point.completed_tasks = data['completed_tasks']
        point.last_update = datetime.fromisoformat(data['last_update'])
        point.error_message = data['error_message']
        
        return point
    
    def can_handle_task(self, task) -> bool:
        """检查是否可以处理任务"""
        # 检查状态
        if self.status != DeliveryPointStatus.AVAILABLE:
            return False
        
        # 检查容量
        if self.current_load >= self.capacity:
            return False
        
        # 检查能力
        if not all(cap in self.capabilities for cap in task.required_capabilities):
            return False
        
        return True
    
    def add_pending_task(self, task_id: str) -> bool:
        """添加待处理任务"""
        if self.current_load < self.capacity:
            self.pending_tasks.append(task_id)
            self.current_load += 1
            return True
        return False
    
    def complete_task(self, task_id: str) -> bool:
        """完成任务"""
        if task_id in self.pending_tasks:
            self.pending_tasks.remove(task_id)
            self.completed_tasks.append(task_id)
            self.current_load -= 1
            return True
        return False

class DeliveryManager:
    """配送点管理器"""
    def __init__(self):
        self.delivery_points: Dict[str, DeliveryPoint] = {}
        self.drone_stations: Dict[str, DeliveryPoint] = {}  # 无人机起降点
        self.logger = logging.getLogger('DeliveryManager')
    
    async def initialize(self):
        """初始化配送点管理器"""
        self.logger.info('配送点管理器初始化')
        
    def register_drone_station(self, location: Dict, capacity: int = 5) -> DeliveryPoint:
        """注册无人机起降点
        Args:
            location: 位置信息 {'lat': float, 'lon': float, 'alt': float}
            capacity: 最大停机数量
        """
        station_id = f'STATION_{len(self.drone_stations) + 1}'
        station = DeliveryPoint(
            point_id=station_id,
            location=location,
            capacity=capacity,
            capabilities=['drone_landing']
        )
        self.drone_stations[station_id] = station
        self.logger.info(f'注册无人机起降点: {station_id}')
        return station
    
    def register_delivery_point(
        self,
        location: Dict,
        capacity: int,
        capabilities: List[str]
    ) -> DeliveryPoint:
        """注册新配送点"""
        # 生成配送点ID
        point_id = f'POINT_{len(self.delivery_points) + 1}'
        
        # 创建配送点对象
        point = DeliveryPoint(
            point_id=point_id,
            location=location,
            capacity=capacity,
            capabilities=capabilities
        )
        
        # 添加到配送点列表
        self.delivery_points[point_id] = point
        
        self.logger.info(f'注册新配送点: {point_id}')
        return point
    
    def get_delivery_point(self, point_id: str) -> Optional[DeliveryPoint]:
        """获取指定配送点"""
        return self.delivery_points.get(point_id)
    
    def get_all_delivery_points(self) -> List[DeliveryPoint]:
        """获取所有配送点"""
        return list(self.delivery_points.values())
    
    def get_available_points(self, required_capabilities: List[str]) -> List[DeliveryPoint]:
        """获取可用的配送点"""
        return [
            point for point in self.delivery_points.values()
            if point.status == DeliveryPointStatus.AVAILABLE
            and point.current_load < point.capacity
            and all(cap in point.capabilities for cap in required_capabilities)
        ]
    
    def find_nearest_point(
        self,
        location: Dict,
        required_capabilities: List[str]
    ) -> Optional[DeliveryPoint]:
        """查找最近的可用配送点"""
        available_points = self.get_available_points(required_capabilities)
        if not available_points:
            return None
        
        # 计算距离并排序
        def calculate_distance(point):
            lat_diff = point.location['lat'] - location['lat']
            lon_diff = point.location['lon'] - location['lon']
            return (lat_diff ** 2 + lon_diff ** 2) ** 0.5
        
        return min(available_points, key=calculate_distance)
    
    async def update_delivery_points(self):
        """更新配送点状态"""
        for point in self.delivery_points.values():
            # 更新状态
            if point.current_load >= point.capacity:
                point.status = DeliveryPointStatus.BUSY
            elif point.status != DeliveryPointStatus.MAINTENANCE:
                point.status = DeliveryPointStatus.AVAILABLE
            
            point.last_update = datetime.now()
    
    def update_delivery_status(self, task) -> bool:
        """更新任务相关的配送点状态"""
        # 更新取货点
        pickup_point = self.delivery_points.get(task.pickup_point['id'])
        if pickup_point:
            pickup_point.complete_task(task.id)
        
        # 更新配送点
        delivery_point = self.delivery_points.get(task.delivery_point['id'])
        if delivery_point:
            delivery_point.complete_task(task.id)
        
        # 更新无人机起降点状态
        if task.drone_station and task.drone_station['id'] in self.drone_stations:
            station = self.drone_stations[task.drone_station['id']]
            station.complete_task(task.id)
        
        return True
    
    def plan_delivery_route(self, task, map_manager) -> Dict:
        """规划配送路线
        返回三段式配送路线：
        1. 无人车取货路线（取货点 -> 起降点）
        2. 无人机配送路线（起降点 -> 目标区域起降点）
        3. 无人车配送路线（起降点 -> 配送点）
        """
        # 找到最近的起降点（取货点附近）
        pickup_station = min(
            self.drone_stations.values(),
            key=lambda x: map_manager.calculate_distance(x.location, task.pickup_point['location'])
        )
        
        # 找到最近的起降点（配送点附近）
        delivery_station = min(
            self.drone_stations.values(),
            key=lambda x: map_manager.calculate_distance(x.location, task.delivery_point['location'])
        )
        
        # 规划路线
        routes = {
            'first_mile': map_manager.plan_car_path(
                start=task.pickup_point['location'],
                end=pickup_station.location
            ),
            'air_route': map_manager.plan_air_path(
                start=pickup_station.location,
                end=delivery_station.location
            ),
            'last_mile': map_manager.plan_car_path(
                start=delivery_station.location,
                end=task.delivery_point['location']
            ),
            'stations': {
                'pickup': pickup_station.id,
                'delivery': delivery_station.id
            }
        }
        
        return routes
    
    def serialize(self) -> Dict:
        """序列化配送点数据"""
        return {
            point_id: point.to_dict()
            for point_id, point in self.delivery_points.items()
        }
    
    def deserialize(self, data: Dict):
        """反序列化配送点数据"""
        self.delivery_points = {
            point_id: DeliveryPoint.from_dict(point_data)
            for point_id, point_data in data.items()
        }