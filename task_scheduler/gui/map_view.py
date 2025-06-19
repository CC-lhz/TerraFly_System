from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
import math
from typing import List, Tuple, Dict

class MapView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        
        # 地图状态
        self.center_lat = 39.9  # 北京市中心纬度
        self.center_lon = 116.3  # 北京市中心经度
        self.zoom_level = 15.0  # 缩放级别
        self.dragging = False
        self.last_pos = None
        
        # 地图数据
        self.vehicles: Dict[str, Dict] = {}  # 存储所有车辆信息
        self.routes: Dict[str, List[Tuple[float, float, float]]] = {}  # 存储所有路线
        
        # 更新定时器
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_map)
        self.update_timer.start(1000)  # 每秒更新一次
        
        # 地图网格配置
        self.grid_size = 0.01  # 网格大小（度）
        self.grid_color = QColor(200, 200, 200, 100)  # 网格颜色
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(600, 400)
    
    def paintEvent(self, event):
        """绘制地图"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor('#f0f0f0'))
        
        # 绘制网格
        self.draw_grid(painter)
        
        # 绘制路线
        self.draw_routes(painter)
        
        # 绘制车辆
        self.draw_vehicles(painter)
    
    def draw_grid(self, painter):
        """绘制网格"""
        pen = QPen(QColor('#e0e0e0'))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 计算网格间距
        grid_size = self.width() / 20
        
        # 绘制垂直线
        for x in range(0, self.width(), int(grid_size)):
            painter.drawLine(x, 0, x, self.height())
        
        # 绘制水平线
        for y in range(0, self.height(), int(grid_size)):
            painter.drawLine(0, y, self.width(), y)
    
    def draw_routes(self, painter):
        """绘制路线"""
        for route in self.routes:
            # 设置路线样式
            pen = QPen(QColor(route.get('color', '#1869AD')))
            pen.setWidth(3)
            painter.setPen(pen)
            
            # 绘制路线段
            points = route['points']
            for i in range(len(points) - 1):
                start = self.geo_to_pixel(points[i][0], points[i][1])
                end = self.geo_to_pixel(points[i + 1][0], points[i + 1][1])
                painter.drawLine(start[0], start[1], end[0], end[1])
                
                # 如果是无人机，绘制高度指示线
                if len(points[i]) > 2:  # 检查是否包含高度信息
                    height_factor = points[i][2] / 120.0  # 假设最大飞行高度为120米
                    line_height = height_factor * 20  # 最大高度指示线为20像素
                    painter.drawLine(int(start[0]), int(start[1]), int(start[0]), int(start[1] - line_height))
    
    def draw_vehicles(self, painter):
        """绘制车辆"""
        for vehicle in self.vehicles:
            # 计算屏幕坐标
            x, y = self.geo_to_pixel(vehicle['location'][0], vehicle['location'][1])
            
            # 绘制车辆图标
            if vehicle['type'] == 'drone':
                self.draw_drone(painter, x, y, vehicle)
            else:
                self.draw_car(painter, x, y, vehicle)
    
    def draw_drone(self, painter, x, y, vehicle):
        """绘制无人机图标"""
        size = 20
        color = QColor('#FF4081') if vehicle['status'] == 'busy' else QColor('#2196F3')
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        
        # 绘制无人机形状
        points = [
            (x, y - size/2),  # 顶部
            (x - size/2, y + size/2),  # 左下
            (x + size/2, y + size/2)   # 右下
        ]
        painter.drawPolygon(*[Qt.QPoint(px, py) for px, py in points])
        
        # 绘制标签
        self.draw_vehicle_label(painter, x, y + size, vehicle)
    
    def draw_car(self, painter, x, y, vehicle):
        """绘制车辆图标"""
        size = 16
        color = QColor('#FF4081') if vehicle['status'] == 'busy' else QColor('#2196F3')
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        
        # 绘制车辆形状（矩形）
        painter.drawRect(x - size/2, y - size/2, size, size)
        
        # 绘制标签
        self.draw_vehicle_label(painter, x, y + size, vehicle)
    
    def draw_vehicle_label(self, painter, x, y, vehicle):
        """绘制车辆标签"""
        painter.setPen(QPen(QColor('#333333')))
        painter.setFont(QFont('Arial', 8))
        
        # 绘制ID
        text = f"{vehicle['id']} ({vehicle['battery_level']}%)"
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        painter.drawText(x - text_width/2, y + 15, text)
    
    def geo_to_pixel(self, lat: float, lon: float) -> Tuple[float, float]:
        """将地理坐标转换为屏幕坐标"""
        # 计算缩放因子
        zoom_factor = math.pow(2, self.zoom_level - 15)
        
        # 计算相对于中心点的偏移（度）
        dlat = lat - self.center_lat
        dlon = lon - self.center_lon
        
        # 转换为屏幕坐标
        x = self.width() / 2 + dlon * zoom_factor * self.width()
        y = self.height() / 2 - dlat * zoom_factor * self.height()
        
        return x, y
    
    def pixel_to_geo(self, x: float, y: float) -> Tuple[float, float]:
        """将屏幕坐标转换为地理坐标"""
        # 计算缩放因子
        zoom_factor = math.pow(2, self.zoom_level - 15)
        
        # 计算相对于中心的偏移（像素）
        dx = x - self.width() / 2
        dy = self.height() / 2 - y
        
        # 转换为地理坐标
        lon = self.center_lon + dx / (zoom_factor * self.width())
        lat = self.center_lat + dy / (zoom_factor * self.height())
        
        return lat, lon
    
    def wheelEvent(self, event):
        """鼠标滚轮事件处理（缩放）"""
        if event.angleDelta().y() > 0:
            self.zoom_level *= 1.2
        else:
            self.zoom_level /= 1.2
        self.update()
    
    def mousePressEvent(self, event):
        """鼠标按下事件处理（拖动开始）"""
        self.last_pos = event.pos()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件处理（拖动地图）"""
        if hasattr(self, 'last_pos'):
            delta = event.pos() - self.last_pos
            self.center_lon -= delta.x() / (self.zoom_level * 10000)
            self.center_lat += delta.y() / (self.zoom_level * 10000)
            self.last_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件处理（拖动结束）"""
        if hasattr(self, 'last_pos'):
            del self.last_pos
    
    def update_map(self):
        """更新地图显示"""
        if not self.main_window.scheduler:
            return
        
        status = self.main_window.scheduler.get_system_status()
        self.vehicles = status['vehicles']
        self.routes = status['routes']
        self.update()
    
    def refresh(self):
        """刷新地图"""
        self.update_map()