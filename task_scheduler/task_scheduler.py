import asyncio
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import math
from map_planner import MapPlanner
from flight_scheduler import FlightScheduler, FlightPath

@dataclass
class Vehicle:
    id: str
    type: str  # 'drone' or 'car'
    location: Tuple[float, float]  # (latitude, longitude)
    status: str  # 'idle', 'busy', 'charging'
    battery_level: float
    max_payload: float
    current_payload: float
    altitude: float = 0.0  # 当前高度（仅用于无人机）

@dataclass
class Task:
    id: str
    pickup: Tuple[float, float]  # (latitude, longitude)
    delivery: Tuple[float, float]  # (latitude, longitude)
    weight: float
    priority: int  # 1-5, 5 being highest
    created_at: datetime
    task_type: str = 'delivery'  # 'delivery' or 'resupply'
    assigned_to: str = None
    support_vehicle: str = None  # 支援车辆ID
    status: str = 'pending'  # 'pending', 'assigned', 'in_progress', 'completed', 'need_resupply'
    path: List[Tuple[float, float]] = None  # 规划的路径
    flight_path: FlightPath = None  # 航线信息（仅用于无人机）

class TaskScheduler:
    def __init__(self):
        self.vehicles: Dict[str, Vehicle] = {}
        self.tasks: Dict[str, Task] = {}
        self.map_planner = MapPlanner(center=(22.5, 113.4), zoom_start=13)
        self.flight_scheduler = FlightScheduler()

    def register_vehicle(self, vehicle: Vehicle):
        """注册新的运输工具（无人机或无人车）"""
        self.vehicles[vehicle.id] = vehicle
        # 在地图上添加标记
        color = 'red' if vehicle.type == 'drone' else 'blue'
        self.map_planner.map.add_child(folium.Marker(
            location=vehicle.location,
            popup=f"{vehicle.type.upper()} - {vehicle.id}",
            icon=folium.Icon(color=color)
        ))

    def add_task(self, task: Task):
        """添加新的配送任务"""
        self.tasks[task.id] = task
        # 在地图上显示任务起点和终点
        self.map_planner.map.add_child(folium.Marker(
            location=task.pickup,
            popup=f"Pickup - {task.id}",
            icon=folium.Icon(color='green')
        ))
        self.map_planner.map.add_child(folium.Marker(
            location=task.delivery,
            popup=f"Delivery - {task.id}",
            icon=folium.Icon(color='orange')
        ))

    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """计算两点间的距离（公里）"""
        return self.map_planner.calculate_distance(point1, point2)

    def get_suitable_vehicles(self, task: Task) -> List[Vehicle]:
        """获取适合执行任务的运输工具列表"""
        suitable = []
        for vehicle in self.vehicles.values():
            if (vehicle.status == 'idle' and
                vehicle.battery_level > 30 and
                vehicle.max_payload >= task.weight):
                suitable.append(vehicle)
        return suitable

    def find_nearest_support_vehicle(self, drone_location: Tuple[float, float]) -> Vehicle:
        """查找最近的可用支援车辆"""
        available_cars = [v for v in self.vehicles.values()
                         if v.type == 'car' and v.status == 'idle']
        if not available_cars:
            return None
            
        distances = [(car, self.calculate_distance(drone_location, car.location))
                    for car in available_cars]
        return min(distances, key=lambda x: x[1])[0]

    def create_resupply_task(self, drone: Vehicle, support_car: Vehicle) -> Task:
        """创建补给任务"""
        task_id = f'resupply_{drone.id}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
        return Task(
            id=task_id,
            pickup=support_car.location,
            delivery=drone.location,
            weight=0,  # 补给任务不计重量
            priority=5,  # 补给任务优先级最高
            created_at=datetime.now(),
            task_type='resupply',
            assigned_to=support_car.id,
            support_vehicle=drone.id
        )

    def plan_route(self, vehicle: Vehicle, start: Tuple[float, float], end: Tuple[float, float]) -> List[Tuple[float, float]]:
        """根据车辆类型规划路线"""
        if vehicle.type == 'drone':
            return self.map_planner.a_star_path(start, end)
        else:  # car
            return self.map_planner.rrt_path(start, end)

    def schedule_drone_flight(self, drone_id: str, path: List[Tuple[float, float]], priority: int) -> bool:
        """为无人机调度航线"""
        start_time = datetime.now() + timedelta(seconds=10)  # 预留10秒准备时间
        return self.flight_scheduler.schedule_flight(drone_id, path, start_time, priority)

    def assign_task(self, task: Task) -> bool:
        """为任务分配最合适的运输工具"""
        if task.task_type == 'delivery':
            # 优先分配给无人机
            suitable_drones = [v for v in self.vehicles.values()
                              if v.type == 'drone' and v.status == 'idle'
                              and v.battery_level > 30 and v.max_payload >= task.weight]
            
            if suitable_drones:
                # 计算每个无人机到取货点的距离
                distances = []
                for drone in suitable_drones:
                    distance = self.calculate_distance(drone.location, task.pickup)
                    total_distance = distance + self.calculate_distance(task.pickup, task.delivery)
                    distances.append((drone, total_distance))

                # 选择距离最近的无人机
                best_drone, _ = min(distances, key=lambda x: x[1])
                
                # 规划路径
                pickup_path = self.plan_route(best_drone, best_drone.location, task.pickup)
                delivery_path = self.plan_route(best_drone, task.pickup, task.delivery)
                task.path = pickup_path + delivery_path[1:]  # 合并路径，避免重复点
                
                # 调度航线
                if not self.schedule_drone_flight(best_drone.id, task.path, task.priority):
                    print(f"无人机 {best_drone.id} 航线调度失败，尝试其他无人机")
                    return False
                
                # 更新任务和无人机状态
                task.assigned_to = best_drone.id
                task.status = 'assigned'
                best_drone.status = 'busy'

                # 在地图上显示规划的路径
                self.map_planner.draw_path(task.path, color='red')
                return True
            
            # 如果没有合适的无人机，尝试分配给无人车
            suitable_cars = [v for v in self.vehicles.values()
                            if v.type == 'car' and v.status == 'idle'
                            and v.max_payload >= task.weight]
            
            if suitable_cars:
                best_car = min(suitable_cars,
                              key=lambda x: self.calculate_distance(x.location, task.pickup))
                
                # 规划路径
                pickup_path = self.plan_route(best_car, best_car.location, task.pickup)
                delivery_path = self.plan_route(best_car, task.pickup, task.delivery)
                task.path = pickup_path + delivery_path[1:]  # 合并路径，避免重复点
                
                task.assigned_to = best_car.id
                task.status = 'assigned'
                best_car.status = 'busy'
                
                # 在地图上显示规划的路径
                self.map_planner.draw_path(task.path, color='blue')
                return True
                
            return False
            
        elif task.task_type == 'resupply':
            # 补给任务直接分配给指定的支援车辆
            support_car = self.vehicles[task.assigned_to]
            support_car.status = 'busy'
            
            # 规划补给路径
            task.path = self.plan_route(support_car, support_car.location, task.delivery)
            self.map_planner.draw_path(task.path, color='green')
            return True
            
        return False

    def save_map(self, filename: str = 'delivery_map.html'):
        """保存当前地图状态到HTML文件"""
        self.map_planner.save_map(filename)

    def update_vehicle_status(self, vehicle_id: str, status: str, location: Tuple[float, float], altitude: float = None):
        """更新车辆状态和位置"""
        if vehicle_id in self.vehicles:
            vehicle = self.vehicles[vehicle_id]
            vehicle.status = status
            vehicle.location = location
            if altitude is not None and vehicle.type == 'drone':
                vehicle.altitude = altitude
                self.flight_scheduler.update_flight_status(vehicle_id, status)

    async def run_scheduler(self):
        """运行任务调度器"""
        while True:
            # 检查所有运行中的无人机电量
            for vehicle in self.vehicles.values():
                if (vehicle.type == 'drone' and 
                    vehicle.status == 'busy' and 
                    vehicle.battery_level < 30):
                    # 寻找最近的支援车辆
                    support_car = self.find_nearest_support_vehicle(vehicle.location)
                    if support_car:
                        # 创建补给任务
                        resupply_task = self.create_resupply_task(vehicle, support_car)
                        self.add_task(resupply_task)
                        vehicle.status = 'need_resupply'
                        print(f"无人机 {vehicle.id} 电量低，创建补给任务 {resupply_task.id}")
            
            # 处理待分配的任务
            pending_tasks = [task for task in self.tasks.values()
                           if task.status == 'pending']
            
            # 按优先级排序，补给任务优先
            pending_tasks.sort(key=lambda x: (-x.priority, 
                                            0 if x.task_type == 'resupply' else 1,
                                            x.created_at))
            
            for task in pending_tasks:
                if self.assign_task(task):
                    print(f"{task.task_type}任务 {task.id} 已分配给 {task.assigned_to}")
                    if task.task_type == 'resupply':
                        print(f"支援无人机: {task.support_vehicle}")
                else:
                    print(f"任务 {task.id} 暂时无法分配")
            
            # 更新地图
            self.save_map()
            await asyncio.sleep(10)  # 每10秒检查一次

# 使用示例
async def main():
    scheduler = TaskScheduler()
    
    # 添加一些障碍物
    scheduler.map_planner.add_obstacle(22.51, 113.41, 200, 100)
    scheduler.map_planner.add_obstacle(22.49, 113.39, 150, 80)
    
    # 注册运输工具
    drone1 = Vehicle('drone1', 'drone', (22.5, 113.4), 'idle', 90, 5.0, 0)
    drone2 = Vehicle('drone2', 'drone', (22.51, 113.41), 'idle', 85, 5.0, 0)
    car1 = Vehicle('car1', 'car', (22.49, 113.39), 'idle', 70, 20.0, 0)
    
    scheduler.register_vehicle(drone1)
    scheduler.register_vehicle(drone2)
    scheduler.register_vehicle(car1)
    
    # 添加任务
    task1 = Task('task1', (22.52, 113.42), (22.48, 113.38), 2.5, 3,
                 datetime.now())
    task2 = Task('task2', (22.51, 113.40), (22.49, 113.41), 15.0, 4,
                 datetime.now())
    
    scheduler.add_task(task1)
    scheduler.add_task(task2)
    
    # 运行调度器
    await scheduler.run_scheduler()

if __name__ == "__main__":
    asyncio.run(main())