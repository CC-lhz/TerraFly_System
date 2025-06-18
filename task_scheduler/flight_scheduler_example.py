from datetime import datetime, timedelta
from flight_scheduler import FlightScheduler

def test_flight_scheduling():
    # 创建航线调度器
    scheduler = FlightScheduler()
    
    # 测试场景：多架无人机在不同时间执行任务
    
    # 无人机1的航线
    drone1_waypoints = [
        (22.50, 113.40),  # 起点
        (22.51, 113.41),  # 途经点1
        (22.52, 113.42)   # 终点
    ]
    
    # 无人机2的航线
    drone2_waypoints = [
        (22.49, 113.39),  # 起点
        (22.50, 113.40),  # 途经点1
        (22.51, 113.41)   # 终点
    ]
    
    # 无人机3的航线（与无人机1和2的航线有潜在冲突）
    drone3_waypoints = [
        (22.51, 113.41),  # 起点
        (22.50, 113.40),  # 途经点1
        (22.49, 113.39)   # 终点
    ]
    
    # 调度第一架无人机的航线
    start_time1 = datetime.now()
    success1 = scheduler.schedule_flight('drone1', drone1_waypoints, start_time1, priority=3)
    print(f"无人机1航线调度: {'成功' if success1 else '失败'}")
    if success1:
        path1 = scheduler.flight_paths['drone1']
        print(f"分配高度: {path1.waypoints[0][2]}米")
    
    # 调度第二架无人机的航线（5分钟后起飞）
    start_time2 = datetime.now() + timedelta(minutes=5)
    success2 = scheduler.schedule_flight('drone2', drone2_waypoints, start_time2, priority=2)
    print(f"无人机2航线调度: {'成功' if success2 else '失败'}")
    if success2:
        path2 = scheduler.flight_paths['drone2']
        print(f"分配高度: {path2.waypoints[0][2]}米")
    
    # 调度第三架无人机的航线（与前两架时空重叠）
    start_time3 = datetime.now() + timedelta(minutes=3)
    success3 = scheduler.schedule_flight('drone3', drone3_waypoints, start_time3, priority=1)
    print(f"无人机3航线调度: {'成功' if success3 else '失败'}")
    if success3:
        path3 = scheduler.flight_paths['drone3']
        print(f"分配高度: {path3.waypoints[0][2]}米")
    
    # 获取当前活动的航线
    active_flights = scheduler.get_active_flights()
    print(f"\n当前活动航线数量: {len(active_flights)}")
    for flight in active_flights:
        print(f"无人机 {flight.drone_id}:")
        print(f"  起飞时间: {flight.start_time}")
        print(f"  预计飞行时间: {flight.estimated_duration}")
        print(f"  飞行高度: {flight.waypoints[0][2]}米")
        print(f"  优先级: {flight.priority}")
        print(f"  状态: {flight.status}")

if __name__ == "__main__":
    test_flight_scheduling()