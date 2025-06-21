from typing import List, Tuple, Dict, Optional
from .map_planner import MapPlanner, MapPoint
from .master_computer.map_manager import MapManager, PathType

class SystemMapPlanner(MapPlanner):
    def __init__(self, center: Tuple[float, float], zoom_start: int = 13):
        super().__init__(center, zoom_start)
        self.map_manager = MapManager()
        
    async def initialize(self):
        """初始化地图管理器（异步方法）"""
        await self.map_manager.initialize()
    
    def initialize_sync(self):
        """初始化地图管理器（同步方法）"""
        # 由于GUI是同步的，这里使用同步方式初始化
        self.map_manager.initialize_sync()
    
    def get_global_path(self, start: Tuple[float, float], goal: Tuple[float, float], vehicle_type: str = "driving") -> List[Tuple[float, float]]:
        """使用系统地图管理器获取全局路径规划
        vehicle_type: driving-驾车, walking-步行, riding-骑行
        """
        # 转换输入格式
        start_point = {"lat": start[0], "lon": start[1], "alt": 0}
        goal_point = {"lat": goal[0], "lon": goal[1], "alt": 0}
        
        # 根据车辆类型选择路径类型
        path_type = PathType.ROAD if vehicle_type == "driving" else PathType.HYBRID
        
        # 使用地图管理器规划路径
        path = self.map_manager.plan_path(
            start=start_point,
            end=goal_point,
            path_type=path_type,
            vehicle_type="car" if vehicle_type == "driving" else "drone",
            avoid_obstacles=True,
            avoid_restricted=True
        )
        
        # 转换输出格式
        if path:
            return [(point["lat"], point["lon"]) for point in path]
        return []

    def plan_path(self, start: Tuple[float, float], goal: Tuple[float, float], 
                  vehicle_type: str = "driving", use_local: bool = False) -> List[Tuple[float, float]]:
        """综合路径规划
        使用系统地图管理器进行路径规划，支持道路和空中路径
        """
        # 获取全局路径
        path = self.get_global_path(start, goal, vehicle_type)
        
        # 如果获取失败或需要使用本地规划
        if not path or use_local:
            if vehicle_type == "driving":
                return self.rrt_path(start, goal)  # 地面车辆使用RRT算法
            else:
                return self.a_star_path(start, goal)  # 无人机使用A*算法
        
        return path

    def add_obstacle(self, lat: float, lon: float, radius: float, height: float):
        """添加障碍物"""
        super().add_obstacle(lat, lon, radius, height)
        # 同步添加到地图管理器
        self.map_manager.add_obstacle({
            "id": f"obs_{lat}_{lon}",
            "lat": lat,
            "lon": lon,
            "radius": radius,
            "height": height
        })

    def add_restricted_area(self, area: Dict):
        """添加限制区域"""
        self.map_manager.add_restricted_area(area)