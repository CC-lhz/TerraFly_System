import asyncio
from datetime import datetime
from unified_scheduler import UnifiedScheduler, Vehicle, Task, Priority, DeliveryPoint
from baidu_map_planner import BaiduMapPlanner
from flight_scheduler import FlightScheduler
import config

async def initialize_system():
    """初始化统一调度系统"""
    # 初始化地图规划器和飞行调度器
    map_planner = BaiduMapPlanner(config.config['baidu_map']['ak'])
    flight_scheduler = FlightScheduler()
    
    # 创建统一调度器
    scheduler = UnifiedScheduler(map_planner, flight_scheduler)
    
    # 注册起降点
    delivery_points = [
        DeliveryPoint(
            id='pickup_point1',
            type='pickup',
            location=(config.config['map']['center_lat'] + 0.01, config.config['map']['center_lon'] + 0.01)
        ),
        DeliveryPoint(
            id='drone_station1',
            type='drone_station',
            location=(config.config['map']['center_lat'], config.config['map']['center_lon'])
        ),
        DeliveryPoint(
            id='delivery_point1',
            type='delivery',
            location=(config.config['map']['center_lat'] - 0.01, config.config['map']['center_lon'] - 0.01)
        )
    ]
    
    for point in delivery_points:
        scheduler.register_delivery_point(point)
        print(f"已注册{point.type}: {point.id}")
    
    # 注册运输工具
    vehicles = [
        Vehicle(
            id='drone1',
            type='drone',
            location=(config.config['map']['center_lat'] + 0.01, config.config['map']['center_lon'] + 0.01),
            status='idle',
            battery_level=90,
            max_payload=config.config['vehicle']['drone']['max_payload'],
            current_payload=0,
            capabilities=['aerial_delivery']
        ),
        Vehicle(
            id='car1',
            type='car',
            location=(config.config['map']['center_lat'] - 0.02, config.config['map']['center_lon'] - 0.01),
            status='idle',
            battery_level=75,
            max_payload=config.config['vehicle']['car']['max_payload'],
            current_payload=0,
            capabilities=['ground_delivery', 'first_mile', 'last_mile']
        )
    ]
    
    for vehicle in vehicles:
        scheduler.register_vehicle(vehicle)
        print(f"已注册{vehicle.type}: {vehicle.id}")
    
    return scheduler

async def add_test_tasks(scheduler: UnifiedScheduler):
    """添加测试任务"""
    tasks = [
        Task(
            id='task1',
            pickup_point='pickup_point1',
            delivery_point='delivery_point1',
            weight=2.5,
            priority=Priority.HIGH,
            created_at=datetime.now(),
            deadline=None,
            required_capabilities=['ground_delivery', 'aerial_delivery']
        ),
        Task(
            id='task2',
            pickup_point='pickup_point1',
            delivery_point='delivery_point1',
            weight=15.0,
            priority=Priority.NORMAL,
            created_at=datetime.now(),
            deadline=None,
            required_capabilities=['ground_delivery']
        )
    ]
    
    # 添加所有测试任务
    for task in tasks:
        await scheduler.add_task(task)
        print(f"已添加任务: {task.id}, 优先级: {task.priority.name}")

async def monitor_system(scheduler: UnifiedScheduler):
    """监控系统状态"""
    while True:
        status = scheduler.get_system_status()
        
        print("\n当前系统状态:")
        print("运输工具状态:")
        for vehicle in status['vehicles']:
            print(f"{vehicle['type']} {vehicle['id']}: {vehicle['status']}, "
                  f"电量: {vehicle['battery_level']}%, "
                  f"位置: ({vehicle['location'][0]:.4f}, {vehicle['location'][1]:.4f})")
        
        print("\n任务状态:")
        for task in status['tasks']:
            print(f"任务 {task['id']}: {task['status']}, "
                  f"优先级: {task['priority']}"
                  + (f", 分配给: {task['assigned_to']}" if task['assigned_to'] else ""))
        
        print("\n起降点状态:")
        for point in status['delivery_points']:
            print(f"{point['type']} {point['id']}: "
                  f"位置: ({point['location'][0]:.4f}, {point['location'][1]:.4f})")
        
        # 保存系统状态
        scheduler.save_state(config.config['storage']['state_file_path'])
        print(f"\n系统状态已保存: {config.config['storage']['state_file_path']}")
        
        # 更新并保存地图
        scheduler.save_map(config.config['storage']['map_filename'])
        print(f"地图已更新: {config.config['storage']['map_filename']}")
        
        await asyncio.sleep(config.config['scheduler']['interval'])

async def main():
    """主程序入口"""
    scheduler = None
    tasks = []
    
    try:
        print("初始化统一调度系统...")
        scheduler = await initialize_system()
        
        # 尝试加载之前的系统状态
        try:
            scheduler.load_state(config.config['storage']['state_file_path'])
            print("已加载系统状态")
        except Exception as e:
            print(f"加载系统状态失败: {str(e)}，将使用初始状态")
        
        print("\n添加测试任务...")
        await add_test_tasks(scheduler)
        
        # 创建监控任务
        monitor_task = asyncio.create_task(monitor_system(scheduler))
        tasks.append(monitor_task)
        
        # 启动调度器主循环
        scheduler_task = asyncio.create_task(scheduler.run())
        tasks.append(scheduler_task)
        
        # 启动系统监控循环
        monitor_loop_task = asyncio.create_task(scheduler.run_monitor_loop())
        tasks.append(monitor_loop_task)
        
        print("系统已启动，按Ctrl+C退出...")
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        print("\n正在优雅关闭系统...")
        if scheduler:
            # 保存当前状态
            scheduler.save_state(config.config['storage']['state_file_path'])
            print("系统状态已保存")
            
            # 停止所有运行中的任务
            for vehicle in scheduler.get_system_status()['vehicles']:
                if vehicle['status'] != 'idle':
                    await scheduler.stop_vehicle(vehicle['id'])
                    print(f"已停止 {vehicle['type']} {vehicle['id']}")
        
        # 取消所有异步任务
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
    except Exception as e:
        print(f"\n系统错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if scheduler:
            # 确保状态被保存
            try:
                scheduler.save_state(config.config['storage']['state_file_path'])
                print("最终系统状态已保存")
            except Exception as e:
                print(f"保存系统状态失败: {str(e)}")
        print("系统已关闭")

if __name__ == "__main__":
    asyncio.run(main())