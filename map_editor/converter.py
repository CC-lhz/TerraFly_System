from typing import Dict, List, Optional, Union
from datetime import datetime

from models import (
    ObjectType, ZoneType, PathType,
    Position, MapObject, StaticObject,
    DynamicZone, Path, MapData
)

class MapConverter:
    """地图数据转换器，用于在编辑器格式和主控系统格式之间转换"""
    
    @staticmethod
    def to_master_format(map_data: MapData) -> Dict:
        """将编辑器格式转换为主控系统格式"""
        master_data = {
            'map_layers': {
                'terrain': {},
                'traffic': {},
                'weather': {},
                'restricted': {},
                'custom': {}
            },
            'obstacles': [],
            'restricted_areas': [],
            'last_update': datetime.now().isoformat()
        }
        
        # 处理所有对象
        for obj in map_data.objects:
            if isinstance(obj, StaticObject):
                # 静态对象转换为障碍物
                if obj.type in [ObjectType.OBSTACLE, ObjectType.BUILDING]:
                    obstacle = {
                        'id': obj.id,
                        'lat': obj.position.lat,
                        'lon': obj.position.lon,
                        'radius': obj.radius,
                        'height': obj.height,
                        'name': obj.name,
                        'type': obj.type.value,
                        'properties': obj.properties
                    }
                    master_data['obstacles'].append(obstacle)
                # 地标和站点添加到自定义图层
                elif obj.type in [ObjectType.LANDMARK, ObjectType.STATION]:
                    custom_obj = obj.to_dict()
                    master_data['map_layers']['custom'][obj.id] = custom_obj
            
            elif isinstance(obj, DynamicZone):
                # 区域对象转换
                zone_data = {
                    'id': obj.id,
                    'type': obj.type.value,
                    'points': [(p.lat, p.lon) for p in obj.points],
                    'name': obj.name,
                    'properties': obj.properties
                }
                
                # 根据区域类型添加到对应图层
                if obj.type == ZoneType.RESTRICTED:
                    master_data['restricted_areas'].append(zone_data)
                else:
                    layer_name = obj.type.value
                    master_data['map_layers'][layer_name][obj.id] = zone_data
            
            elif isinstance(obj, Path):
                # 路径对象添加到交通图层
                path_data = {
                    'id': obj.id,
                    'type': obj.type.value,
                    'points': [(p.lat, p.lon, p.alt) for p in obj.points],
                    'name': obj.name,
                    'properties': obj.properties
                }
                master_data['map_layers']['traffic'][obj.id] = path_data
        
        return master_data
    
    @staticmethod
    def from_master_format(master_data: Dict) -> MapData:
        """将主控系统格式转换为编辑器格式"""
        map_data = MapData()
        
        # 转换障碍物
        for obstacle in master_data.get('obstacles', []):
            obj = StaticObject(
                id=obstacle['id'],
                type=ObjectType.OBSTACLE if obstacle.get('type') == 'obstacle' else ObjectType.BUILDING,
                position=Position(
                    lat=obstacle['lat'],
                    lon=obstacle['lon'],
                    alt=0.0
                ),
                name=obstacle.get('name', ''),
                radius=obstacle.get('radius', 0.0),
                height=obstacle.get('height', 0.0),
                properties=obstacle.get('properties', {})
            )
            map_data.objects.append(obj)
        
        # 转换限制区域
        for area in master_data.get('restricted_areas', []):
            zone = DynamicZone(
                id=area['id'],
                type=ZoneType.RESTRICTED,
                points=[Position(lat=p[0], lon=p[1]) for p in area['points']],
                name=area.get('name', ''),
                properties=area.get('properties', {})
            )
            map_data.objects.append(zone)
        
        # 转换图层数据
        for layer_type, layer_data in master_data.get('map_layers', {}).items():
            if isinstance(layer_data, dict):
                for obj_id, obj_data in layer_data.items():
                    if 'type' in obj_data:
                        if obj_data['type'] in [t.value for t in PathType]:
                            # 转换路径
                            path = Path(
                                id=obj_id,
                                type=PathType(obj_data['type']),
                                points=[Position(lat=p[0], lon=p[1], alt=p[2] if len(p) > 2 else 0.0)
                                        for p in obj_data['points']],
                                name=obj_data.get('name', ''),
                                properties=obj_data.get('properties', {})
                            )
                            map_data.objects.append(path)
                        elif obj_data['type'] in [t.value for t in ZoneType]:
                            # 转换区域
                            zone = DynamicZone(
                                id=obj_id,
                                type=ZoneType(layer_type),
                                points=[Position(lat=p[0], lon=p[1]) for p in obj_data['points']],
                                name=obj_data.get('name', ''),
                                properties=obj_data.get('properties', {})
                            )
                            map_data.objects.append(zone)
                        elif obj_data['type'] in [t.value for t in ObjectType]:
                            # 转换静态对象
                            obj = StaticObject(
                                id=obj_id,
                                type=ObjectType(obj_data['type']),
                                position=Position(
                                    lat=obj_data['position']['lat'],
                                    lon=obj_data['position']['lon'],
                                    alt=obj_data['position'].get('alt', 0.0)
                                ),
                                name=obj_data.get('name', ''),
                                radius=obj_data.get('radius', 0.0),
                                height=obj_data.get('height', 0.0),
                                properties=obj_data.get('properties', {})
                            )
                            map_data.objects.append(obj)
        
        return map_data