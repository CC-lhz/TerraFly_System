from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from enum import Enum
import numpy as np

class MapLayerType(Enum):
    """地图图层类型"""
    TERRAIN = 'terrain'  # 地形图层
    TRAFFIC = 'traffic'  # 交通图层
    WEATHER = 'weather'  # 天气图层
    RESTRICTED = 'restricted'  # 限飞区图层
    CUSTOM = 'custom'  # 自定义图层

class PathType(Enum):
    """路径类型"""
    ROAD = 'road'  # 道路路径
    AIR = 'air'  # 空中路径
    HYBRID = 'hybrid'  # 混合路径

class MapManager:
    """地图管理器"""
    def __init__(self):
        self.logger = logging.getLogger('MapManager')
        self.map_layers = {}
        self.cached_paths = {}
        self.obstacles = []
        self.restricted_areas = []
        self.last_update = datetime.now()
    
    async def initialize(self):
        """初始化地图管理器"""
        self.logger.info('地图管理器初始化')
        await self.load_map_layers()
        await self.load_restricted_areas()
    
    async def load_map_layers(self):
        """加载地图图层"""
        # 加载基础地图图层
        self.map_layers[MapLayerType.TERRAIN] = await self.load_terrain_data()
        self.map_layers[MapLayerType.TRAFFIC] = await self.load_traffic_data()
        self.map_layers[MapLayerType.WEATHER] = await self.load_weather_data()
        self.map_layers[MapLayerType.RESTRICTED] = await self.load_restricted_data()
    
    async def load_terrain_data(self) -> Dict:
        """加载地形数据"""
        # 实现地形数据加载逻辑
        return {}
    
    async def load_traffic_data(self) -> Dict:
        """加载交通数据"""
        # 实现交通数据加载逻辑
        return {}
    
    async def load_weather_data(self) -> Dict:
        """加载天气数据"""
        # 实现天气数据加载逻辑
        return {}
    
    async def load_restricted_data(self) -> Dict:
        """加载限飞区数据"""
        # 实现限飞区数据加载逻辑
        return {}
    
    async def load_restricted_areas(self):
        """加载限制区域"""
        # 实现限制区域加载逻辑
        pass
    
    def get_map_layer(self, layer_type: MapLayerType) -> Optional[Dict]:
        """获取指定图层数据"""
        return self.map_layers.get(layer_type)
    
    def add_obstacle(self, obstacle: Dict):
        """添加障碍物"""
        self.obstacles.append(obstacle)
    
    def remove_obstacle(self, obstacle_id: str):
        """移除障碍物"""
        self.obstacles = [obs for obs in self.obstacles if obs['id'] != obstacle_id]
    
    def add_restricted_area(self, area: Dict):
        """添加限制区域"""
        self.restricted_areas.append(area)
    
    def remove_restricted_area(self, area_id: str):
        """移除限制区域"""
        self.restricted_areas = [area for area in self.restricted_areas if area['id'] != area_id]
    
    def is_point_restricted(self, location: Dict) -> bool:
        """检查点是否在限制区域内"""
        lat, lon = location['lat'], location['lon']
        for area in self.restricted_areas:
            if self._point_in_polygon(lat, lon, area['polygon']):
                return True
        return False
    
    def _point_in_polygon(self, lat: float, lon: float, polygon: List[Dict]) -> bool:
        """检查点是否在多边形内"""
        n = len(polygon)
        inside = False
        p1 = polygon[0]
        for i in range(n + 1):
            p2 = polygon[i % n]
            if lon > min(p1['lon'], p2['lon']):
                if lon <= max(p1['lon'], p2['lon']):
                    if lat <= max(p1['lat'], p2['lat']):
                        if p1['lon'] != p2['lon']:
                            lat_inters = (lon - p1['lon']) * (p2['lat'] - p1['lat']) / (p2['lon'] - p1['lon']) + p1['lat']
                            if p1['lat'] == p2['lat'] or lat <= lat_inters:
                                inside = not inside
            p1 = p2
        return inside
    
    def plan_path(
        self,
        start: Dict,
        end: Dict,
        path_type: PathType,
        vehicle_type: str,
        avoid_obstacles: bool = True,
        avoid_restricted: bool = True
    ) -> Optional[List[Dict]]:
        """规划路径"""
        # 检查起点和终点是否在限制区域内
        if avoid_restricted:
            if self.is_point_restricted(start) or self.is_point_restricted(end):
                return None
        
        # 生成路径缓存键
        cache_key = f"{start['lat']},{start['lon']}-{end['lat']},{end['lon']}-{path_type.value}-{vehicle_type}"
        
        # 检查缓存
        if cache_key in self.cached_paths:
            path = self.cached_paths[cache_key]
            if self._is_path_valid(path, avoid_obstacles, avoid_restricted):
                return path
        
        # 根据路径类型选择规划算法
        if path_type == PathType.ROAD:
            path = self._plan_road_path(start, end, vehicle_type, avoid_obstacles, avoid_restricted)
        elif path_type == PathType.AIR:
            path = self._plan_air_path(start, end, vehicle_type, avoid_obstacles, avoid_restricted)
        else:  # HYBRID
            path = self._plan_hybrid_path(start, end, vehicle_type, avoid_obstacles, avoid_restricted)
        
        # 缓存路径
        if path:
            self.cached_paths[cache_key] = path
        
        return path
    
    def _is_path_valid(
        self,
        path: List[Dict],
        avoid_obstacles: bool,
        avoid_restricted: bool
    ) -> bool:
        """检查路径是否有效"""
        if not path:
            return False
        
        for point in path:
            # 检查障碍物
            if avoid_obstacles:
                for obstacle in self.obstacles:
                    if self._is_point_near_obstacle(point, obstacle):
                        return False
            
            # 检查限制区域
            if avoid_restricted and self.is_point_restricted(point):
                return False
        
        return True
    
    def _is_point_near_obstacle(
        self,
        point: Dict,
        obstacle: Dict,
        threshold: float = 0.001  # 约100米
    ) -> bool:
        """检查点是否靠近障碍物"""
        lat_diff = point['lat'] - obstacle['lat']
        lon_diff = point['lon'] - obstacle['lon']
        distance = (lat_diff ** 2 + lon_diff ** 2) ** 0.5
        return distance < threshold
    
    def _plan_road_path(
        self,
        start: Dict,
        end: Dict,
        vehicle_type: str,
        avoid_obstacles: bool,
        avoid_restricted: bool
    ) -> Optional[List[Dict]]:
        """规划道路路径"""
        # 实现道路路径规划算法
        return None
    
    def _plan_air_path(
        self,
        start: Dict,
        end: Dict,
        vehicle_type: str,
        avoid_obstacles: bool,
        avoid_restricted: bool
    ) -> Optional[List[Dict]]:
        """规划空中路径"""
        # 实现空中路径规划算法
        return None
    
    def _plan_hybrid_path(
        self,
        start: Dict,
        end: Dict,
        vehicle_type: str,
        avoid_obstacles: bool,
        avoid_restricted: bool
    ) -> Optional[List[Dict]]:
        """规划混合路径"""
        # 实现混合路径规划算法
        return None
    
    async def update_map_data(self):
        """更新地图数据"""
        # 更新交通数据
        self.map_layers[MapLayerType.TRAFFIC] = await self.load_traffic_data()
        
        # 更新天气数据
        self.map_layers[MapLayerType.WEATHER] = await self.load_weather_data()
        
        # 更新时间戳
        self.last_update = datetime.now()
        
        self.logger.info('地图数据已更新')
    
    def clear_path_cache(self):
        """清除路径缓存"""
        self.cached_paths.clear()
        self.logger.info('路径缓存已清除')
    
    def serialize(self) -> Dict:
        """序列化地图数据"""
        return {
            'map_layers': {
                layer_type.value: layer_data
                for layer_type, layer_data in self.map_layers.items()
            },
            'obstacles': self.obstacles,
            'restricted_areas': self.restricted_areas,
            'last_update': self.last_update.isoformat()
        }
    
    def deserialize(self, data: Dict):
        """反序列化地图数据"""
        self.map_layers = {
            MapLayerType(layer_type): layer_data
            for layer_type, layer_data in data['map_layers'].items()
        }
        self.obstacles = data['obstacles']
        self.restricted_areas = data['restricted_areas']
        self.last_update = datetime.fromisoformat(data['last_update'])