from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl
import json
from typing import List, Dict
import logging
import os

class MapView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setMinimumSize(800, 600)
        self.logger = logging.getLogger('MapView')
        
        # 初始化Web视图
        self.web_view = QWebEngineView(self)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        
        # 地图数据
        self.static_objects = []  # 静态对象（建筑、充电站等）
        self.zones = []  # 区域（禁飞区、交通管制区等）
        self.paths = []  # 路径（地面配送路线、无人机航线等）
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)
        self.setLayout(layout)
        
        # 初始化地图HTML
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>TerraFly Map</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" />
            <style>
                #map { height: 100vh; width: 100%; }
                body { margin: 0; }
                .custom-icon {
                    background: none;
                    border: none;
                }
                .custom-icon i {
                    font-size: 24px;
                }
                .building-icon i { color: #1976D2; }
                .station-icon i { color: #FF4081; }
                .obstacle-icon i { color: #FFA000; }
                .landmark-icon i { color: #7B1FA2; }
                .restricted-icon i { color: #D32F2F; }
                .traffic-icon i { color: #388E3C; }
                .weather-icon i { color: #0288D1; }
                .custom-icon i { color: #5D4037; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map', {
                    center: [31.2287, 121.4726],
                    zoom: 15,
                    zoomControl: true,
                    attributionControl: false
                });
                
                // 自定义图标类
                function CustomIcon(options) {
                    var opts = {
                        className: options.className || 'custom-icon',
                        html: options.html || '<i class="fas fa-building"></i>',
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    };
                    return L.divIcon(opts);
                }
                
                var buildingIcon = CustomIcon({
                    className: 'custom-icon building-icon',
                    html: '<i class="fas fa-building"></i>'
                });
                var stationIcon = CustomIcon({
                    className: 'custom-icon station-icon',
                    html: '<i class="fas fa-charging-station"></i>'
                });
                
                // 定义路径样式
                var pathStyles = {
                    'road': { color: '#1976D2', weight: 3, opacity: 0.8 },
                    'air': { color: '#FF4081', weight: 3, opacity: 0.8, dashArray: '5, 10' },
                    'hybrid': { color: '#7B1FA2', weight: 3, opacity: 0.8, dashArray: '15, 10, 5, 10' }
                };
                
                // 全局变量存储marker和path
                var markers = {};
                var paths = {};
            </script>
        </body>
        </html>
        '''
        self.web_view.setHtml(html)
    
    def refresh(self):
        """刷新地图显示"""
        try:
            # 读取example_map.tfmap文件
            map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'example_map.tfmap')
            with open(map_path, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
                
            # 加载地图数据
            self.load_map_data(json.dumps(map_data))            
        except Exception as e:
            self.logger.error(f'加载地图数据失败：{str(e)}')
    
    def load_map_data(self, map_data):
        """加载地图数据"""
        try:
            data = json.loads(map_data)  # 解析地图数据
            
            # 准备JavaScript代码
            js_code = 'Object.values(markers).forEach(marker => marker.remove()); Object.values(paths).forEach(path => path.remove()); markers = {}; paths = {};'
            
            # 添加对象（建筑物、充电站等）
            for obj in data.get('objects', []):
                # 处理标记点
                if 'position' in obj:
                    pos = obj.get('position', [])
                    if not isinstance(pos, list) or len(pos) < 2:
                        continue
                        
                    lat, lon = pos[0], pos[1]
                    
                    # 根据对象类型设置图标类和图标
                    icon_class = None
                    icon_name = None
                    if obj['type'] == 'building':
                        icon_class = 'building-icon'
                        icon_name = 'building'
                    elif obj['type'] == 'station':
                        icon_class = 'station-icon'
                        icon_name = 'charging-station'
                    elif obj['type'] == 'obstacle':
                        icon_class = 'obstacle-icon'
                        icon_name = 'exclamation-triangle'
                    elif obj['type'] == 'landmark':
                        icon_class = 'landmark-icon'
                        icon_name = 'map-marker-alt'
                    elif obj['type'] == 'restricted':
                        icon_class = 'restricted-icon'
                        icon_name = 'ban'
                    elif obj['type'] == 'traffic':
                        icon_class = 'traffic-icon'
                        icon_name = 'traffic-light'
                    elif obj['type'] == 'weather':
                        icon_class = 'weather-icon'
                        icon_name = 'cloud'
                    elif obj['type'] == 'custom':
                        icon_class = 'custom-icon'
                        icon_name = 'map'
                        
                    if not icon_class or not icon_name:
                        continue
                    
                    name = obj.get('name', '').replace('"', '\\"')
                    description = obj.get('description', '').replace('"', '\\"')
                    
                    # 构造图标选项
                    icon_div = f'L.divIcon({{className:"custom-icon {icon_class}",html:"<i class=\\"fas fa-{icon_name}\\"></i>",iconSize:[30,30],iconAnchor:[15,15]}})'
                    js_code += f'markers["{obj["id"]}"] = L.marker([{lat}, {lon}], {{icon:{icon_div},title:"{name}"}}).addTo(map).bindPopup("<b>{name}</b><br>{description}");'
                
                # 处理路径
                elif obj['type'] in ['road', 'air', 'hybrid'] and 'points' in obj:
                    points = obj.get('points', [])
                    if not points:
                        continue
                    
                    name = obj.get('name', '').replace('"', '\\"')
                    description = obj.get('description', '').replace('"', '\\"')
                    
                    # 转换点坐标为JavaScript数组
                    coords_str = json.dumps(points)
                    style = f"pathStyles['{obj['type']}']"
                    js_code += f'paths["{obj["id"]}"] = L.polyline({coords_str}, {style}).addTo(map).bindPopup("<b>{name}</b><br>{description}");'
            
            # 执行JavaScript代码
            self.web_view.page().runJavaScript(js_code)
            
        except Exception as e:
            raise Exception(f'解析地图数据失败：{str(e)}')
        
        
        
        
    def on_map_loaded(self, ok):
        """地图加载完成事件处理"""
        if ok:
            self.web_view.page().loadFinished.connect(lambda ok: print('地图加载完成' if ok else '地图加载失败'))