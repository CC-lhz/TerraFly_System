from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import math
import numpy as np
from datetime import datetime, timedelta

@dataclass
class FlightPath:
    drone_id: str
    waypoints: List[Tuple[float, float, float]]  # [(lat, lon, altitude), ...]
    start_time: datetime
    estimated_duration: timedelta
    priority: int
    status: str = 'scheduled'  # 'scheduled', 'active', 'completed', 'aborted'

class FlightScheduler:
    def __init__(self):
        self.flight_paths: Dict[str, FlightPath] = {}
        self.min_separation = 0.0001  # 约10米的经纬度差
        self.vertical_separation = 10  # 垂直间隔10米
        self.altitude_levels = list(range(30, 121, 10))  # 30米到120米，每10米一层
        self.speed = 10  # 米/秒

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

    def find_safe_altitude(self, waypoints: List[Tuple[float, float, float]], 
                         start_time: datetime) -> Optional[float]:
        """为航线找到安全的飞行高度"""
        # 检查每个可用的高度层
        for alt in self.altitude_levels:
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

    def schedule_flight(self, drone_id: str, waypoints: List[Tuple[float, float]], 
                       start_time: datetime, priority: int) -> bool:
        """调度新的飞行任务"""
        # 寻找安全的飞行高度
        safe_alt = self.find_safe_altitude(waypoints, start_time)
        if safe_alt is None:
            return False

        # 创建带高度的航点
        waypoints_3d = [(wp[0], wp[1], safe_alt) for wp in waypoints]
        
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