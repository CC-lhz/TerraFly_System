from dataclasses import dataclass
from typing import List, Tuple, Optional
import math
from . import config
import logging

@dataclass
class Obstacle:
    """障碍物数据类"""
    position: Tuple[float, float, float]  # 位置（纬度、经度、高度）
    radius: float                         # 半径（米）

@dataclass
class PathPoint:
    """路径点数据类"""
    position: Tuple[float, float, float]  # 位置（纬度、经度、高度）
    heading: float                        # 航向角（度）
    velocity: float                       # 速度（米/秒）

class AutonomousController:
    def __init__(self):
        self.vehicle_type = 'drone'  # 默认为无人机
        self.current_position = (0.0, 0.0, 0.0)
        self.current_heading = 0.0
        self.target_position = None
        self.obstacles: List[Obstacle] = []
        self.path: List[PathPoint] = []
        self.logger = logging.getLogger(__name__)

    def set_vehicle_type(self, vehicle_type: str):
        """设置车辆类型（'drone' 或 'car'）"""
        if vehicle_type not in ['drone', 'car']:
            raise ValueError("车辆类型必须是 'drone' 或 'car'")
        self.vehicle_type = vehicle_type

    def update_position(self, position: Tuple[float, float, float]):
        """更新当前位置"""
        self.current_position = position

    def update_heading(self, heading: float):
        """更新当前航向角"""
        self.current_heading = heading

    def set_target(self, position: Tuple[float, float, float]):
        """设置目标位置"""
        self.target_position = position
        self.path = []  # 清除现有路径

    def add_obstacle(self, obstacle: Obstacle):
        """添加障碍物"""
        self.obstacles.append(obstacle)

    def clear_obstacles(self):
        """清除所有障碍物"""
        self.obstacles = []

    def calculate_distance(self, pos1: Tuple[float, float, float],
                         pos2: Tuple[float, float, float]) -> float:
        """计算两点间距离（米）"""
        # 使用Haversine公式计算地球表面两点间距离
        R = 6371000  # 地球半径（米）
        lat1, lon1, h1 = pos1
        lat2, lon2, h2 = pos2

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi/2) * math.sin(delta_phi/2) +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(delta_lambda/2) * math.sin(delta_lambda/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R * c

        # 考虑高度差
        height_diff = h2 - h1
        return math.sqrt(d*d + height_diff*height_diff)

    def check_collision(self, position: Tuple[float, float, float]) -> bool:
        """检查位置是否与障碍物碰撞"""
        margin = config.PATH_PLANNING[self.vehicle_type]['obstacle_margin']
        for obstacle in self.obstacles:
            distance = self.calculate_distance(position, obstacle.position)
            if distance <= (obstacle.radius + margin):
                return True
        return False

    def generate_path(self) -> List[PathPoint]:
        """生成路径点"""
        if not self.target_position:
            self.logger.error("未设置目标位置")
            return []

        if self.vehicle_type == 'drone':
            return self._generate_drone_path()
        else:
            return self._generate_car_path()

    def _generate_drone_path(self) -> List[PathPoint]:
        """使用A*算法为无人机生成路径"""
        params = config.PATH_PLANNING['drone']
        path = []
        current = PathPoint(
            position=self.current_position,
            heading=self.current_heading,
            velocity=params['min_velocity']
        )
        path.append(current)

        while self.calculate_distance(current.position, self.target_position) > params['step_size']:
            best_point = None
            min_cost = float('inf')

            # 在不同角度和高度搜索下一个点
            for i in range(params['search_angles']):
                angle = current.heading + (i - params['search_angles']//2) * \
                        (params['angle_range'] / params['search_angles'])
                angle = angle % 360

                # 计算下一个位置
                lat = current.position[0] + params['step_size'] * math.cos(math.radians(angle))
                lon = current.position[1] + params['step_size'] * math.sin(math.radians(angle))
                alt = current.position[2]

                # 调整高度以避开障碍物
                if self.check_collision((lat, lon, alt)):
                    continue

                new_pos = (lat, lon, alt)
                # 计算代价（距离目标点的距离）
                cost = self.calculate_distance(new_pos, self.target_position)

                if cost < min_cost:
                    min_cost = cost
                    velocity = self._calculate_velocity(current.position, new_pos)
                    best_point = PathPoint(position=new_pos, heading=angle, velocity=velocity)

            if best_point is None:
                self.logger.error("无法找到有效路径点")
                return []

            path.append(best_point)
            current = best_point

        # 添加目标点
        final_heading = self._calculate_heading(current.position, self.target_position)
        path.append(PathPoint(
            position=self.target_position,
            heading=final_heading,
            velocity=params['min_velocity']
        ))

        return path

    def _generate_car_path(self) -> List[PathPoint]:
        """使用RRT算法为无人车生成路径"""
        params = config.PATH_PLANNING['car']
        path = []
        current = PathPoint(
            position=self.current_position,
            heading=self.current_heading,
            velocity=params['min_velocity']
        )
        path.append(current)

        while self.calculate_distance(current.position, self.target_position) > params['step_size']:
            best_point = None
            min_cost = float('inf')

            # 在不同转向角度搜索下一个点
            for i in range(params['search_angles']):
                angle = current.heading + (i - params['search_angles']//2) * \
                        (params['angle_range'] / params['search_angles'])
                angle = angle % 360

                # 考虑转弯半径限制
                if abs(angle - current.heading) > params['angle_range']:
                    continue

                # 计算下一个位置
                lat = current.position[0] + params['step_size'] * math.cos(math.radians(angle))
                lon = current.position[1] + params['step_size'] * math.sin(math.radians(angle))
                new_pos = (lat, lon, 0.0)  # 无人车高度始终为0

                # 检查碰撞
                if self.check_collision(new_pos):
                    continue

                # 计算代价（距离目标点的距离）
                cost = self.calculate_distance(new_pos, self.target_position)

                if cost < min_cost:
                    min_cost = cost
                    velocity = self._calculate_velocity(current.position, new_pos)
                    best_point = PathPoint(position=new_pos, heading=angle, velocity=velocity)

            if best_point is None:
                self.logger.error("无法找到有效路径点")
                return []

            path.append(best_point)
            current = best_point

        # 添加目标点
        final_heading = self._calculate_heading(current.position, self.target_position)
        path.append(PathPoint(
            position=self.target_position,
            heading=final_heading,
            velocity=params['min_velocity']
        ))

        return path

    def _calculate_heading(self, pos1: Tuple[float, float, float],
                         pos2: Tuple[float, float, float]) -> float:
        """计算两点间航向角（度）"""
        delta_lon = pos2[1] - pos1[1]
        delta_lat = pos2[0] - pos1[0]
        heading = math.degrees(math.atan2(delta_lon, delta_lat)) % 360
        return heading

    def _calculate_velocity(self, pos1: Tuple[float, float, float],
                          pos2: Tuple[float, float, float]) -> float:
        """计算两点间的速度"""
        params = config.PATH_PLANNING[self.vehicle_type]
        distance = self.calculate_distance(pos1, pos2)
        # 根据距离调整速度，确保在拐弯处减速
        velocity = min(params['max_velocity'],
                      max(params['min_velocity'],
                          distance * 0.5))  # 速度与距离成正比
        return velocity