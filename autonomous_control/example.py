import asyncio
from vehicle_controller import VehicleController
from autonomous_control import Obstacle

async def main():
    # 创建无人机控制器
    drone_controller = VehicleController('drone')
    await drone_controller.connect('udp://:14540')
    await drone_controller.initialize()
    
    # 添加一些障碍物
    drone_controller.autonomous_controller.add_obstacle(
        Obstacle((39.9087, 116.3975, 50.0), 10.0)  # 位置和半径（米）
    )
    
    # 设置目标位置（纬度、经度、高度）
    target_position = (39.9090, 116.3980, 30.0)
    
    # 执行自主导航任务
    await drone_controller.execute_mission(target_position)
    
    # 创建无人车控制器
    car_controller = VehicleController('car')
    await car_controller.connect('udp://:14541')
    await car_controller.initialize()
    
    # 添加一些障碍物
    car_controller.autonomous_controller.add_obstacle(
        Obstacle((39.9088, 116.3976, 0.0), 5.0)  # 位置和半径（米）
    )
    
    # 设置目标位置（纬度、经度、高度始终为0）
    target_position = (39.9091, 116.3981, 0.0)
    
    # 执行自主导航任务
    await car_controller.execute_mission(target_position)

if __name__ == '__main__':
    # 运行示例程序
    asyncio.run(main())