import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import json
import logging

from .task_manager import TaskManager
from .vehicle_manager import VehicleManager
from .delivery_manager import DeliveryManager
from .map_manager import MapManager

class MasterScheduler:
    """主控电脑调度器，负责全局任务分配和协调"""
    
    def __init__(self):
        self.task_manager = TaskManager()
        self.vehicle_manager = VehicleManager()
        self.delivery_manager = DeliveryManager()
        self.map_manager = MapManager()
        
        self.running = False
        self.logger = logging.getLogger('MasterScheduler')
    
    async def initialize(self):
        """初始化调度器"""
        try:
            # 初始化各个管理器
            await self.task_manager.initialize()
            await self.vehicle_manager.initialize()
            await self.delivery_manager.initialize()
            await self.map_manager.initialize()
            
            # 加载历史状态
            self.load_state()
            
            self.logger.info('调度器初始化完成')
            return True
        except Exception as e:
            self.logger.error(f'调度器初始化失败: {str(e)}')
            return False
    
    async def start(self):
        """启动调度器"""
        if self.running:
            return
        
        self.running = True
        self.logger.info('调度器启动')
        
        # 启动主调度循环
        asyncio.create_task(self.schedule_loop())
        
        # 启动状态监控循环
        asyncio.create_task(self.monitor_loop())
    
    async def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info('调度器停止')
        
        # 保存当前状态
        self.save_state()
        
        # 停止所有车辆
        await self.vehicle_manager.stop_all_vehicles()
    
    async def schedule_loop(self):
        """主调度循环"""
        while self.running:
            try:
                # 获取待分配的任务
                pending_tasks = self.task_manager.get_pending_tasks()
                
                for task in pending_tasks:
                    # 获取可用车辆
                    available_vehicles = self.vehicle_manager.get_available_vehicles(
                        task.required_capabilities
                    )
                    
                    if not available_vehicles:
                        continue
                    
                    # 选择最优车辆
                    best_vehicle = self.select_best_vehicle(task, available_vehicles)
                    
                    if best_vehicle:
                        # 分配任务
                        await self.assign_task(task, best_vehicle)
                
                # 更新任务状态
                self.task_manager.update_task_status()
                
                # 检查任务完成情况
                self.check_completed_tasks()
                
                await asyncio.sleep(1)  # 调度间隔
                
            except Exception as e:
                self.logger.error(f'调度循环异常: {str(e)}')
                await asyncio.sleep(5)  # 出错后等待较长时间
    
    async def monitor_loop(self):
        """状态监控循环"""
        while self.running:
            try:
                # 更新车辆状态
                await self.vehicle_manager.update_vehicle_status()
                
                # 更新配送点状态
                await self.delivery_manager.update_delivery_points()
                
                # 检查异常情况
                self.check_anomalies()
                
                # 更新地图显示
                self.map_manager.update_display()
                
                await asyncio.sleep(0.5)  # 监控间隔
                
            except Exception as e:
                self.logger.error(f'监控循环异常: {str(e)}')
                await asyncio.sleep(5)
    
    def select_best_vehicle(self, task, available_vehicles):
        """选择最优车辆执行任务
        考虑因素：
        1. 车辆类型是否匹配当前任务阶段
        2. 车辆位置与任务起点的距离
        3. 车辆电量
        4. 负载能力
        5. 历史任务完成情况
        """
        best_vehicle = None
        min_cost = float('inf')
        
        for vehicle in available_vehicles:
            # 检查车辆类型是否匹配任务阶段
            if task.status == TaskStatus.PENDING and vehicle.type != 'car':
                continue  # 第一段必须使用无人车
            if task.status == TaskStatus.PICKUP and vehicle.type != 'drone':
                continue  # 第二段必须使用无人机
            if task.status == TaskStatus.DELIVERING and vehicle.type != 'car':
                continue  # 第三段必须使用无人车
            
            # 计算任务执行成本
            cost = self.calculate_task_cost(task, vehicle)
            
            if cost < min_cost:
                min_cost = cost
                best_vehicle = vehicle
        
        return best_vehicle
    
    def calculate_task_cost(self, task, vehicle):
        """计算任务执行成本
        考虑不同类型车辆的特性和任务阶段
        """
        cost = 0
        
        # 获取当前阶段的路线
        routes = self.delivery_manager.plan_delivery_route(task, self.map_manager)
        if not routes:
            return float('inf')
        
        if vehicle.type == 'car':
            if task.status == TaskStatus.PENDING:
                path = routes['first_mile']
            else:
                path = routes['last_mile']
        else:  # drone
            path = routes['air_route']
        
        # 距离成本
        distance = self.map_manager.calculate_path_length(path)
        cost += distance * vehicle.distance_cost_factor
        
        # 时间成本
        if vehicle.type == 'car':
            estimated_time = distance / 40.0  # 无人车平均速度40km/h
        else:
            estimated_time = distance / 10.0  # 无人机平均速度10m/s
            # 考虑起降时间
            estimated_time += 60  # 预估起降各需要30秒
        
        if task.deadline:
            time_to_deadline = (task.deadline - datetime.now()).total_seconds()
            if estimated_time > time_to_deadline:
                return float('inf')  # 无法在截止时间前完成
            else:
                cost += estimated_time * vehicle.time_cost_factor
        
        # 电量成本
        if vehicle.type == 'car':
            energy_consumption = distance * 0.1  # 每公里消耗10%电量
        else:
            energy_consumption = distance * 0.2  # 每公里消耗20%电量
            energy_consumption += 10  # 起降额外消耗10%电量
        
        if energy_consumption > vehicle.battery_level:
            return float('inf')  # 电量不足
        else:
            cost += energy_consumption * vehicle.energy_cost_factor
        
        # 负载成本
        if task.weight > vehicle.max_payload:
            return float('inf')  # 超出最大负载
        else:
            cost += (task.weight / vehicle.max_payload) * vehicle.payload_cost_factor
        
        # 历史任务成本
        completed_tasks = len([t for t in self.task_manager.get_completed_tasks()
                              if t.assigned_vehicle == vehicle.id])
        cost -= completed_tasks * 0.1  # 每完成一个任务减少0.1的成本，鼓励使用可靠的车辆
        
        return cost
    
    def estimate_energy_consumption(self, vehicle, distance, weight):
        """估算能量消耗"""
        base_consumption = distance * vehicle.base_consumption_rate
        weight_factor = 1 + (weight / vehicle.max_payload) * 0.5
        return base_consumption * weight_factor
    
    async def assign_task(self, task, vehicle):
        """分配任务给车辆"""
        try:
            # 规划配送路线
            routes = self.delivery_manager.plan_delivery_route(task, self.map_manager)
            if not routes:
                self.logger.error(f'任务 {task.id} 路线规划失败')
                return False
            
            # 根据车辆类型分配不同的路线
            if vehicle.type == 'car':
                if task.status == TaskStatus.PENDING:
                    # 第一段：取货点 -> 起降点
                    path = routes['first_mile']
                    task.status = TaskStatus.PICKUP
                else:
                    # 第三段：起降点 -> 配送点
                    path = routes['last_mile']
                    task.status = TaskStatus.DELIVERING
            else:  # drone
                # 第二段：起降点 -> 起降点（空中配送）
                path = routes['air_route']
                task.status = TaskStatus.DELIVERING
            
            # 更新任务状态
            task.assigned_vehicle = vehicle.id
            task.assigned_time = datetime.now()
            
            # 更新车辆状态
            vehicle.status = 'busy'
            vehicle.current_task = task.id
            
            # 规划路径
            path = await self.map_manager.plan_path(
                vehicle.location,
                task.pickup_point,
                task.delivery_point
            )
            
            # 发送任务指令到车辆
            success = await vehicle.assign_task(task, path)
            
            if success:
                self.logger.info(
                    f'任务 {task.id} 已分配给车辆 {vehicle.id}'
                )
                return True
            else:
                # 分配失败，恢复状态
                task.status = 'pending'
                task.assigned_vehicle = None
                task.assigned_time = None
                vehicle.status = 'idle'
                vehicle.current_task = None
                return False
                
        except Exception as e:
            self.logger.error(f'任务分配失败: {str(e)}')
            return False
    
    def check_completed_tasks(self):
        """检查已完成的任务"""
        completed_tasks = self.task_manager.get_completed_tasks()
        
        for task in completed_tasks:
            # 释放车辆资源
            vehicle = self.vehicle_manager.get_vehicle(task.assigned_vehicle)
            if vehicle:
                vehicle.status = 'idle'
                vehicle.current_task = None
            
            # 更新配送点状态
            self.delivery_manager.update_delivery_status(task)
            
            self.logger.info(f'任务 {task.id} 已完成')
    
    def check_anomalies(self):
        """检查异常情况"""
        # 检查车辆异常
        for vehicle in self.vehicle_manager.get_all_vehicles():
            if vehicle.battery_level < vehicle.low_battery_threshold:
                self.logger.warning(
                    f'车辆 {vehicle.id} 电量低: {vehicle.battery_level}%'
                )
            
            if vehicle.status == 'error':
                self.logger.error(
                    f'车辆 {vehicle.id} 发生错误: {vehicle.error_message}'
                )
        
        # 检查任务异常
        for task in self.task_manager.get_active_tasks():
            if task.deadline and datetime.now() > task.deadline:
                self.logger.warning(f'任务 {task.id} 已超时')
    
    def save_state(self):
        """保存系统状态"""
        try:
            state = {
                'tasks': self.task_manager.serialize(),
                'vehicles': self.vehicle_manager.serialize(),
                'delivery_points': self.delivery_manager.serialize(),
                'timestamp': datetime.now().isoformat()
            }
            
            with open('system_state.json', 'w') as f:
                json.dump(state, f, indent=2)
                
            self.logger.info('系统状态已保存')
            
        except Exception as e:
            self.logger.error(f'保存系统状态失败: {str(e)}')
    
    def load_state(self):
        """加载系统状态"""
        try:
            with open('system_state.json', 'r') as f:
                state = json.load(f)
            
            self.task_manager.deserialize(state.get('tasks', {}))
            self.vehicle_manager.deserialize(state.get('vehicles', {}))
            self.delivery_manager.deserialize(state.get('delivery_points', {}))
            
            self.logger.info('系统状态已加载')
            
        except FileNotFoundError:
            self.logger.info('未找到系统状态文件，使用初始状态')
        except Exception as e:
            self.logger.error(f'加载系统状态失败: {str(e)}')