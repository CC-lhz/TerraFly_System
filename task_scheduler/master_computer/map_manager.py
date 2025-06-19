from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from enum import Enum
import numpy as np
import heapq

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
        self.drone_paths = {}  # 存储所有无人机的当前路径
        self.min_drone_distance = 50.0  # 无人机之间的最小安全距离（米）
        self.max_drones_per_zone = 5  # 每个空域允许的最大无人机数量
    
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
        avoid_restricted: bool = True,
        path_params: Dict = None
    ) -> Optional[List[Dict]]:
        """规划路径
        Args:
            start: 起点坐标 {lat: float, lon: float, alt: float}
            end: 终点坐标 {lat: float, lon: float, alt: float}
            path_type: 路径类型
            vehicle_type: 车辆类型 ('car' 或 'drone')
            avoid_obstacles: 是否避开障碍物
            avoid_restricted: 是否避开限制区域
            path_params: 路径参数 {
                speed: float,  # 期望速度
                acceleration: float,  # 加速度
                deceleration: float,  # 减速度
                lookahead_distance: float,  # 前视距离
                max_lateral_error: float,  # 最大横向误差
                waypoint_radius: float  # 航点到达半径
            }
        Returns:
            路径点列表 [{lat: float, lon: float, alt: float, speed: float}]
        """
        # 检查起点和终点是否在限制区域内
        if avoid_restricted:
            if self.is_point_restricted(start) or self.is_point_restricted(end):
                return None
        
        # 设置默认路径参数
        if path_params is None:
            path_params = {
                'speed': 5.0 if vehicle_type == 'car' else 10.0,
                'acceleration': 1.0,
                'deceleration': 1.0,
                'lookahead_distance': 5.0,
                'max_lateral_error': 1.0,
                'waypoint_radius': 3.0
            }
        
        # 生成路径缓存键
        cache_key = f"{start['lat']},{start['lon']}-{end['lat']},{end['lon']}-{path_type.value}-{vehicle_type}"
        
        # 检查缓存
        if cache_key in self.cached_paths:
            path = self.cached_paths[cache_key]
            if self._is_path_valid(path, avoid_obstacles, avoid_restricted):
                return path
        
        # 根据路径类型选择规划算法
        if path_type == PathType.ROAD:
            path = self._plan_road_path(start, end, vehicle_type, avoid_obstacles, avoid_restricted, path_params)
        elif path_type == PathType.AIR:
            path = self._plan_air_path(start, end, vehicle_type, avoid_obstacles, avoid_restricted, path_params)
        else:  # HYBRID
            path = self._plan_hybrid_path(start, end, vehicle_type, avoid_obstacles, avoid_restricted, path_params)
        
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

    def _check_drone_conflicts(
        self,
        point: Dict,
        time_estimate: float,
        drone_id: str,
        path_params: Dict
    ) -> bool:
        """检查指定位置是否与其他无人机路径冲突
        Args:
            point: 待检查的位置点
            time_estimate: 预计到达该点的时间（秒）
            drone_id: 当前无人机ID
            path_params: 路径参数
        Returns:
            True表示有冲突，False表示无冲突
        """
        # 将经纬度转换为米为单位的相对距离
        lat_to_meters = 111000  # 1度纬度约等于111公里
        lon_to_meters = 111000 * np.cos(np.radians(point['lat']))  # 经度随纬度变化

        # 检查该空域的无人机数量
        drones_in_zone = 0
        for other_id, other_path in self.drone_paths.items():
            if other_id == drone_id:
                continue

            # 找到其他无人机在该时间点的预计位置
            other_point = None
            time_passed = 0
            for i in range(len(other_path)):
                if i > 0:
                    dist = self._calculate_distance(other_path[i-1], other_path[i])
                    time_passed += dist / other_path[i]['speed']
                    if time_passed >= time_estimate:
                        other_point = other_path[i]
                        break

            if other_point:
                # 计算水平距离
                lat_diff = (point['lat'] - other_point['lat']) * lat_to_meters
                lon_diff = (point['lon'] - other_point['lon']) * lon_to_meters
                horizontal_dist = np.sqrt(lat_diff**2 + lon_diff**2)

                # 计算垂直距离
                vertical_dist = abs(point['alt'] - other_point['alt'])

                # 如果距离小于安全距离，返回True表示有冲突
                if horizontal_dist < self.min_drone_distance and vertical_dist < 20.0:
                    return True

                # 统计该空域的无人机数量
                if horizontal_dist < 500.0:  # 500米范围内视为同一空域
                    drones_in_zone += 1

        # 如果空域内无人机数量超过限制，返回True表示有冲突
        return drones_in_zone >= self.max_drones_per_zone
    
    def _plan_road_path(
        self,
        start: Dict,
        end: Dict,
        vehicle_type: str,
        avoid_obstacles: bool,
        avoid_restricted: bool,
        path_params: Dict = None
    ) -> Optional[List[Dict]]:
        """规划道路路径
        使用改进的Dijkstra算法在道路网络上规划路径
        考虑道路限速、转弯半径等约束
        """
        if not path_params:
            path_params = {
                'speed': 5.0,
                'acceleration': 1.0,
                'deceleration': 1.0,
                'lookahead_distance': 5.0,
                'max_lateral_error': 1.0,
                'waypoint_radius': 3.0
            }
        
        # 获取道路网络数据
        road_network = self.map_layers.get(MapLayerType.TRAFFIC, {})
        if not road_network:
            return None
        
        # 构建路网图
        graph = {}
        for road in road_network.get('roads', []):
            start_node = (road['start_lat'], road['start_lon'])
            end_node = (road['end_lat'], road['end_lon'])
            speed_limit = road.get('speed_limit', path_params['speed'])
            
            # 添加双向边
            if start_node not in graph:
                graph[start_node] = []
            if end_node not in graph:
                graph[end_node] = []
            
            # 计算边的权重（考虑距离和速度限制）
            weight = self._calculate_edge_weight(start_node, end_node, speed_limit)
            
            graph[start_node].append((end_node, weight, speed_limit))
            graph[end_node].append((start_node, weight, speed_limit))
        
        # 使用Dijkstra算法找到最短路径
        start_point = (start['lat'], start['lon'])
        end_point = (end['lat'], end['lon'])
        
        # 找到最近的道路节点
        start_node = self._find_nearest_node(start_point, graph)
        end_node = self._find_nearest_node(end_point, graph)
        
        if not (start_node and end_node):
            return None
        
        # 运行Dijkstra算法
        path_nodes = self._dijkstra(graph, start_node, end_node)
        if not path_nodes:
            return None
        
        # 构建路径点列表
        path = []
        # 添加起点
        path.append({
            'lat': start['lat'],
            'lon': start['lon'],
            'alt': start.get('alt', 0.0),
            'speed': path_params['speed']
        })
        
        # 添加路径点
        for i in range(len(path_nodes)):
            node = path_nodes[i]
            # 获取当前路段的速度限制
            speed = path_params['speed']
            if i < len(path_nodes) - 1:
                next_node = path_nodes[i + 1]
                for neighbor, _, limit in graph[node]:
                    if neighbor == next_node:
                        speed = min(limit, path_params['speed'])
                        break
            
            path.append({
                'lat': node[0],
                'lon': node[1],
                'alt': 0.0,  # 道路路径的高度为0
                'speed': speed
            })
        
        # 添加终点
        path.append({
            'lat': end['lat'],
            'lon': end['lon'],
            'alt': end.get('alt', 0.0),
            'speed': path_params['speed']
        })
        
        return path
    
    def _plan_air_path(
        self,
        start: Dict,
        end: Dict,
        vehicle_type: str,
        avoid_obstacles: bool,
        avoid_restricted: bool,
        path_params: Dict = None,
        drone_id: str = None
    ) -> Optional[List[Dict]]:
        """规划空中路径
        使用A*算法规划无人机路径，考虑高度、障碍物和其他无人机路径
        实现垂直起降，在巡航高度时只考虑航线冲突
        Args:
            drone_id: 当前规划路径的无人机ID
        """
        if not path_params:
            path_params = {
                'speed': 10.0,  # 巡航速度
                'vertical_speed': 3.0,  # 垂直起降速度
                'acceleration': 2.0,
                'deceleration': 2.0,
                'lookahead_distance': 10.0,
                'max_lateral_error': 2.0,
                'waypoint_radius': 5.0,
                'min_altitude': 20.0,
                'cruise_altitude': 80.0,  # 巡航高度
                'max_altitude': 120.0,
                'grid_size': 0.0001,  # 约10米
                'safe_distance': 50.0  # 无人机间安全距离
            }
        
        # 生成完整的飞行路径（垂直起飞 -> 巡航 -> 垂直降落）
        path = []
        time_estimate = 0
        
        # 1. 垂直起飞阶段
        start_ground = {
            'lat': start['lat'],
            'lon': start['lon'],
            'alt': start.get('alt', 0.0),
            'speed': 0.0
        }
        
        # 添加起飞点
        path.append(start_ground)
        
        # 垂直上升到过渡高度
        transition_height = 30.0  # 过渡高度
        ascent_point = {
            'lat': start['lat'],
            'lon': start['lon'],
            'alt': transition_height,
            'speed': path_params['vertical_speed']
        }
        path.append(ascent_point)
        time_estimate += transition_height / path_params['vertical_speed']
        
        # 加速上升到巡航高度
        cruise_point = {
            'lat': start['lat'],
            'lon': start['lon'],
            'alt': path_params['cruise_altitude'],
            'speed': path_params['speed']
        }
        path.append(cruise_point)
        time_estimate += (path_params['cruise_altitude'] - transition_height) / path_params['speed']
        
        # 2. 巡航阶段 - 使用A*算法规划水平路径
        cruise_start = (start['lat'], start['lon'], path_params['cruise_altitude'])
        cruise_end = (end['lat'], end['lon'], path_params['cruise_altitude'])
        
        # 在巡航高度规划路径
        cruise_nodes = self._astar(cruise_start, cruise_end, path_params, False, drone_id)  # 巡航时不考虑地面障碍物
        if not cruise_nodes:
            return None
        
        # 添加巡航路径点
        for i, node in enumerate(cruise_nodes[1:-1]):  # 跳过起点和终点，因为已经包含在路径中
            point = {
                'lat': node[0],
                'lon': node[1],
                'alt': node[2],
                'speed': path_params['speed']
            }
            
            # 检查与其他无人机的冲突
            if self._check_drone_conflicts(point, time_estimate, drone_id, path_params):
                # 如果存在冲突，尝试调整高度
                point['alt'] += path_params['safe_distance']
                if point['alt'] > path_params['max_altitude']:
                    point['alt'] -= 2 * path_params['safe_distance']
            
            path.append(point)
            
            # 更新时间估计
            if i > 0:
                dist = self._calculate_distance(path[-2], point)
                time_estimate += dist / path_params['speed']
        
        # 3. 降落阶段
        # 减速下降到过渡高度
        descent_point = {
            'lat': end['lat'],
            'lon': end['lon'],
            'alt': transition_height,
            'speed': path_params['vertical_speed']
        }
        path.append(descent_point)
        time_estimate += (path_params['cruise_altitude'] - transition_height) / path_params['speed']
        
        # 垂直降落到地面
        end_ground = {
            'lat': end['lat'],
            'lon': end['lon'],
            'alt': end.get('alt', 0.0),
            'speed': 0.0
        }
        path.append(end_ground)
        time_estimate += transition_height / path_params['vertical_speed']
        
        # 更新无人机路径记录
        if drone_id:
            self.drone_paths[drone_id] = path
        
        return path
        
        # 如果找到可行路径，更新无人机路径记录
        if best_path and drone_id:
            self.drone_paths[drone_id] = best_path
        
        return best_path

    def _astar(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        path_params: Dict,
        avoid_obstacles: bool,
        drone_id: str = None
    ) -> Optional[List[Tuple[float, float, float]]]:
        """使用A*算法进行路径规划
        考虑高度、障碍物和其他无人机的路径
        """
        def heuristic(node: Tuple[float, float, float]) -> float:
            """启发式函数：估计从当前节点到终点的成本
            使用欧几里得距离作为基础，考虑高度差异和其他无人机的影响
            """
            # 计算直线距离
            lat_diff = (node[0] - end[0]) * 111000  # 转换为米
            lon_diff = (node[1] - end[1]) * 111000 * np.cos(np.radians(node[0]))
            alt_diff = node[2] - end[2]
            distance = np.sqrt(lat_diff**2 + lon_diff**2 + alt_diff**2)
            
            # 检查该点是否与其他无人机路径冲突
            point = {'lat': node[0], 'lon': node[1], 'alt': node[2]}
            if self._check_drone_conflicts(point, 0, drone_id, path_params):
                return distance * 2  # 如果有冲突，增加成本
            
            return distance
        
        def get_neighbors(node: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
            """获取相邻节点
            在三维空间中生成可能的移动方向
            """
            neighbors = []
            grid_size = path_params['grid_size']
            alt_step = path_params['altitude_step'] / 2  # 使用较小的高度步长
            
            # 水平方向的移动
            for dlat in [-grid_size, 0, grid_size]:
                for dlon in [-grid_size, 0, grid_size]:
                    for dalt in [-alt_step, 0, alt_step]:
                        if dlat == 0 and dlon == 0 and dalt == 0:
                            continue
                        
                        new_lat = node[0] + dlat
                        new_lon = node[1] + dlon
                        new_alt = node[2] + dalt
                        
                        # 检查高度限制
                        if not (path_params['min_altitude'] <= new_alt <= path_params['max_altitude']):
                            continue
                        
                        # 检查节点是否有效
                        if self._is_node_valid((new_lat, new_lon, new_alt), avoid_obstacles):
                            neighbors.append((new_lat, new_lon, new_alt))
            
            return neighbors
        
        def reconstruct_path(came_from: Dict, current: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
            """重建路径"""
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]
        
        # 初始化开放集和关闭集
        open_set = {start}
        closed_set = set()
        
        # 记录来源节点
        came_from = {}
        
        # 记录从起点到达每个节点的实际成本
        g_score = {start: 0}
        
        # 记录从起点经过每个节点到达终点的估计总成本
        f_score = {start: heuristic(start)}
        
        while open_set:
            # 获取f_score最小的节点
            current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
            
            # 如果到达终点附近
            if abs(current[0] - end[0]) < path_params['grid_size'] and \
               abs(current[1] - end[1]) < path_params['grid_size'] and \
               abs(current[2] - end[2]) < path_params['altitude_step']:
                return reconstruct_path(came_from, current)
            
            open_set.remove(current)
            closed_set.add(current)
            
            # 检查所有相邻节点
            for neighbor in get_neighbors(current):
                if neighbor in closed_set:
                    continue
                
                # 计算经过当前节点到达相邻节点的成本
                tentative_g_score = g_score[current] + heuristic(neighbor)
                
                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue
                
                # 这是一条更好的路径，记录下来
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor)
        
        return None
    
    def _is_node_valid(
        self,
        node: Tuple[float, float, float],
        avoid_obstacles: bool
    ) -> bool:
        """检查节点是否有效
        检查是否在地图范围内，是否与障碍物碰撞
        在飞行高度时不考虑地面障碍物，仅在起降时检查
        """
        point = {'lat': node[0], 'lon': node[1], 'alt': node[2]}
        
        # 检查是否在限制区域内
        if self.is_point_restricted(point):
            return False
        
        # 仅在低空（起降阶段）检查障碍物
        min_safe_altitude = 30.0  # 安全飞行高度（米）
        if avoid_obstacles and point['alt'] < min_safe_altitude:
            for obstacle in self.obstacles:
                if self._is_point_near_obstacle(point, obstacle):
                    return False
        
        return True
    
    def _plan_hybrid_path(
        self,
        start: Dict,
        end: Dict,
        vehicle_type: str,
        avoid_obstacles: bool,
        avoid_restricted: bool,
        path_params: Dict = None,
        drone_id: str = None
    ) -> Optional[List[Dict]]:
        """规划混合路径
        结合道路和空中路径规划，根据实际情况选择最优路径
        对于无人机，可以在部分路段使用道路上方的空域，部分路段使用直线飞行
        对于车辆，可以在合适的地方使用非道路区域作为捷径
        """
        if not path_params:
            path_params = {
                'speed': 10.0 if vehicle_type == 'drone' else 5.0,
                'acceleration': 2.0,
                'deceleration': 2.0,
                'lookahead_distance': 10.0,
                'max_lateral_error': 2.0,
                'waypoint_radius': 5.0,
                'min_altitude': 20.0,
                'max_altitude': 120.0,
                'grid_size': 0.0001,  # 约10米
                'altitude_levels': 5,  # 可选择的高度层数
                'altitude_step': 20.0  # 高度层间隔（米）
            }
        
        # 对于车辆，直接使用道路路径
        if vehicle_type == 'car':
            return self._plan_road_path(start, end, vehicle_type, avoid_obstacles, avoid_restricted, path_params)
        
        # 对于无人机，尝试多种路径组合
        paths = []
        
        # 1. 纯空中路径
        air_path = self._plan_air_path(start, end, vehicle_type, avoid_obstacles, avoid_restricted, path_params, drone_id)
        if air_path:
            paths.append({
                'path': air_path,
                'type': 'air',
                'length': self._calculate_path_length(air_path)
            })
        
        # 2. 道路上方路径（在道路路径基础上调整高度）
        road_path = self._plan_road_path(start, end, vehicle_type, avoid_obstacles, avoid_restricted, path_params)
        if road_path:
            # 将道路路径转换为空中路径（在道路上方飞行）
            above_road_path = []
            for point in road_path:
                above_road_path.append({
                    'lat': point['lat'],
                    'lon': point['lon'],
                    'alt': path_params['min_altitude'],  # 在道路上方固定高度飞行
                    'speed': point['speed']
                })
            
            paths.append({
                'path': above_road_path,
                'type': 'above_road',
                'length': self._calculate_path_length(above_road_path)
            })
        
        # 3. 混合路径（部分使用道路上方，部分使用直线飞行）
        if road_path and len(road_path) > 2:
            # 选择道路路径的中间点作为转换点
            mid_idx = len(road_path) // 2
            mid_point = {
                'lat': road_path[mid_idx]['lat'],
                'lon': road_path[mid_idx]['lon'],
                'alt': path_params['min_altitude'],
                'speed': path_params['speed']
            }
            
            # 规划两段空中路径
            path1 = self._plan_air_path(start, mid_point, vehicle_type, avoid_obstacles, avoid_restricted, path_params, drone_id)
            path2 = self._plan_air_path(mid_point, end, vehicle_type, avoid_obstacles, avoid_restricted, path_params, drone_id)
            
            if path1 and path2:
                hybrid_path = path1[:-1] + path2  # 去掉重复的中间点
                paths.append({
                    'path': hybrid_path,
                    'type': 'hybrid',
                    'length': self._calculate_path_length(hybrid_path)
                })
        
        if not paths:
            return None
        
        # 选择最优路径（根据路径长度和冲突数量）
        best_path = None
        min_cost = float('inf')
        
        for path_info in paths:
            # 计算路径成本（考虑长度和冲突）
            conflicts = 0
            time_estimate = 0
            
            for i, point in enumerate(path_info['path']):
                if i > 0:
                    prev_point = path_info['path'][i-1]
                    dist = self._calculate_distance(prev_point, point)
                    time_estimate += dist / point['speed']
                
                if self._check_drone_conflicts(point, time_estimate, drone_id, path_params):
                    conflicts += 1
            
            # 成本 = 路径长度 + 冲突数量 * 惩罚因子
            cost = path_info['length'] + conflicts * 1000  # 1000米的惩罚因子
            
            if cost < min_cost:
                min_cost = cost
                best_path = path_info['path']
        
        # 更新无人机路径记录
        if best_path and drone_id:
            self.drone_paths[drone_id] = best_path
        
        return best_path
        
    def _calculate_path_length(self, path: List[Dict]) -> float:
        """计算路径长度
        使用Haversine公式计算两点间的距离，考虑高度差异
        """
        if not path or len(path) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(1, len(path)):
            total_length += self._calculate_distance(path[i-1], path[i])
        
        return total_length
    
    def _calculate_distance(self, point1: Dict, point2: Dict) -> float:
        """计算两点间的距离
        使用Haversine公式计算地理距离，并考虑高度差异
        """
        # 地球半径（米）
        R = 6371000
        
        # 将经纬度转换为弧度
        lat1 = np.radians(point1['lat'])
        lon1 = np.radians(point1['lon'])
        lat2 = np.radians(point2['lat'])
        lon2 = np.radians(point2['lon'])
        
        # 计算经纬度差值
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Haversine公式
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        horizontal_distance = R * c
        
        # 计算高度差
        alt1 = point1.get('alt', 0.0)
        alt2 = point2.get('alt', 0.0)
        vertical_distance = abs(alt2 - alt1)
        
        # 计算总距离（三维空间中的欧几里得距离）
        return np.sqrt(horizontal_distance**2 + vertical_distance**2)
        
        # 尝试规划空中路径
        air_path = self._plan_air_path(start, end, vehicle_type, avoid_obstacles, avoid_restricted, path_params)
        
        # 根据路径长度、安全性等因素选择最优路径
        if road_path and air_path:
            # 计算路径长度
            road_length = self._calculate_path_length(road_path)
            air_length = self._calculate_path_length(air_path)
            
            # 如果空中路径比道路路径短很多，选择空中路径
            if air_length < road_length * 0.8:
                return air_path
            return road_path
        
        # 如果只有一种路径可用，返回该路径
        return road_path or air_path
    
    def _calculate_path_length(self, path: List[Dict]) -> float:
        """计算路径长度
        使用Haversine公式计算两点之间的距离，考虑高度差
        """
        if not path or len(path) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(len(path) - 1):
            p1, p2 = path[i], path[i + 1]
            # 计算水平距离
            lat1, lon1 = p1['lat'], p1['lon']
            lat2, lon2 = p2['lat'], p2['lon']
            R = 6371000  # 地球半径（米）
            
            # 将经纬度转换为弧度
            lat1, lon1 = np.radians(lat1), np.radians(lon1)
            lat2, lon2 = np.radians(lat2), np.radians(lon2)
            
            # Haversine公式
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            horizontal_distance = R * c
            
            # 计算高度差
            alt1 = p1.get('alt', 0.0)
            alt2 = p2.get('alt', 0.0)
            vertical_distance = abs(alt2 - alt1)
            
            # 计算三维距离
            distance = np.sqrt(horizontal_distance**2 + vertical_distance**2)
            total_length += distance
        
        return total_length

    def _calculate_edge_weight(self, node1: Tuple[float, float], node2: Tuple[float, float], speed_limit: float) -> float:
        """计算路网图中边的权重
        考虑距离和速度限制
        """
        # 计算两点间的距离
        lat1, lon1 = node1
        lat2, lon2 = node2
        distance = self._calculate_distance(lat1, lon1, lat2, lon2)
        
        # 考虑速度限制，权重为预计通过时间
        weight = distance / speed_limit
        return weight
    
    def _find_nearest_node(self, point: Tuple[float, float], graph: Dict) -> Optional[Tuple[float, float]]:
        """找到路网图中距离给定点最近的节点"""
        if not graph:
            return None
        
        nearest_node = None
        min_distance = float('inf')
        
        for node in graph.keys():
            distance = self._calculate_distance(point[0], point[1], node[0], node[1])
            if distance < min_distance:
                min_distance = distance
                nearest_node = node
        
        return nearest_node
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间的距离（米）"""
        R = 6371000  # 地球半径（米）
        
        # 将经纬度转换为弧度
        lat1, lon1 = np.radians(lat1), np.radians(lon1)
        lat2, lon2 = np.radians(lat2), np.radians(lon2)
        
        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _dijkstra(self, graph: Dict, start: Tuple[float, float], end: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """Dijkstra算法实现
        返回从起点到终点的最短路径
        """
        if start not in graph or end not in graph:
            return None
        
        # 初始化距离字典和前驱节点字典
        distances = {node: float('inf') for node in graph}
        distances[start] = 0
        predecessors = {node: None for node in graph}
        
        # 优先队列，存储(距离, 节点)元组
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            
            if current_node == end:
                break
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # 遍历当前节点的所有邻居
            for neighbor, weight, _ in graph[current_node]:
                if neighbor in visited:
                    continue
                
                distance = current_distance + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    predecessors[neighbor] = current_node
                    heapq.heappush(pq, (distance, neighbor))
        
        # 构建路径
        if predecessors[end] is None:
            return None
        
        path = []
        current_node = end
        while current_node is not None:
            path.append(current_node)
            current_node = predecessors[current_node]
        
        return list(reversed(path))

    def _astar(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        path_params: Dict,
        avoid_obstacles: bool
    ) -> Optional[List[Tuple[float, float, float]]]:
        """A*算法实现
        考虑三维空间中的路径规划，包括高度
        """
        def heuristic(node: Tuple[float, float, float]) -> float:
            # 使用欧几里得距离作为启发函数
            lat_diff = end[0] - node[0]
            lon_diff = end[1] - node[1]
            alt_diff = end[2] - node[2]
            return np.sqrt(lat_diff**2 + lon_diff**2 + alt_diff**2)
        
        def get_neighbors(node: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
            # 生成3D网格中的邻居节点
            neighbors = []
            grid_size = path_params['grid_size']
            alt_step = 10.0  # 高度步长（米）
            
            # 水平方向的8个邻居
            for dlat, dlon in [(0, 1), (1, 0), (0, -1), (-1, 0),
                              (1, 1), (-1, 1), (-1, -1), (1, -1)]:
                new_lat = node[0] + dlat * grid_size
                new_lon = node[1] + dlon * grid_size
                
                # 保持当前高度的邻居
                neighbors.append((new_lat, new_lon, node[2]))
                
                # 添加上下高度的邻居
                if node[2] + alt_step <= path_params['max_altitude']:
                    neighbors.append((new_lat, new_lon, node[2] + alt_step))
                if node[2] - alt_step >= path_params['min_altitude']:
                    neighbors.append((new_lat, new_lon, node[2] - alt_step))
            
            return neighbors
        
        def is_valid(node: Tuple[float, float, float]) -> bool:
            # 检查节点是否有效（在范围内且不与障碍物碰撞）
            if not (path_params['min_altitude'] <= node[2] <= path_params['max_altitude']):
                return False
            
            if avoid_obstacles:
                for obstacle in self.obstacles:
                    # 检查水平距离
                    dist = self._calculate_distance(node[0], node[1],
                                                  obstacle[0], obstacle[1])
                    if dist < obstacle[2]:  # 如果在障碍物半径内
                        # 检查高度是否与障碍物重叠
                        if node[2] < obstacle[3]:  # obstacle[3]是障碍物高度
                            return False
            
            return True
        
        # 初始化开放列表和关闭列表
        open_set = {start}
        closed_set = set()
        
        # 记录路径信息
        came_from = {}
        
        # 记录代价值
        g_score = {start: 0}
        f_score = {start: heuristic(start)}
        
        while open_set:
            # 获取f值最小的节点
            current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
            
            if self._calculate_distance(current[0], current[1], end[0], end[1]) < path_params['waypoint_radius'] \
               and abs(current[2] - end[2]) < alt_step:
                # 重建路径
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return list(reversed(path))
            
            open_set.remove(current)
            closed_set.add(current)
            
            # 检查所有邻居
            for neighbor in get_neighbors(current):
                if neighbor in closed_set or not is_valid(neighbor):
                    continue
                
                # 计算通过当前节点到达邻居的代价
                tentative_g_score = g_score[current] + \
                    np.sqrt(sum((a - b) ** 2 for a, b in zip(current, neighbor)))
                
                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue
                
                # 这是目前找到的最佳路径，记录下来
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor)
        
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