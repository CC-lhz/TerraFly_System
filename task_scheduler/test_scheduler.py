import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from master_computer.scheduler import MasterScheduler
from master_computer.task_manager import Task, TaskPriority
from master_computer.vehicle_manager import Vehicle, VehicleType
from master_computer.delivery_manager import DeliveryPoint
from master_computer.map_manager import MapManager, PathType

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchedulerTester:
    def __init__(self):
        self.scheduler = MasterScheduler()
        self.vehicles: Dict[str, Vehicle] = {}
        self.delivery_points: Dict[str, DeliveryPoint] = {}
        
    async def initialize(self):
        """初始化测试环境"""
        await self.scheduler.initialize()
        await self.setup_vehicles()
        await self.setup_delivery_points()
    
    async def setup_vehicles(self):
        """设置测试用车辆"""
        # 创建3辆无人车，位置分散在不同区域
        car_locations = [
            {'lat': 39.90, 'lon': 116.30},  # 西部
            {'lat': 39.95, 'lon': 116.35},  # 中部
            {'lat': 39.92, 'lon': 116.40}   # 东部
        ]
        for i in range(3):
            car = Vehicle(
                vehicle_id=f'CAR_{i+1}',
                vehicle_type=VehicleType.CAR,
                capabilities=['ground_delivery'],
                max_payload=100.0,
                location=car_locations[i],
                connection_info={
                    'host': 'localhost',
                    'port': 8000 + i
                }
            )
            self.scheduler.vehicle_manager.register_vehicle(car)
            self.vehicles[car.id] = car
            logger.info(f'注册无人车: {car.id}, 位置: {car.location}')
        
        # 创建3架无人机，位置分散在不同区域
        drone_locations = [
            {'lat': 39.88, 'lon': 116.32},  # 西南
            {'lat': 39.93, 'lon': 116.37},  # 中部
            {'lat': 39.91, 'lon': 116.42}   # 东部
        ]
        for i in range(3):
            drone = Vehicle(
                vehicle_id=f'DRONE_{i+1}',
                vehicle_type=VehicleType.DRONE,
                capabilities=['air_delivery'],
                max_payload=5.0,
                location=drone_locations[i],
                connection_info={
                    'host': 'localhost',
                    'port': 9000 + i
                }
            )
            self.scheduler.vehicle_manager.register_vehicle(drone)
            self.vehicles[drone.id] = drone
            logger.info(f'注册无人机: {drone.id}, 位置: {drone.location}')

    
    async def setup_delivery_points(self):
        """设置测试用配送点"""
        # 创建2个起降点，分别位于城市不同区域
        points = [
            DeliveryPoint(
                location={'lat': 39.92, 'lon': 116.34},  # 西部中心
                capacity=10,
                capabilities=['ground_delivery', 'air_delivery']
            ),
            DeliveryPoint(
                location={'lat': 39.90, 'lon': 116.38},  # 东部中心
                capacity=10,
                capabilities=['ground_delivery', 'air_delivery']
            )
        ]
        
        for point in points:
            self.scheduler.delivery_manager.register_delivery_point(point)
            self.delivery_points[point.id] = point
            logger.info(f'注册配送点: {point.id}, 位置: {point.location}')
    
    async def create_test_tasks(self):
        """创建测试任务"""
        points = list(self.delivery_points.values())
        
        # 创建多个不同类型和优先级的任务
        tasks_data = [
            # 紧急空运任务
            Task(
                weight=2.5,
                priority=TaskPriority.URGENT,
                required_capabilities=['air_delivery'],
                pickup_point=points[0],
                delivery_point=points[1],
                deadline=datetime.now() + timedelta(minutes=30)
            ),
            # 重型地面运输
            Task(
                weight=90.0,
                priority=TaskPriority.HIGH,
                required_capabilities=['ground_delivery'],
                pickup_point=points[1],
                delivery_point=points[0],
                deadline=datetime.now() + timedelta(hours=1)
            ),
            # 中等优先级空运
            Task(
                weight=4.0,
                priority=TaskPriority.NORMAL,
                required_capabilities=['air_delivery'],
                pickup_point=points[0],
                delivery_point=points[1],
                deadline=datetime.now() + timedelta(hours=2)
            ),
            # 普通地面运输
            Task(
                weight=60.0,
                priority=TaskPriority.NORMAL,
                required_capabilities=['ground_delivery'],
                pickup_point=points[1],
                delivery_point=points[0],
                deadline=datetime.now() + timedelta(hours=3)
            )
        ]
        
        for task in tasks_data:
            self.scheduler.task_manager.add_task(task)
            logger.info(
                f'创建任务: {task.id}, '
                f'类型: {", ".join(task.required_capabilities)}, '
                f'优先级: {task.priority.name}, '
                f'重量: {task.weight}kg'
            )
    
    async def run_test(self):
        """运行测试"""
        try:
            # 初始化
            logger.info('开始调度系统测试')
            await self.initialize()
            
            # 创建测试任务
            await self.create_test_tasks()
            
            # 运行调度器
            logger.info('启动调度器')
            scheduler_task = asyncio.create_task(self.scheduler.run())
            
            # 等待一段时间观察调度结果
            await asyncio.sleep(30)
            
            # 获取调度状态
            tasks = self.scheduler.task_manager.get_all_tasks()
            vehicles = self.scheduler.vehicle_manager.get_all_vehicles()
            
            # 输出状态信息
            logger.info('\n调度测试结果:')
            logger.info('任务状态:')
            for task in tasks:
                logger.info(f'任务 {task.id}: {task.status.value}')
            
            logger.info('\n车辆状态:')
            for vehicle in vehicles:
                logger.info(
                    f'车辆 {vehicle.id}: {vehicle.status.value}, '
                    f'当前任务: {vehicle.current_task}')
            
            # 停止调度器
            scheduler_task.cancel()
            logger.info('测试完成')
            
        except Exception as e:
            logger.error(f'测试过程出错: {str(e)}')
        finally:
            # 清理资源
            await self.scheduler.cleanup()

if __name__ == '__main__':
    # 运行测试
    tester = SchedulerTester()
    asyncio.run(tester.run_test())