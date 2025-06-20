from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
import json

class ObjectType(Enum):
    """地图对象类型"""
    OBSTACLE = 'obstacle'  # 障碍物
    BUILDING = 'building'  # 建筑物
    LANDMARK = 'landmark'  # 地标
    STATION = 'station'    # 站点

class ZoneType(Enum):
    """区域类型"""
    RESTRICTED = 'restricted'  # 限制区域
    TRAFFIC = 'traffic'       # 交通区域
    WEATHER = 'weather'       # 天气区域
    CUSTOM = 'custom'         # 自定义区域

class PathType(Enum):
    """路径类型"""
    ROAD = 'road'      # 道路路径
    AIR = 'air'        # 空中路径
    HYBRID = 'hybrid'  # 混合路径

@dataclass
class Position:
    """位置信息"""
    lat: float  # 纬度
    lon: float  # 经度
    alt: float = 0.0  # 高度（米）

    def to_dict(self) -> Dict:
        return {
            'lat': self.lat,
            'lon': self.lon,
            'alt': self.alt
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Position':
        return cls(
            lat=data['lat'],
            lon=data['lon'],
            alt=data.get('alt', 0.0)
        )

@dataclass
class MapObject:
    """地图对象基类"""
    id: str
    type: ObjectType
    position: Position
    name: str = ''
    description: str = ''
    properties: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'position': self.position.to_dict(),
            'name': self.name,
            'description': self.description,
            'properties': self.properties
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MapObject':
        return cls(
            id=data['id'],
            type=ObjectType(data['type']),
            position=Position.from_dict(data['position']),
            name=data.get('name', ''),
            description=data.get('description', ''),
            properties=data.get('properties', {})
        )

@dataclass
class StaticObject(MapObject):
    """静态对象（如建筑物、障碍物等）"""
    radius: float = 0.0  # 半径（米）
    height: float = 0.0  # 高度（米）

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'radius': self.radius,
            'height': self.height
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'StaticObject':
        obj = super().from_dict(data)
        return cls(
            id=obj.id,
            type=obj.type,
            position=obj.position,
            name=obj.name,
            description=obj.description,
            properties=obj.properties,
            radius=data.get('radius', 0.0),
            height=data.get('height', 0.0)
        )

@dataclass
class DynamicZone:
    """动态区域（如限飞区、天气区等）"""
    id: str
    type: ZoneType
    points: List[Position]  # 多边形顶点
    name: str = ''
    description: str = ''
    properties: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'points': [p.to_dict() for p in self.points],
            'name': self.name,
            'description': self.description,
            'properties': self.properties
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'DynamicZone':
        return cls(
            id=data['id'],
            type=ZoneType(data['type']),
            points=[Position.from_dict(p) for p in data['points']],
            name=data.get('name', ''),
            description=data.get('description', ''),
            properties=data.get('properties', {})
        )

@dataclass
class Path:
    """路径"""
    id: str
    type: PathType
    points: List[Position]
    name: str = ''
    description: str = ''
    properties: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'points': [p.to_dict() for p in self.points],
            'name': self.name,
            'description': self.description,
            'properties': self.properties
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Path':
        return cls(
            id=data['id'],
            type=PathType(data['type']),
            points=[Position.from_dict(p) for p in data['points']],
            name=data.get('name', ''),
            description=data.get('description', ''),
            properties=data.get('properties', {})
        )

@dataclass
class MapData:
    """地图数据"""
    objects: List[Union[StaticObject, DynamicZone, Path]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'objects': [obj.to_dict() for obj in self.objects]
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict) -> 'MapData':
        objects = []
        for obj_data in data.get('objects', []):
            if 'type' in obj_data:
                if obj_data['type'] in [t.value for t in ObjectType]:
                    objects.append(StaticObject.from_dict(obj_data))
                elif obj_data['type'] in [t.value for t in ZoneType]:
                    objects.append(DynamicZone.from_dict(obj_data))
                elif obj_data['type'] in [t.value for t in PathType]:
                    objects.append(Path.from_dict(obj_data))
        return cls(objects=objects)

    @classmethod
    def from_json(cls, json_str: str) -> 'MapData':
        return cls.from_dict(json.loads(json_str))