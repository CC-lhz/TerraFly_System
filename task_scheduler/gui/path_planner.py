from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QFormLayout, QCheckBox, QSplitter
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTimer
import folium
from folium import plugins
import tempfile
import os
import json
from ..config import config

class PathPlannerWidget(QWidget):
    """路径规划界面"""
    refresh_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()
        self.refresh_signal.connect(self.refresh)
        self.temp_html = None
        
        # 创建自动刷新定时器
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(2000)  # 每2秒刷新一次
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # 创建左侧控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # 规划参数设置
        params_group = QGroupBox('规划参数')
        params_layout = QFormLayout(params_group)
        
        # 规划模式选择
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['全局规划', '局部规划'])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        params_layout.addRow('规划模式:', self.mode_combo)
        
        # 车辆类型选择
        self.vehicle_type_combo = QComboBox()
        self.vehicle_type_combo.addItems(['car', 'drone'])
        params_layout.addRow('车辆类型:', self.vehicle_type_combo)
        
        # 全局规划参数
        self.global_params_group = QGroupBox('全局规划参数')
        global_params_layout = QFormLayout(self.global_params_group)
        
        self.route_type_combo = QComboBox()
        self.route_type_combo.addItems(['driving', 'walking', 'riding'])
        global_params_layout.addRow('路线类型:', self.route_type_combo)
        
        self.avoid_traffic = QCheckBox('避开拥堵')
        global_params_layout.addRow(self.avoid_traffic)
        
        # 局部规划参数
        self.local_params_group = QGroupBox('局部规划参数')
        local_params_layout = QFormLayout(self.local_params_group)
        
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(['A*', 'RRT'])
        local_params_layout.addRow('算法:', self.algorithm_combo)
        
        self.step_size = QDoubleSpinBox()
        self.step_size.setRange(0.1, 10.0)
        self.step_size.setValue(1.0)
        local_params_layout.addRow('步长:', self.step_size)
        
        self.max_iterations = QSpinBox()
        self.max_iterations.setRange(100, 10000)
        self.max_iterations.setValue(1000)
        local_params_layout.addRow('最大迭代:', self.max_iterations)
        
        # 添加参数组到控制面板
        control_layout.addWidget(params_group)
        control_layout.addWidget(self.global_params_group)
        control_layout.addWidget(self.local_params_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        plan_button = QPushButton('规划路径')
        plan_button.clicked.connect(self.plan_path)
        button_layout.addWidget(plan_button)
        
        clear_button = QPushButton('清除路径')
        clear_button.clicked.connect(self.clear_path)
        button_layout.addWidget(clear_button)
        
        control_layout.addLayout(button_layout)
        control_layout.addStretch()
        
        # 创建地图视图
        self.map_view = QWebEngineView()
        self.map_view.page().settings().setAttribute(
            self.map_view.page().settings().WebAttribute.JavascriptEnabled, True
        )
        self.map_view.loadFinished.connect(self.on_map_loaded)
        
        # 使用分割器组织布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(control_panel)
        splitter.addWidget(self.map_view)
        splitter.setStretchFactor(0, 1)  # 控制面板占1份
        splitter.setStretchFactor(1, 4)  # 地图视图占4份
        
        layout.addWidget(splitter)
        
        # 初始化地图
        self.init_map()
        
    def init_map(self):
        """初始化地图"""
        # 创建包含地图的HTML文件
        self.temp_html = tempfile.NamedTemporaryFile(suffix='.html', delete=False).name
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>TerraFly Map</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css" />
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
            <script defer src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js" onload="initMap()"></script>
            <script defer src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
            <style>
                #map {{ height: 100vh; width: 100%; margin: 0; padding: 0; }}
                body {{ margin: 0; padding: 0; }}
                .custom-div-icon {{ background: none; border: none; }}
                .custom-div-icon i {{ display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map;
                function initMap() {{
                    map = L.map('map').setView([{config['map_center'][0]}, {config['map_center'][1]}], {config['zoom_start']});
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        attribution: '© OpenStreetMap contributors'
                    }}).addTo(map);
                    
                    // 添加控件
                    L.control.scale().addTo(map);
                    
                    // 添加绘图控件
                    var drawControl = new L.Control.Draw({{
                        draw: {{
                            polyline: true,
                            rectangle: true,
                            circle: true,
                            marker: true,
                            polygon: true
                        }}
                    }});
                    map.addControl(drawControl);
                }});
            </script>
        </body>
        </html>
        """
        
        with open(self.temp_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.map_view.setUrl(QUrl.fromLocalFile(self.temp_html))
    
    def on_mode_changed(self, mode):
        """规划模式改变时更新界面"""
        if mode == '全局规划':
            self.global_params_group.setVisible(True)
            self.local_params_group.setVisible(False)
        else:
            self.global_params_group.setVisible(False)
            self.local_params_group.setVisible(True)
    
    def refresh(self):
        """刷新地图显示"""
        if not self.main_window.scheduler:
            return
        
        # 获取当前系统状态
        status = self.main_window.scheduler.get_system_status()
        
        # 使用JavaScript更新地图
        update_script = f"""
        (function() {{
            if (typeof L === 'undefined' || !map) {{
                console.log('Map not initialized yet...');
                return;
            }}
            
            // 清除现有标记和轨迹
            map.eachLayer(function(layer) {{
                if (!(layer instanceof L.TileLayer)) {{
                    map.removeLayer(layer);
                }}
            }});
            
            // 添加车辆标记和轨迹
            const vehicles = {json.dumps(status['vehicles'])};
            vehicles.forEach(function(vehicle) {{
                const color = vehicle.type === 'drone' ? 'red' : 'blue';
                
                // 创建自定义图标
                const icon = L.divIcon({{
                    html: `
                        <div style="
                            width: 20px;
                            height: 20px;
                            border-radius: 50%;
                            background-color: ${{color}};
                            border: 2px solid white;
                            box-shadow: 0 0 10px rgba(0,0,0,0.5);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-weight: bold;
                            font-size: 12px;
                        ">${{vehicle.id[0].toUpperCase()}}</div>
                    `,
                    className: ''
                }});
                
                // 添加标记
                const marker = L.marker(vehicle.location, {{icon: icon}});
                const popupContent = `
                    <div style='min-width: 180px'>
                        <b>${{vehicle.type.toUpperCase()}} ${{vehicle.id}}</b><br>
                        状态: ${{vehicle.status}}<br>
                        电量: ${{vehicle.battery_level}}%<br>
                        位置: ${{vehicle.location}}<br>
                        ${{vehicle.type === 'drone' ? `高度: ${{vehicle.altitude || 'N/A'}}m<br>` : ''}}
                        ${{vehicle.speed ? `速度: ${{vehicle.speed}}km/h` : ''}}
                    </div>
                `;
                marker.bindPopup(popupContent, {{maxWidth: 300}});
                marker.addTo(map);
                
                // 添加轨迹
                if (vehicle.trajectory) {{
                    const polyline = L.polyline(vehicle.trajectory, {{
                        color: color,
                        weight: 2,
                        opacity: 0.5,
                        dashArray: '5,10'
                    }}).addTo(map);
                }}
            }});
            
            // 添加起降点和充电站标记
            const points = {json.dumps(status['delivery_points'])};
            points.forEach(function(point) {{
                let iconColor = 'green';
                let iconType = 'info';
                
                if (point.type === 'pickup') {{
                    iconColor = 'orange';
                    iconType = 'upload';
                }} else if (point.type === 'drone_station') {{
                    iconColor = 'purple';
                    iconType = 'plane';
                }} else if (point.type === 'charging_station') {{
                    iconColor = 'red';
                    iconType = 'bolt';
                }}
                
                const marker = L.marker(point.location, {{
                    icon: L.divIcon({{
                        html: `<i class="fa fa-${{iconType}}" style="color: ${{iconColor}}; font-size: 24px;"></i>`,
                        className: 'custom-div-icon',
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    }})
                }});
                
                const popupContent = `
                    <div style='min-width: 150px'>
                        <b>${{point.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}}</b><br>
                        ID: ${{point.id}}<br>
                        位置: ${{point.location}}
                    </div>
                `;
                marker.bindPopup(popupContent, {{maxWidth: 250}});
                marker.addTo(map);
            }});
            
            // 添加任务路径和航路点
            const tasks = {json.dumps(status['tasks'])};
            tasks.forEach(function(task) {{
                if (task.planned_path) {{
                    const color = task.vehicle_type === 'drone' ? 'red' : 'blue';
                    
                    // 绘制路径线
                    const path = L.polyline(task.planned_path, {{
                        color: color,
                        weight: 3,
                        opacity: 0.8
                    }}).bindPopup(`任务 ${{task.id}}`).addTo(map);
                    
                    // 添加航路点标记
                    task.planned_path.forEach((point, index) => {{
                        L.circleMarker(point, {{
                            radius: 5,
                            color: color,
                            fillColor: color,
                            fillOpacity: 0.7,
                            weight: 1
                        }}).bindPopup(`航路点 ${{index + 1}}`).addTo(map);
                    }});
                }}
            }});
        }})();
        """
        
        self.map_view.page().runJavaScript(update_script)
    
    def plan_path(self):
        """规划路径"""
        if not self.main_window.scheduler:
            return
        
        try:
            # 获取规划参数
            params = {
                'mode': self.mode_combo.currentText(),
                'vehicle_type': self.vehicle_type_combo.currentText()
            }
            
            if params['mode'] == '全局规划':
                params.update({
                    'route_type': self.route_type_combo.currentText(),
                    'avoid_traffic': self.avoid_traffic.isChecked()
                })
            else:
                params.update({
                    'algorithm': self.algorithm_combo.currentText(),
                    'step_size': self.step_size.value(),
                    'max_iterations': self.max_iterations.value()
                })
            
            # 调用路径规划
            self.main_window.scheduler.plan_path(params)
            self.refresh()
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, '错误', f'路径规划失败: {str(e)}')
    
    def clear_path(self):
        """清除规划的路径"""
        if not self.main_window.scheduler:
            return
        
        try:
            self.main_window.scheduler.clear_planned_paths()
            self.refresh()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, '错误', f'清除路径失败: {str(e)}')
    
    def on_map_loaded(self, ok):
        """地图加载完成事件处理"""
        if ok:
            # 等待一段时间确保 Leaflet.js 加载完成
            QTimer.singleShot(1000, self.refresh)
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.temp_html and os.path.exists(self.temp_html):
            try:
                os.unlink(self.temp_html)
            except:
                pass
        event.accept()