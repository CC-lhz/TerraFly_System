from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import datetime
import json
import threading
from queue import PriorityQueue
from .baidu_map_planner import BaiduMapPlanner
from .flight_scheduler import FlightScheduler
from .delivery_scheduler import DeliveryPoint, VehicleType, TaskStatus

class Priority(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    EMERGENCY = 3

@dataclass
class Vehicle:
    id: str
    type: VehicleType
    location: Tuple[float, float]
    battery: float
    status: str
    payload_capacity: float
    current_payload: float
    last_updated: datetime.datetime
    capabilities: List[str]  # 特殊能力，如'night_vision', 'weather_resistant'
    maintenance_status: Dict[str, Any]  # 维护状态信息

@dataclass
class Task:
    id: str
    type: str  # 'delivery', 'patrol', 'inspection', etc.
    priority: Priority
    start_point: DeliveryPoint
    end_point: DeliveryPoint
    intermediate_points: List[DeliveryPoint]  # 中间点（如无人机起降点）
    status: TaskStatus
    assigned_vehicles: Dict[str, str]  # 阶段到车辆的映射
    payload_weight: float
    special_requirements: List[str]  # 特殊要求
    created_time: datetime.datetime
    deadline: Optional[datetime.datetime]
    completion_time: Optional[datetime.datetime]

class UnifiedScheduler:
    def __init__(self, config: dict):
        self.config = config
        self.map_planner = BaiduMapPlanner(
            center=config['map_center'],
            zoom_start=config['zoom_start'],
            ak=config['baidu_map_ak']
        )
        self.flight_scheduler = FlightScheduler()
        
        self.vehicles: Dict[str, Vehicle] = {}
        self.tasks: Dict[str, Task] = {}
        self.delivery_points: Dict[str, DeliveryPoint] = {}
        self.task_queue = PriorityQueue()
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # 状态监控
        self.status_monitor = threading.Thread(target=self._monitor_loop, daemon=True)
        self.status_monitor.start()

    def register_vehicle(self, vehicle: Vehicle) -> bool:
        """注册新车辆"""
        if vehicle.id in self.vehicles:
            return False
            
        self.vehicles[vehicle.id] = vehicle
        return True

    def register_delivery_point(self, point: DeliveryPoint) -> bool:
        """注册配送点"""
        if point.id in self.delivery_points:
            return False
            
        self.delivery_points[point.id] = point
        return True

    def create_task(self, task: Task) -> bool:
        """创建新任务"""
        if task.id in self.tasks:
            return False
            
        self.tasks[task.id] = task
        self.task_queue.put((-task.priority.value, task.created_time, task.id))
        return True

    def _find_suitable_vehicles(self, task: Task, stage: str) -> List[str]:
        """查找适合任务的车辆"""
        suitable_vehicles = []
        for vid, vehicle in self.vehicles.items():
            if vehicle.status != 'idle':
                continue
                
            if vehicle.battery < self.config['min_battery_level']:
                continue
                
            if vehicle.current_payload + task.payload_weight > vehicle.payload_capacity:
                continue
                
            # 检查特殊要求
            if not all(req in vehicle.capabilities for req in task.special_requirements):
                continue
                
            suitable_vehicles.append(vid)
            
        return suitable_vehicles

    def _calculate_task_cost(self, task: Task, vehicle_id: str, stage: str) -> float:
        """计算任务成本"""
        vehicle = self.vehicles[vehicle_id]
        
        # 距离成本
        distance_cost = self.map_planner.calculate_distance(
            vehicle.location,
            task.start_point.location if stage == 'pickup' else task.end_point.location
        )
        
        # 电量成本
        battery_cost = (100 - vehicle.battery) / 100
        
        # 时间成本
        time_cost = 0
        if task.deadline:
            remaining_time = (task.deadline - datetime.datetime.now()).total_seconds()
            time_cost = max(0, 1 - remaining_time / 3600)  # 1小时作为基准
            
        return distance_cost + battery_cost + time_cost

    def _assign_task(self, task: Task) -> bool:
        """分配任务给合适的车辆"""
        stages = ['pickup', 'transfer', 'delivery']
        for stage in stages:
            suitable_vehicles = self._find_suitable_vehicles(task, stage)
            if not suitable_vehicles:
                continue
                
            # 选择成本最低的车辆
            best_vehicle = min(suitable_vehicles,
                key=lambda vid: self._calculate_task_cost(task, vid, stage))
                
            task.assigned_vehicles[stage] = best_vehicle
            self.vehicles[best_vehicle].status = 'busy'
            
            # 规划路径
            if self.vehicles[best_vehicle].type == VehicleType.DRONE:
                self.flight_scheduler.schedule_flight(
                    drone_id=best_vehicle,
                    start=task.start_point.location,
                    goal=task.end_point.location
                )
            else:
                self.map_planner.plan_path(
                    start=self.vehicles[best_vehicle].location,
                    goal=task.start_point.location if stage == 'pickup' else task.end_point.location,
                    vehicle_type="driving"
                )
                
        return len(task.assigned_vehicles) == len(stages)

    def _scheduler_loop(self):
        """调度主循环"""
        while True:
            if not self.task_queue.empty():
                _, _, task_id = self.task_queue.get()
                task = self.tasks[task_id]
                
                if task.status == TaskStatus.PENDING:
                    if self._assign_task(task):
                        task.status = TaskStatus.ASSIGNED
                    else:
                        # 重新入队，等待后续调度
                        self.task_queue.put((-task.priority.value, datetime.datetime.now(), task_id))

    def _monitor_loop(self):
        """状态监控循环"""
        while True:
            current_time = datetime.datetime.now()
            
            # 检查车辆状态
            for vehicle in self.vehicles.values():
                if (current_time - vehicle.last_updated).total_seconds() > self.config['vehicle_timeout']:
                    vehicle.status = 'unknown'
                    
            # 检查任务截止时间
            for task in self.tasks.values():
                if task.deadline and current_time > task.deadline and task.status not in [
                    TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task.status = TaskStatus.FAILED

    def update_vehicle_status(self, vehicle_id: str, location: Tuple[float, float],
                            battery: float, status: str, current_payload: float):
        """更新车辆状态"""
        if vehicle_id not in self.vehicles:
            return
            
        vehicle = self.vehicles[vehicle_id]
        vehicle.location = location
        vehicle.battery = battery
        vehicle.status = status
        vehicle.current_payload = current_payload
        vehicle.last_updated = datetime.datetime.now()

    def update_task_status(self, task_id: str, new_status: TaskStatus,
                          completion_time: Optional[datetime.datetime] = None):
        """更新任务状态"""
        if task_id not in self.tasks:
            return
            
        task = self.tasks[task_id]
        task.status = new_status
        
        if new_status == TaskStatus.COMPLETED:
            task.completion_time = completion_time or datetime.datetime.now()
            # 释放相关车辆
            for vehicle_id in task.assigned_vehicles.values():
                if vehicle_id in self.vehicles:
                    self.vehicles[vehicle_id].status = 'idle'

    def get_system_status(self) -> dict:
        """获取系统状态概览"""
        return {
            'vehicles': {
                'total': len(self.vehicles),
                'idle': sum(1 for v in self.vehicles.values() if v.status == 'idle'),
                'busy': sum(1 for v in self.vehicles.values() if v.status == 'busy'),
                'unknown': sum(1 for v in self.vehicles.values() if v.status == 'unknown')
            },
            'tasks': {
                'total': len(self.tasks),
                'pending': sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
                'in_progress': sum(1 for t in self.tasks.values() if t.status in [
                    TaskStatus.ASSIGNED, TaskStatus.PICKUP_REACHED, TaskStatus.TRANSFER_STARTED]),
                'completed': sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                'failed': sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
            },
            'delivery_points': len(self.delivery_points)
        }

    def save_state(self, filename: str):
        """保存系统状态到文件"""
        state = {
            'vehicles': {vid: vars(v) for vid, v in self.vehicles.items()},
            'tasks': {tid: vars(t) for tid, t in self.tasks.items()},
            'delivery_points': {pid: vars(p) for pid, p in self.delivery_points.items()}
        }
        with open(filename, 'w') as f:
            json.dump(state, f, default=str)

    def load_state(self, filename: str):
        """从文件加载系统状态"""
        with open(filename, 'r') as f:
            state = json.load(f)
            
        self.vehicles = {}
        self.tasks = {}
        self.delivery_points = {}
        
        for vid, vdata in state['vehicles'].items():
            self.vehicles[vid] = Vehicle(**vdata)
            
        for tid, tdata in state['tasks'].items():
            self.tasks[tid] = Task(**tdata)
            
        for pid, pdata in state['delivery_points'].items():
            self.delivery_points[pid] = DeliveryPoint(**pdata)