import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass
import math
from queue import PriorityQueue

@dataclass
class MapPoint:
    latitude: float
    longitude: float
    elevation: float = 0.0  # 海拔高度
    obstacle: bool = False   # 是否为障碍物
    cost: float = 0.0       # 路径代价

class MapPlanner:
    def __init__(self, center: Tuple[float, float], zoom_start: int = 13):
        self.center = center
        self.zoom_start = zoom_start
        self.obstacles: List[Tuple[float, float, float, float]] = []  # (lat, lon, radius, height)
        self.grid_size = 0.001  # 约100米网格
        self.max_elevation = 120.0  # 最大飞行高度
        self.min_elevation = 20.0   # 最小飞行高度
        self.terrain_map = {}  # 地形高度图
        
    def add_terrain(self, lat: float, lon: float, elevation: float):
        """添加地形高度信息"""
        self.terrain_map[(lat, lon)] = elevation
    
    def get_terrain_elevation(self, lat: float, lon: float) -> float:
        """获取指定位置的地形高度"""
        # 如果没有精确的高度数据，使用最近点的高度
        if (lat, lon) in self.terrain_map:
            return self.terrain_map[(lat, lon)]
        
        # 找到最近的已知高度点
        nearest = min(self.terrain_map.keys(),
                     key=lambda p: self.calculate_distance((lat, lon), p))
        return self.terrain_map[nearest]

    def add_obstacle(self, lat: float, lon: float, radius: float, height: float):
        """添加障碍物"""
        self.obstacles.append((lat, lon, radius, height))

    def check_collision(self, point: Tuple[float, float, float]) -> bool:
        """检查是否与障碍物碰撞，考虑高度"""
        lat, lon, elevation = point
        
        # 检查是否超出高度限制
        if elevation < self.min_elevation or elevation > self.max_elevation:
            return True
        
        # 检查是否低于地形
        terrain_height = self.get_terrain_elevation(lat, lon)
        if elevation < terrain_height:
            return True
        
        # 检查是否与障碍物碰撞
        for obs_lat, obs_lon, radius, height in self.obstacles:
            if self.calculate_distance((obs_lat, obs_lon), (lat, lon)) <= radius:
                if elevation <= height:
                    return True
        return False

    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """计算两点间的水平距离（公里）"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        R = 6371  # 地球半径（公里）

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def calculate_3d_distance(self, point1: Tuple[float, float, float],
                            point2: Tuple[float, float, float]) -> float:
        """计算两点间的三维距离（公里）"""
        horizontal_dist = self.calculate_distance(
            (point1[0], point1[1]), (point2[0], point2[1]))
        vertical_dist = abs(point1[2] - point2[2]) / 1000  # 转换为公里
        return math.sqrt(horizontal_dist**2 + vertical_dist**2)

    def get_neighbors_3d(self, point: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
        """获取三维空间中的相邻点"""
        lat, lon, elevation = point
        neighbors = []
        
        # 水平方向的邻居
        for dlat in [-self.grid_size, 0, self.grid_size]:
            for dlon in [-self.grid_size, 0, self.grid_size]:
                # 垂直方向的邻居
                for delev in [-10, 0, 10]:  # 每次上升或下降10米
                    if dlat == 0 and dlon == 0 and delev == 0:
                        continue
                    new_point = (lat + dlat, lon + dlon, elevation + delev)
                    if not self.check_collision(new_point):
                        neighbors.append(new_point)
        return neighbors

    def get_neighbors_2d(self, point: Tuple[float, float]) -> List[Tuple[float, float]]:
        """获取平面上的相邻点（用于地面车辆）"""
        lat, lon = point
        neighbors = []
        for dlat in [-self.grid_size, 0, self.grid_size]:
            for dlon in [-self.grid_size, 0, self.grid_size]:
                if dlat == 0 and dlon == 0:
                    continue
                new_point = (lat + dlat, lon + dlon)
                # 获取地形高度
                elevation = self.get_terrain_elevation(new_point[0], new_point[1])
                if not self.check_collision((new_point[0], new_point[1], elevation)):
                    neighbors.append(new_point)
        return neighbors

    def plan_drone_path(self, start: Tuple[float, float], goal: Tuple[float, float],
                       start_elevation: float, goal_elevation: float) -> List[Tuple[float, float, float]]:
        """规划无人机路径（三维A*算法）"""
        start_3d = (start[0], start[1], start_elevation)
        goal_3d = (goal[0], goal[1], goal_elevation)
        
        frontier = PriorityQueue()
        frontier.put((0, start_3d))
        came_from = {start_3d: None}
        cost_so_far = {start_3d: 0}

        while not frontier.empty():
            current = frontier.get()[1]

            if current == goal_3d:
                break

            for next_point in self.get_neighbors_3d(current):
                new_cost = cost_so_far[current] + self.calculate_3d_distance(current, next_point)

                if next_point not in cost_so_far or new_cost < cost_so_far[next_point]:
                    cost_so_far[next_point] = new_cost
                    priority = new_cost + self.calculate_3d_distance(next_point, goal_3d)
                    frontier.put((priority, next_point))
                    came_from[next_point] = current

        # 重建路径
        path = []
        current = goal_3d
        while current is not None:
            path.append(current)
            current = came_from.get(current)
        path.reverse()
        return path

    def plan_car_path(self, start: Tuple[float, float], goal: Tuple[float, float]) -> List[Tuple[float, float, float]]:
        """规划无人车路径（二维A*算法，但返回带高度的路径）"""
        frontier = PriorityQueue()
        frontier.put((0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()[1]

            if current == goal:
                break

            for next_point in self.get_neighbors_2d(current):
                new_cost = cost_so_far[current] + self.calculate_distance(current, next_point)

                if next_point not in cost_so_far or new_cost < cost_so_far[next_point]:
                    cost_so_far[next_point] = new_cost
                    priority = new_cost + self.calculate_distance(next_point, goal)
                    frontier.put((priority, next_point))
                    came_from[next_point] = current

        # 重建路径，加入高度信息
        path = []
        current = goal
        while current is not None:
            elevation = self.get_terrain_elevation(current[0], current[1])
            path.append((current[0], current[1], elevation))
            current = came_from.get(current)
        path.reverse()
        return path