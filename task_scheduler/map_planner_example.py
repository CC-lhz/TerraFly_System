from map_planner import MapPlanner

def main():
    # 创建地图规划器，设置深圳市中心坐标
    planner = MapPlanner(center=(22.5, 113.4))
    
    # 添加一些障碍物（建筑物、禁飞区等）
    planner.add_obstacle(22.51, 113.41, 200, 100)  # 半径200米，高度100米的障碍物
    planner.add_obstacle(22.49, 113.39, 150, 80)   # 半径150米，高度80米的障碍物
    planner.add_obstacle(22.505, 113.405, 180, 90)  # 半径180米，高度90米的障碍物
    
    # 设置起点和终点
    start_point = (22.48, 113.38)  # 起点坐标
    goal_point = (22.52, 113.42)   # 终点坐标
    
    # 使用A*算法为无人机生成路径（考虑三维空间）
    drone_path = planner.a_star_path(start_point, goal_point)
    print("无人机路径规划完成，路径点数量:", len(drone_path))
    
    # 在地图上绘制无人机路径
    planner.draw_path(drone_path, color='red', weight=3)
    
    # 使用RRT算法为地面车辆生成路径（考虑二维平面和转弯半径）
    car_start = (22.49, 113.39)
    car_goal = (22.51, 113.41)
    car_path = planner.rrt_path(car_start, car_goal)
    print("地面车辆路径规划完成，路径点数量:", len(car_path))
    
    # 在地图上绘制地面车辆路径
    planner.draw_path(car_path, color='blue', weight=3)
    
    # 保存地图
    planner.save_map('example_routes.html')
    print("地图已保存到 example_routes.html")

if __name__ == "__main__":
    main()