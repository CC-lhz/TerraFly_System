import requests
import folium
from typing import List, Tuple, Dict
from dataclasses import dataclass
import json
from .map_planner import MapPlanner, MapPoint

class BaiduMapPlanner(MapPlanner):
    def __init__(self, center: Tuple[float, float], zoom_start: int = 13, ak: str = None):
        super().__init__(center, zoom_start)
        self.ak = ak  # 百度地图API密钥
        self.base_url = "http://api.map.baidu.com"

    def get_global_path(self, start: Tuple[float, float], goal: Tuple[float, float], vehicle_type: str = "driving") -> List[Tuple[float, float]]:
        """使用百度地图API获取全局路径规划
        vehicle_type: driving-驾车, walking-步行, riding-骑行
        """
        if not self.ak:
            raise ValueError("需要设置百度地图API密钥(ak)")

        # 构建路径规划API请求
        url = f"{self.base_url}/direction/v2/{vehicle_type}"
        params = {
            "origin": f"{start[0]},{start[1]}",
            "destination": f"{goal[0]},{goal[1]}",
            "ak": self.ak,
            "coord_type": "bd09ll",  # 百度经纬度坐标
            "ret_coordtype": "bd09ll"
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data["status"] == 0:
                # 提取路径点
                route = data["result"]["routes"][0]
                path_points = []
                
                for step in route["steps"]:
                    # 解析每个路段的路径点
                    path = step["path"].split(";")  # 百度地图返回的路径点格式为"lng,lat;lng,lat"
                    points = [(float(p.split(",")[1]), float(p.split(",")[0])) for p in path]  # 转换为(lat, lon)格式
                    path_points.extend(points)
                
                return path_points
            else:
                raise Exception(f"百度地图API请求失败: {data['message']}")

        except Exception as e:
            print(f"获取全局路径失败: {str(e)}")
            return None

    def plan_path(self, start: Tuple[float, float], goal: Tuple[float, float], 
                  vehicle_type: str = "driving", use_local: bool = False) -> List[Tuple[float, float]]:
        """综合路径规划
        首先尝试使用百度地图API获取全局路径，如果失败或遇到局部障碍，则使用本地路径规划算法
        """
        if not use_local:
            # 尝试使用百度地图API获取全局路径
            global_path = self.get_global_path(start, goal, vehicle_type)
            if global_path:
                # 检查路径是否与障碍物相交
                has_collision = False
                for point in global_path:
                    if self.check_collision(point):
                        has_collision = True
                        break
                
                if not has_collision:
                    return global_path

        # 如果全局路径规划失败或遇到障碍，使用本地路径规划
        if vehicle_type == "driving":
            return self.rrt_path(start, goal)  # 地面车辆使用RRT算法
        else:
            return self.a_star_path(start, goal)  # 无人机使用A*算法

    def draw_path(self, path: List[Tuple[float, float]], color: str = 'blue', weight: int = 3, 
                  start_icon: str = 'green', goal_icon: str = 'red'):
        """在地图上绘制路径，支持自定义起点和终点图标颜色"""
        if len(path) < 2:
            return

        # 绘制路径线
        folium.PolyLine(
            locations=path,
            weight=weight,
            color=color,
            opacity=0.8
        ).add_to(self.map)

        # 添加起点标记
        folium.Marker(
            location=path[0],
            popup='Start',
            icon=folium.Icon(color=start_icon)
        ).add_to(self.map)

        # 添加终点标记
        folium.Marker(
            location=path[-1],
            popup='Goal',
            icon=folium.Icon(color=goal_icon)
        ).add_to(self.map)