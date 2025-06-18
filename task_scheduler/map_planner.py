import folium
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
        self.map = folium.Map(location=center, zoom_start=zoom_start)
        self.obstacles: List[Tuple[float, float, float]] = []  # (lat, lon, radius)
        self.grid_size = 0.001  # 约100米网格
        self.max_elevation = 120.0  # 最大飞行高度
        self.min_elevation = 20.0   # 最小飞行高度

    def add_obstacle(self, lat: float, lon: float, radius: float, height: float):
        """添加障碍物"""
        self.obstacles.append((lat, lon, radius))
        folium.Circle(
            location=(lat, lon),
            radius=radius,
            color='red',
            fill=True,
            popup=f'Obstacle H:{height}m'
        ).add_to(self.map)

    def check_collision(self, point: Tuple[float, float]) -> bool:
        """检查是否与障碍物碰撞"""
        for obs_lat, obs_lon, radius in self.obstacles:
            if self.calculate_distance((obs_lat, obs_lon), point) <= radius:
                return True
        return False

    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """计算两点间的距离（公里）"""
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

    def get_neighbors(self, point: Tuple[float, float]) -> List[Tuple[float, float]]:
        """获取相邻点"""
        lat, lon = point
        neighbors = []
        for dlat in [-self.grid_size, 0, self.grid_size]:
            for dlon in [-self.grid_size, 0, self.grid_size]:
                if dlat == 0 and dlon == 0:
                    continue
                new_point = (lat + dlat, lon + dlon)
                if not self.check_collision(new_point):
                    neighbors.append(new_point)
        return neighbors

    def a_star_path(self, start: Tuple[float, float], goal: Tuple[float, float]) -> List[Tuple[float, float]]:
        """使用A*算法生成路径"""
        frontier = PriorityQueue()
        frontier.put((0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()[1]

            if current == goal:
                break

            for next_point in self.get_neighbors(current):
                new_cost = cost_so_far[current] + self.calculate_distance(current, next_point)

                if next_point not in cost_so_far or new_cost < cost_so_far[next_point]:
                    cost_so_far[next_point] = new_cost
                    priority = new_cost + self.calculate_distance(next_point, goal)
                    frontier.put((priority, next_point))
                    came_from[next_point] = current

        # 重建路径
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = came_from.get(current)
        path.reverse()
        return path

    def rrt_path(self, start: Tuple[float, float], goal: Tuple[float, float], max_iter: int = 1000) -> List[Tuple[float, float]]:
        """使用RRT算法生成路径（适用于地面车辆）"""
        nodes = [start]
        parent = {start: None}

        for _ in range(max_iter):
            # 随机采样点
            if np.random.random() < 0.1:
                sample = goal
            else:
                sample = (
                    start[0] + (np.random.random() - 0.5) * 0.02,
                    start[1] + (np.random.random() - 0.5) * 0.02
                )

            # 找到最近的节点
            nearest = min(nodes, key=lambda n: self.calculate_distance(n, sample))

            # 计算新节点
            dist = self.calculate_distance(nearest, sample)
            if dist > self.grid_size:
                theta = math.atan2(sample[1] - nearest[1], sample[0] - nearest[0])
                new_node = (
                    nearest[0] + self.grid_size * math.cos(theta),
                    nearest[1] + self.grid_size * math.sin(theta)
                )
            else:
                new_node = sample

            # 检查碰撞
            if not self.check_collision(new_node):
                nodes.append(new_node)
                parent[new_node] = nearest

                # 检查是否到达目标
                if self.calculate_distance(new_node, goal) < self.grid_size:
                    nodes.append(goal)
                    parent[goal] = new_node
                    break

        # 重建路径
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = parent.get(current)
        path.reverse()
        return path

    def draw_path(self, path: List[Tuple[float, float]], color: str = 'blue', weight: int = 3):
        """在地图上绘制路径"""
        if len(path) < 2:
            return

        folium.PolyLine(
            locations=path,
            weight=weight,
            color=color,
            opacity=0.8
        ).add_to(self.map)

        # 添加起点和终点标记
        folium.Marker(
            location=path[0],
            popup='Start',
            icon=folium.Icon(color='green')
        ).add_to(self.map)

        folium.Marker(
            location=path[-1],
            popup='Goal',
            icon=folium.Icon(color='red')
        ).add_to(self.map)

    def save_map(self, filename: str = 'path_map.html'):
        """保存地图到文件"""
        self.map.save(filename)