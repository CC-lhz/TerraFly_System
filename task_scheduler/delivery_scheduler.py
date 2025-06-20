from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from enum import Enum
import datetime
from .system_map_planner import SystemMapPlanner
from .flight_scheduler import FlightScheduler

class VehicleType(Enum):
    CAR = "car"
    DRONE = "drone"

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKUP_REACHED = "pickup_reached"
    PICKUP_COMPLETE = "pickup_complete"
    TRANSFER_STARTED = "transfer_started"
    TRANSFER_COMPLETE = "transfer_complete"
    DELIVERY_STARTED = "delivery_started"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DeliveryPoint:
    id: str
    location: Tuple[float, float]  # (latitude, longitude)
    type: str  # 'pickup', 'drone_station', 'delivery'

@dataclass
class DeliveryTask:
    id: str
    pickup_point: DeliveryPoint
    delivery_point: DeliveryPoint
    drone_station: Optional[DeliveryPoint] = None
    status: TaskStatus = TaskStatus.PENDING
    assigned_car_first_mile: Optional[str] = None  # 取货无人车ID
    assigned_drone: Optional[str] = None          # 无人机ID
    assigned_car_last_mile: Optional[str] = None  # 配送无人车ID
    created_time: datetime.datetime = datetime.datetime.now()

class DeliveryScheduler:
    def __init__(self, map_planner: BaiduMapPlanner, flight_scheduler: FlightScheduler):
        self.map_planner = map_planner
        self.flight_scheduler = flight_scheduler
        self.delivery_points: Dict[str, DeliveryPoint] = {}
        self.vehicles: Dict[str, dict] = {}  # 存储无人车和无人机信息
        self.tasks: Dict[str, DeliveryTask] = {}
        self.drone_stations: List[DeliveryPoint] = []

    def register_delivery_point(self, point: DeliveryPoint):
        """注册配送点（包括取货点、无人机起降点和配送点）"""
        self.delivery_points[point.id] = point
        if point.type == 'drone_station':
            self.drone_stations.append(point)

    def register_vehicle(self, vehicle_id: str, vehicle_type: VehicleType, 
                        location: Tuple[float, float], battery: float = 100.0):
        """注册无人车或无人机"""
        self.vehicles[vehicle_id] = {
            'type': vehicle_type,
            'location': location,
            'battery': battery,
            'status': 'idle'
        }

    def create_delivery_task(self, task_id: str, pickup_point_id: str, delivery_point_id: str) -> Optional[DeliveryTask]:
        """创建配送任务"""
        if pickup_point_id not in self.delivery_points or delivery_point_id not in self.delivery_points:
            return None

        # 找到最近的无人机起降点
        nearest_station = min(self.drone_stations,
            key=lambda x: self.map_planner.calculate_distance(x.location, self.delivery_points[pickup_point_id].location))

        task = DeliveryTask(
            id=task_id,
            pickup_point=self.delivery_points[pickup_point_id],
            delivery_point=self.delivery_points[delivery_point_id],
            drone_station=nearest_station
        )
        self.tasks[task_id] = task
        return task

    def find_nearest_available_vehicle(self, location: Tuple[float, float], 
                                     vehicle_type: VehicleType) -> Optional[str]:
        """查找最近的可用车辆"""
        available_vehicles = [
            (vid, vinfo) for vid, vinfo in self.vehicles.items()
            if vinfo['type'] == vehicle_type and vinfo['status'] == 'idle' and vinfo['battery'] > 30.0
        ]

        if not available_vehicles:
            return None

        return min(available_vehicles,
            key=lambda x: self.map_planner.calculate_distance(x[1]['location'], location))[0]

    def assign_first_mile_delivery(self, task: DeliveryTask) -> bool:
        """分配取货无人车"""
        vehicle_id = self.find_nearest_available_vehicle(task.pickup_point.location, VehicleType.CAR)
        if not vehicle_id:
            return False

        # 规划路径并分配任务
        path = self.map_planner.plan_path(
            start=self.vehicles[vehicle_id]['location'],
            goal=task.pickup_point.location,
            vehicle_type="driving"
        )
        if not path:
            return False

        task.assigned_car_first_mile = vehicle_id
        task.status = TaskStatus.ASSIGNED
        self.vehicles[vehicle_id]['status'] = 'busy'
        return True

    def assign_drone_delivery(self, task: DeliveryTask) -> bool:
        """分配无人机"""
        vehicle_id = self.find_nearest_available_vehicle(task.drone_station.location, VehicleType.DRONE)
        if not vehicle_id:
            return False

        # 规划航线
        flight_path = self.flight_scheduler.schedule_flight(
            drone_id=vehicle_id,
            start=task.drone_station.location,
            goal=task.delivery_point.location
        )
        if not flight_path:
            return False

        task.assigned_drone = vehicle_id
        task.status = TaskStatus.TRANSFER_STARTED
        self.vehicles[vehicle_id]['status'] = 'busy'
        return True

    def assign_last_mile_delivery(self, task: DeliveryTask) -> bool:
        """分配配送无人车"""
        vehicle_id = self.find_nearest_available_vehicle(task.delivery_point.location, VehicleType.CAR)
        if not vehicle_id:
            return False

        # 规划路径
        path = self.map_planner.plan_path(
            start=self.vehicles[vehicle_id]['location'],
            goal=task.delivery_point.location,
            vehicle_type="driving"
        )
        if not path:
            return False

        task.assigned_car_last_mile = vehicle_id
        task.status = TaskStatus.DELIVERY_STARTED
        self.vehicles[vehicle_id]['status'] = 'busy'
        return True

    def update_task_status(self, task_id: str, new_status: TaskStatus):
        """更新任务状态"""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        task.status = new_status

        # 根据状态变化触发下一步任务分配
        if new_status == TaskStatus.PICKUP_COMPLETE:
            self.assign_drone_delivery(task)
        elif new_status == TaskStatus.TRANSFER_COMPLETE:
            self.assign_last_mile_delivery(task)
        elif new_status == TaskStatus.COMPLETED:
            # 释放所有相关车辆
            for vehicle_id in [task.assigned_car_first_mile, 
                              task.assigned_drone,
                              task.assigned_car_last_mile]:
                if vehicle_id and vehicle_id in self.vehicles:
                    self.vehicles[vehicle_id]['status'] = 'idle'

    def update_vehicle_location(self, vehicle_id: str, location: Tuple[float, float]):
        """更新车辆位置"""
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]['location'] = location

    def update_vehicle_battery(self, vehicle_id: str, battery: float):
        """更新车辆电量"""
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]['battery'] = battery