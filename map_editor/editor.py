from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QPalette

from typing import Dict, List, Optional, Tuple, Union
from uuid import uuid4

from .models import (
    ObjectType, ZoneType, PathType,
    Position, MapObject, StaticObject,
    DynamicZone, Path, MapData
)
from .signals import MapEditorSignals

class MapEditor(QWidget):
    """地图编辑器主类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = MapEditorSignals()
        
        # 初始化数据
        self.map_data = MapData()
        self.selected_object = None
        self.current_tool = None
        
        # 视图参数
        self.center_lat = 39.9  # 北京市中心纬度
        self.center_lon = 116.3  # 北京市中心经度
        self.zoom_level = 100.0  # 缩放级别（像素/度）
        self.grid_size = 50  # 网格大小（像素）
        
        # 编辑状态
        self.is_drawing = False
        self.temp_points = []
        
        # 初始化UI
        self._init_ui()
        
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 设置最小尺寸
        self.setMinimumSize(800, 600)
        
        # 设置焦点策略
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # 设置背景色
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor('#f0f0f0'))
        self.setPalette(palette)
    
    def paintEvent(self, event):
        """绘制地图"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor('#f0f0f0'))
        
        # 绘制网格
        self._draw_grid(painter)
        
        # 绘制地图对象
        self._draw_objects(painter)
        
        # 绘制临时图形
        if self.is_drawing and self.temp_points:
            self._draw_temp_shape(painter)
    
    def _draw_grid(self, painter: QPainter):
        """绘制网格"""
        pen = QPen(QColor('#e0e0e0'))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 计算网格线
        width = self.width()
        height = self.height()
        
        # 绘制经纬度网格
        for x in range(0, width, int(self.grid_size * self.zoom_level)):
            painter.drawLine(x, 0, x, height)
        for y in range(0, height, int(self.grid_size * self.zoom_level)):
            painter.drawLine(0, y, width, y)
    
    def _draw_objects(self, painter: QPainter):
        """绘制地图对象"""
        for obj in self.map_data.objects:
            if isinstance(obj, StaticObject):
                self._draw_static_object(painter, obj)
            elif isinstance(obj, DynamicZone):
                self._draw_dynamic_zone(painter, obj)
            elif isinstance(obj, Path):
                self._draw_path(painter, obj)
    
    def _draw_static_object(self, painter: QPainter, obj: StaticObject):
        """绘制静态对象"""
        pen = QPen(QColor('blue') if obj != self.selected_object else QColor('red'))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # 计算屏幕坐标
        pos = self._geo_to_screen(obj.position.lat, obj.position.lon)
        radius = obj.radius * self.zoom_level
        
        # 绘制圆形
        painter.drawEllipse(pos, radius, radius)
    
    def _draw_dynamic_zone(self, painter: QPainter, zone: DynamicZone):
        """绘制动态区域"""
        pen = QPen(QColor('green') if zone != self.selected_object else QColor('red'))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # 绘制多边形
        points = [self._geo_to_screen(p.lat, p.lon) for p in zone.points]
        if len(points) > 1:
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
            painter.drawLine(points[-1], points[0])
    
    def _draw_path(self, painter: QPainter, path: Path):
        """绘制路径"""
        pen = QPen(QColor('purple') if path != self.selected_object else QColor('red'))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # 绘制路径线
        points = [self._geo_to_screen(p.lat, p.lon) for p in path.points]
        if len(points) > 1:
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
    
    def _draw_temp_shape(self, painter: QPainter):
        """绘制临时图形"""
        pen = QPen(QColor('gray'))
        pen.setWidth(1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        if self.current_tool in ['obstacle', 'building', 'landmark', 'station'] and len(self.temp_points) == 2:
            # 绘制临时圆形
            center = self._geo_to_screen(self.temp_points[0].lat, self.temp_points[0].lon)
            edge = self._geo_to_screen(self.temp_points[1].lat, self.temp_points[1].lon)
            radius = ((center.x() - edge.x()) ** 2 + (center.y() - edge.y()) ** 2) ** 0.5
            painter.drawEllipse(center, radius, radius)
        else:
            # 绘制临时点和线
            points = [self._geo_to_screen(p.lat, p.lon) for p in self.temp_points]
            if len(points) > 1:
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
    
    def _geo_to_screen(self, lat: float, lon: float) -> QPointF:
        """将地理坐标转换为屏幕坐标"""
        x = (lon - self.center_lon) * self.zoom_level * 10000 + self.width() / 2
        y = (self.center_lat - lat) * self.zoom_level * 10000 + self.height() / 2
        return QPointF(x, y)
    
    def _screen_to_geo(self, x: float, y: float) -> Tuple[float, float]:
        """将屏幕坐标转换为地理坐标"""
        lon = (x - self.width() / 2) / (self.zoom_level * 10000) + self.center_lon
        lat = self.center_lat - (y - self.height() / 2) / (self.zoom_level * 10000)
        return lat, lon
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 获取地理坐标
            lat, lon = self._screen_to_geo(event.pos().x(), event.pos().y())
            
            if self.current_tool == 'select':
                # 选择对象
                self._select_object_at(lat, lon)
            elif self.current_tool in ['obstacle', 'building', 'landmark', 'station']:
                # 开始绘制静态对象
                self.is_drawing = True
                self.temp_points = [Position(lat=lat, lon=lon), Position(lat=lat, lon=lon)]  # 起点和临时点
            elif self.current_tool in ['restricted', 'traffic', 'weather', 'custom', 'road', 'air', 'hybrid']:
                # 如果已经在绘制中，添加新的点
                if self.is_drawing:
                    # 移除临时预览点
                    if self.temp_points:
                        self.temp_points.pop()
                    # 添加新的固定点
                    self.temp_points.append(Position(lat=lat, lon=lon))
                    # 添加新的临时预览点
                    self.temp_points.append(Position(lat=lat, lon=lon))
                else:
                    # 开始新的绘制
                    self.is_drawing = True
                    self.temp_points.append(Position(lat=lat, lon=lon))
                    self.temp_points.append(Position(lat=lat, lon=lon))  # 临时预览点
        
        self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        lat, lon = self._screen_to_geo(event.pos().x(), event.pos().y())
        
        # 如果正在绘制，更新临时点
        if self.is_drawing and self.temp_points:
            if self.current_tool in ['obstacle', 'building', 'landmark', 'station']:
                # 更新临时点并计算半径
                self.temp_points[1] = Position(lat=lat, lon=lon)
                self.update()
            elif self.current_tool in ['restricted', 'traffic', 'weather', 'custom', 'road', 'air', 'hybrid']:
                # 更新最后一个点的位置，用于实时预览
                self.temp_points[-1] = Position(lat=lat, lon=lon)
                self.update()
        else:
            # 更新状态栏坐标显示
            self.signals.status_changed.emit(f'坐标: ({lat:.6f}, {lon:.6f})')
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            # 完成绘制
            if len(self.temp_points) > 2:  # 至少需要3个点（包括临时点）
                # 移除最后的临时预览点
                self.temp_points.pop()
                if self.current_tool in ['restricted', 'traffic', 'weather', 'custom']:
                    self._create_dynamic_zone()
                elif self.current_tool in ['road', 'air', 'hybrid']:
                    self._create_path()
            
            self.is_drawing = False
            self.temp_points.clear()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            if self.current_tool in ['obstacle', 'building', 'landmark', 'station']:
                # 完成静态对象的绘制
                if len(self.temp_points) == 2:
                    start = self.temp_points[0]
                    end = self.temp_points[1]
                    radius = self._calculate_distance(start.lat, start.lon, end.lat, end.lon) * 10000
                    self._create_static_object(start.lat, start.lon, radius)
                self.is_drawing = False
                self.temp_points.clear()
                self.update()
        elif event.button() == Qt.MouseButton.RightButton and self.is_drawing:
            # 取消绘制
            self.is_drawing = False
            self.temp_points.clear()
            self.update()
    
    def _select_object_at(self, lat: float, lon: float):
        """选择指定位置的对象"""
        min_dist = float('inf')
        selected = None
        
        for obj in self.map_data.objects:
            if isinstance(obj, StaticObject):
                dist = self._calculate_distance(lat, lon, obj.position.lat, obj.position.lon)
                if dist < min_dist:
                    min_dist = dist
                    selected = obj
            elif isinstance(obj, (DynamicZone, Path)):
                for point in obj.points:
                    dist = self._calculate_distance(lat, lon, point.lat, point.lon)
                    if dist < min_dist:
                        min_dist = dist
                        selected = obj
        
        if min_dist < 0.001:  # 选择阈值
            self.selected_object = selected
            self.signals.object_selected.emit(selected.to_dict() if selected else None)
        else:
            self.selected_object = None
            self.signals.object_selected.emit(None)
    
    def _create_static_object(self, lat: float, lon: float, radius: float):
        """创建静态对象"""
        obj = StaticObject(
            id=str(uuid4()),
            type=ObjectType(self.current_tool),
            position=Position(lat=lat, lon=lon),
            radius=radius,  # 根据拖拽距离计算半径
            height=30.0   # 默认高度
        )
        self.map_data.objects.append(obj)
        self.signals.map_updated.emit()
    
    def _create_dynamic_zone(self):
        """创建动态区域"""
        zone = DynamicZone(
            id=str(uuid4()),
            type=ZoneType(self.current_tool),
            points=self.temp_points.copy()
        )
        self.map_data.objects.append(zone)
        self.signals.map_updated.emit()
    
    def _create_path(self):
        """创建路径"""
        path = Path(
            id=str(uuid4()),
            type=PathType(self.current_tool),
            points=self.temp_points.copy()
        )
        self.map_data.objects.append(path)
        self.signals.map_updated.emit()
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间距离（简化版，仅用于选择）"""
        return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5
    
    def set_tool(self, tool_name: str):
        """设置当前工具"""
        self.current_tool = tool_name
        self.signals.tool_changed.emit(tool_name)
        
        # 清除临时状态
        self.is_drawing = False
        self.temp_points.clear()
        self.update()
    
    def load_map_data(self, data: Union[Dict, str]):
        """加载地图数据"""
        try:
            if isinstance(data, str):
                self.map_data = MapData.from_json(data)
            else:
                self.map_data = MapData.from_dict(data)
            self.signals.load_completed.emit(True)
            self.signals.map_updated.emit()
            self.update()
        except Exception as e:
            self.signals.error_occurred.emit(f'加载地图数据失败：{str(e)}')
            self.signals.load_completed.emit(False)
    
    def save_map_data(self) -> Optional[str]:
        """保存地图数据"""
        try:
            data = self.map_data.to_json()
            self.signals.save_completed.emit(True)
            return data
        except Exception as e:
            self.signals.error_occurred.emit(f'保存地图数据失败：{str(e)}')
            self.signals.save_completed.emit(False)
            return None
    
    def set_view(self, center_lat: float, center_lon: float, zoom_level: float):
        """设置视图参数"""
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.zoom_level = zoom_level
        
        view_params = {
            'center_lat': center_lat,
            'center_lon': center_lon,
            'zoom_level': zoom_level
        }
        self.signals.view_changed.emit(view_params)
        self.update()
    
    def set_grid_size(self, size: float):
        """设置网格大小"""
        self.grid_size = size
        self.signals.grid_changed.emit({'size': size})
        self.update()