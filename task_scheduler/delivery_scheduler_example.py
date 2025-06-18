from delivery_scheduler import DeliveryScheduler, DeliveryPoint, VehicleType, TaskStatus
from baidu_map_planner import BaiduMapPlanner
from flight_scheduler import FlightScheduler
import time

def main():
    # 初始化地图规划器和航线调度器
    map_planner = BaiduMapPlanner(
        center=(39.915, 116.404),
        zoom_start=12,
        ak="your_baidu_map_ak_here"
    )
    flight_scheduler = FlightScheduler()

    # 创建配送调度器
    scheduler = DeliveryScheduler(map_planner, flight_scheduler)

    # 注册配送点
    pickup_point = DeliveryPoint(
        id="pickup_1",
        location=(39.910, 116.400),
        type="pickup"
    )
    scheduler.register_delivery_point(pickup_point)

    drone_station = DeliveryPoint(
        id="station_1",
        location=(39.915, 116.405),
        type="drone_station"
    )
    scheduler.register_delivery_point(drone_station)

    delivery_point = DeliveryPoint(
        id="delivery_1",
        location=(39.920, 116.410),
        type="delivery"
    )
    scheduler.register_delivery_point(delivery_point)

    # 注册车辆
    # 注册取货无人车
    scheduler.register_vehicle(
        vehicle_id="car_1",
        vehicle_type=VehicleType.CAR,
        location=(39.908, 116.398)
    )

    # 注册无人机
    scheduler.register_vehicle(
        vehicle_id="drone_1",
        vehicle_type=VehicleType.DRONE,
        location=drone_station.location
    )

    # 注册配送无人车
    scheduler.register_vehicle(
        vehicle_id="car_2",
        vehicle_type=VehicleType.CAR,
        location=(39.918, 116.408)
    )

    # 创建配送任务
    task = scheduler.create_delivery_task(
        task_id="task_1",
        pickup_point_id="pickup_1",
        delivery_point_id="delivery_1"
    )

    if task:
        print(f"创建配送任务: {task.id}")
        print(f"选择的无人机起降点: {task.drone_station.id}")

        # 分配取货无人车
        if scheduler.assign_first_mile_delivery(task):
            print(f"分配取货无人车: {task.assigned_car_first_mile}")
            
            # 模拟取货过程
            time.sleep(2)  # 模拟时间延迟
            scheduler.update_vehicle_location(
                task.assigned_car_first_mile,
                task.pickup_point.location
            )
            scheduler.update_task_status(task.id, TaskStatus.PICKUP_COMPLETE)
            print("取货完成")

            # 检查无人机分配
            if task.assigned_drone:
                print(f"分配无人机: {task.assigned_drone}")
                
                # 模拟无人机运输过程
                time.sleep(2)  # 模拟时间延迟
                scheduler.update_vehicle_location(
                    task.assigned_drone,
                    task.delivery_point.location
                )
                scheduler.update_task_status(task.id, TaskStatus.TRANSFER_COMPLETE)
                print("无人机运输完成")

                # 检查配送无人车分配
                if task.assigned_car_last_mile:
                    print(f"分配配送无人车: {task.assigned_car_last_mile}")
                    
                    # 模拟最后一公里配送
                    time.sleep(2)  # 模拟时间延迟
                    scheduler.update_vehicle_location(
                        task.assigned_car_last_mile,
                        task.delivery_point.location
                    )
                    scheduler.update_task_status(task.id, TaskStatus.COMPLETED)
                    print("配送完成")

        # 显示任务完成后的状态
        print("\n任务状态:")
        print(f"任务ID: {task.id}")
        print(f"状态: {task.status}")
        print(f"取货无人车: {task.assigned_car_first_mile}")
        print(f"无人机: {task.assigned_drone}")
        print(f"配送无人车: {task.assigned_car_last_mile}")

        # 保存包含路径的地图
        map_planner.save_map('delivery_task_map.html')
        print("\n地图已保存到 delivery_task_map.html")

if __name__ == "__main__":
    main()