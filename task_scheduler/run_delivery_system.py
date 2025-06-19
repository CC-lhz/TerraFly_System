import asyncio
import sys
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from unified_scheduler import UnifiedScheduler, Vehicle, Task, Priority, DeliveryPoint
from map_planner import MapPlanner
from flight_scheduler import FlightScheduler
from gui.main_window import MainWindow
import config

async def initialize_system():
    """初始化统一调度系统"""
    # 初始化地图规划器和飞行调度器
    map_planner = MapPlanner(center=config.config['map_center'], zoom_start=config.config['zoom_start'])
    flight_scheduler = FlightScheduler()
    
    # 创建统一调度器
    scheduler = UnifiedScheduler(map_planner, flight_scheduler)
    
    # 尝试加载之前的系统状态
    try:
        scheduler.load_state(config.config['storage']['state_file_path'])
        print("已加载系统状态")
    except Exception as e:
        print(f"加载系统状态失败: {str(e)}，将使用初始状态")
    
    return scheduler

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
        
        await asyncio.sleep(config.config['scheduler']['interval'])

async def main():
    """主程序入口"""
    try:
        print("初始化统一调度系统...")
        scheduler = await initialize_system()
        
        # 创建QApplication实例
        app = QApplication(sys.argv)
        
        # 创建主窗口
        main_window = MainWindow()
        main_window.scheduler = scheduler  # 设置调度器
        main_window.show()
        
        # 创建监控任务
        monitor_task = asyncio.create_task(monitor_system(scheduler))
        
        # 启动调度器主循环
        scheduler_task = asyncio.create_task(scheduler.run())
        
        # 启动系统监控循环
        monitor_loop_task = asyncio.create_task(scheduler.run_monitor_loop())
        
        print("系统已启动，GUI界面已加载")
        
        # 等待GUI事件循环和异步任务
        await asyncio.gather(
            monitor_task,
            scheduler_task,
            monitor_loop_task
        )
        
    except Exception as e:
        print(f"\n系统错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'scheduler' in locals():
            try:
                scheduler.save_state(config.config['storage']['state_file_path'])
                print("最终系统状态已保存")
            except Exception as e:
                print(f"保存状态失败: {str(e)}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n系统已退出")
    except Exception as e:
        print(f"\n系统启动失败: {str(e)}")
        sys.exit(1)