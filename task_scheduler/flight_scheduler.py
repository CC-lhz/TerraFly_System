from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import math
import numpy as np
from datetime import datetime, timedelta
from car.ground_control.environment_init import EnvironmentManager

@dataclass
class FlightPath:
    drone_id: str
    waypoints: List[Tuple[float, float, float]]  # [(lat, lon, altitude), ...]
    start_time: datetime
    estimated_duration: timedelta
    priority: int
    status: str = 'scheduled'  # 'scheduled', 'active', 'completed', 'aborted'

class FlightScheduler:
    def __init__(self, env_manager: EnvironmentManager):
        self.flight_paths: Dict[str, FlightPath] = {}
        self.env_manager = env_manager
        self.min_separation = 0.0001  # 约10米的经纬度差
        self.vertical_separation = 10  # 垂直间隔10米
        self.altitude_levels = list(range(30, 121, 10))  # 30米到120米，每10米一层
        self.speed = 10  # 米/秒
        self.safety_margin = 5  # 建筑物上方安全边际（米）

    def calculate_duration(self, waypoints: List[Tuple[float, float, float]]) -> timedelta:
        """计算飞行时间"""
        total_distance = 0
        for i in range(len(waypoints) - 1):
            total_distance += self.calculate_distance(waypoints[i], waypoints[i+1])
        return timedelta(seconds=total_distance / self.speed)

    def calculate_distance(self, point1: Tuple[float, float, float], 
                         point2: Tuple[float, float, float]) -> float:
        """计算两点间的三维距离（米）"""
        lat1, lon1, alt1 = point1
        lat2, lon2, alt2 = point2
        # 使用Haversine公式计算地面距离
        R = 6371000  # 地球半径（米）
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        ground_distance = R * c
        # 计算三维距离
        height_diff = alt2 - alt1
        return math.sqrt(ground_distance**2 + height_diff**2)

    def check_path_conflict(self, path1: FlightPath, path2: FlightPath, 
                          time_window: timedelta) -> bool:
        """检查两条航线是否在给定时间窗口内存在冲突"""
        if path1.status == 'completed' or path2.status == 'completed':
            return False

        # 检查时间重叠
        path1_end = path1.start_time + path1.estimated_duration
        path2_end = path2.start_time + path2.estimated_duration
        if (path1_end < path2.start_time or 
            path2_end < path1.start_time):
            return False

        # 检查空间冲突
        for wp1 in path1.waypoints:
            for wp2 in path2.waypoints:
                if self.check_point_conflict(wp1, wp2):
                    return True
        return False

    def check_point_conflict(self, point1: Tuple[float, float, float], 
                           point2: Tuple[float, float, float]) -> bool:
        """检查两个点是否存在冲突"""
        lat1, lon1, alt1 = point1
        lat2, lon2, alt2 = point2
        
        # 检查水平距离
        if (abs(lat1 - lat2) > self.min_separation or
            abs(lon1 - lon2) > self.min_separation):
            return False
            
        # 检查垂直距离
        if abs(alt1 - alt2) >= self.vertical_separation:
            return False
            
        return True

    def get_max_building_height(self, lat: float, lon: float) -> float:
        """获取指定位置的最大建筑物高度"""
        max_height = 0
        for obstacle in self.env_manager.static_obstacles:
            # 计算点到建筑物中心的距离
            dx = lat - obstacle.position[0]
            dy = lon - obstacle.position[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            # 如果点在建筑物范围内，更新最大高度
            if distance <= obstacle.radius:
                max_height = max(max_height, obstacle.position[2] + obstacle.height)
        return max_height

    def check_building_clearance(self, waypoint: Tuple[float, float, float]) -> bool:
        """检查航点是否在建筑物上方的安全高度"""
        lat, lon, alt = waypoint
        building_height = self.get_max_building_height(lat, lon)
        return alt >= building_height + self.safety_margin

    def find_safe_altitude(self, waypoints: List[Tuple[float, float, float]], 
                         start_time: datetime) -> Optional[float]:
        """为航线找到安全的飞行高度"""
        # 首先找到航线经过的所有建筑物的最大高度
        max_building_height = 0
        for wp in waypoints:
            building_height = self.get_max_building_height(wp[0], wp[1])
            max_building_height = max(max_building_height, building_height)

        # 确定最小安全飞行高度
        min_safe_alt = max_building_height + self.safety_margin

        # 在可用高度层中找到第一个大于最小安全高度的高度
        safe_levels = [alt for alt in self.altitude_levels if alt >= min_safe_alt]
        if not safe_levels:
            return None

        # 检查每个安全的高度层
        for alt in safe_levels:
            # 创建测试航线
            test_waypoints = [(wp[0], wp[1], alt) for wp in waypoints]
            test_path = FlightPath(
                drone_id='test',
                waypoints=test_waypoints,
                start_time=start_time,
                estimated_duration=self.calculate_duration(test_waypoints),
                priority=0
            )
            
            # 检查是否与现有航线冲突
            conflict = False
            for existing_path in self.flight_paths.values():
                if self.check_path_conflict(test_path, existing_path, 
                                          timedelta(minutes=5)):
                    conflict = True
                    break
            
            if not conflict:
                return alt
        return None

    def check_path_building_safety(self, waypoints: List[Tuple[float, float, float]]) -> bool:
        """检查路径是否安全（不穿过建筑物之间）"""
        for i in range(len(waypoints) - 1):
            start = waypoints[i]
            end = waypoints[i + 1]
            
            # 在路径上采样多个点进行检查
            steps = 10  # 采样点数量
            for step in range(steps + 1):
                t = step / steps
                # 线性插值计算采样点
                point = (
                    start[0] + (end[0] - start[0]) * t,
                    start[1] + (end[1] - start[1]) * t,
                    start[2] + (end[2] - start[2]) * t
                )
                
                # 检查该点是否满足建筑物高度要求
                if not self.check_building_clearance(point):
                    return False
        return True

    def schedule_flight(self, drone_id: str, waypoints: List[Tuple[float, float]], 
                       start_time: datetime, priority: int) -> bool:
        """调度新的飞行任务"""
        # 寻找安全的飞行高度
        safe_alt = self.find_safe_altitude(waypoints, start_time)
        if safe_alt is None:
            return False

        # 创建带高度的航点
        waypoints_3d = [(wp[0], wp[1], safe_alt) for wp in waypoints]
        
        # 检查路径是否安全（不穿过建筑物之间）
        if not self.check_path_building_safety(waypoints_3d):
            return False
        
        # 计算预计飞行时间
        duration = self.calculate_duration(waypoints_3d)
        
        # 创建飞行路径
        flight_path = FlightPath(
            drone_id=drone_id,
            waypoints=waypoints_3d,
            start_time=start_time,
            estimated_duration=duration,
            priority=priority
        )
        
        # 添加到调度系统
        self.flight_paths[drone_id] = flight_path
        return True

    def update_flight_status(self, drone_id: str, status: str):
        """更新飞行状态"""
        if drone_id in self.flight_paths:
            self.flight_paths[drone_id].status = status

    def get_current_altitude(self, drone_id: str) -> Optional[float]:
        """获取无人机当前的飞行高度"""
        if drone_id in self.flight_paths:
            path = self.flight_paths[drone_id]
            if path.status == 'active':
                return path.waypoints[0][2]  # 返回第一个航点的高度
        return None

    def get_active_flights(self) -> List[FlightPath]:
        """获取所有活动的飞行任务"""
        return [path for path in self.flight_paths.values() 
                if path.status == 'active']