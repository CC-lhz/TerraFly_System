from baidu_map_planner import BaiduMapPlanner

def main():
    # 创建百度地图规划器实例（需要替换为实际的百度地图API密钥）
    planner = BaiduMapPlanner(
        center=(39.915, 116.404),  # 北京市中心
        zoom_start=12,
        ak="your_baidu_map_ak_here"
    )

    # 添加一些障碍物
    planner.add_obstacle(39.915, 116.405, 200, 50)  # 添加一个半径200米，高度50米的障碍物
    planner.add_obstacle(39.920, 116.410, 300, 80)  # 添加另一个障碍物

    # 设置起点和终点
    start_point = (39.910, 116.400)  # 起点坐标
    goal_point = (39.925, 116.415)   # 终点坐标

    # 无人机路径规划示例
    print("规划无人机路径...")
    drone_path = planner.plan_path(
        start=start_point,
        goal=goal_point,
        vehicle_type="walking",  # 对于无人机，使用walking模式获取更直接的路径
        use_local=False  # 首先尝试使用百度地图API
    )
    if drone_path:
        planner.draw_path(drone_path, color='red', weight=3)
        print("无人机路径规划完成")
    else:
        print("无人机路径规划失败")

    # 地面车辆路径规划示例
    print("规划地面车辆路径...")
    car_path = planner.plan_path(
        start=start_point,
        goal=goal_point,
        vehicle_type="driving",  # 对于地面车辆，使用driving模式
        use_local=False  # 首先尝试使用百度地图API
    )
    if car_path:
        planner.draw_path(car_path, color='blue', weight=3)
        print("地面车辆路径规划完成")
    else:
        print("地面车辆路径规划失败")

    # 保存地图
    planner.save_map('baidu_path_planning.html')
    print("地图已保存到 baidu_path_planning.html")

    # 局部避障示例
    print("\n测试局部避障...")
    # 在全局路径上添加一个新的障碍物
    planner.add_obstacle(39.918, 116.408, 250, 60)

    # 使用本地路径规划算法进行避障
    print("使用本地算法重新规划无人机路径...")
    local_drone_path = planner.plan_path(
        start=start_point,
        goal=goal_point,
        vehicle_type="walking",
        use_local=True  # 强制使用本地算法
    )
    if local_drone_path:
        planner.draw_path(local_drone_path, color='green', weight=3)
        print("本地无人机路径规划完成")
    else:
        print("本地无人机路径规划失败")

    # 保存包含避障路径的地图
    planner.save_map('baidu_path_planning_with_obstacle.html')
    print("更新后的地图已保存到 baidu_path_planning_with_obstacle.html")

if __name__ == "__main__":
    main()