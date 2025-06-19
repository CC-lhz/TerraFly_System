from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QFormLayout, QCheckBox, QWebEngineView, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
import folium
from folium import plugins
import tempfile
import os
import json
import config

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
        # 创建Folium地图
        m = folium.Map(
            location=[config.config['map']['center_lat'],
                     config.config['map']['center_lon']],
            zoom_start=config.config['map']['zoom_level'],
            control_scale=True
        )
        
        # 添加图层控制
        folium.LayerControl().add_to(m)
        
        # 添加全屏控件
        folium.plugins.Fullscreen().add_to(m)
        
        # 添加绘图控件
        folium.plugins.Draw(
            export=True,
            position='topleft',
            draw_options={
                'polyline': True,
                'rectangle': True,
                'circle': True,
                'marker': True,
                'circlemarker': False,
                'polygon': True
            }
        ).add_to(m)
        
        # 添加鼠标位置显示
        folium.plugins.MousePosition(
            position='bottomleft',
            separator=' | ',
            prefix='坐标: '
        ).add_to(m)
        
        # 添加小地图
        folium.plugins.MiniMap().add_to(m)
        
        # 保存到临时文件并显示
        self.temp_html = tempfile.NamedTemporaryFile(suffix='.html', delete=False).name
        m.save(self.temp_html)
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
        
        # 获取当前地图的视角和缩放级别
        current_view = None
        if self.map_view.page():
            self.map_view.page().runJavaScript(
                """(function() {
                    var map = document.querySelector('#map')._leaflet_map;
                    return JSON.stringify({
                        center: map.getCenter(),
                        zoom: map.getZoom()
                    });
                })();""",
                lambda result: setattr(self, '_map_state', json.loads(result) if result else None)
            )
        
        # 创建新地图，使用保存的视角
        if hasattr(self, '_map_state') and self._map_state:
            m = folium.Map(
                location=[self._map_state['center']['lat'],
                         self._map_state['center']['lng']],
                zoom_start=self._map_state['zoom'],
                control_scale=True
            )
        else:
            m = folium.Map(
                location=[config.config['map']['center_lat'],
                         config.config['map']['center_lon']],
                zoom_start=config.config['map']['zoom_level'],
                control_scale=True
            )
        
        # 添加车辆标记和轨迹
        for vehicle in status['vehicles']:
            # 添加车辆实时位置标记
            color = 'red' if vehicle['type'] == 'drone' else 'blue'
            icon = folium.DivIcon(html=f"""
                <div style="
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background-color: {color};
                    border: 2px solid white;
                    box-shadow: 0 0 10px rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 12px;
                ">{vehicle['id'][0].upper()}</div>
            """)
            
            folium.Marker(
                location=vehicle['location'],
                icon=icon,
                popup=folium.Popup(f"""
                    <div style='min-width: 180px'>
                        <b>{vehicle['type'].upper()} {vehicle['id']}</b><br>
                        状态: {vehicle['status']}<br>
                        电量: {vehicle['battery_level']}%<br>
                        位置: {vehicle['location']}<br>
                        {'高度: ' + str(vehicle.get('altitude', 'N/A')) + 'm<br>' if vehicle['type'] == 'drone' else ''}
                        {'速度: ' + str(vehicle.get('speed', 'N/A')) + 'km/h' if 'speed' in vehicle else ''}
                    </div>
                """, max_width=300)
            ).add_to(m)
            
            # 添加历史轨迹
            if 'trajectory' in vehicle:
                folium.PolyLine(
                    locations=vehicle['trajectory'],
                    color=color,
                    weight=2,
                    opacity=0.5,
                    dash_array='5,10'
                ).add_to(m)
        
        # 添加起降点和充电站标记
        for point in status['delivery_points']:
            icon_color = 'green'
            icon_type = 'info-sign'
            if point['type'] == 'pickup':
                icon_color = 'orange'
                icon_type = 'upload'
            elif point['type'] == 'drone_station':
                icon_color = 'purple'
                icon_type = 'plane'
            elif point['type'] == 'charging_station':
                icon_color = 'lightred'
                icon_type = 'flash'
            
            folium.Marker(
                location=point['location'],
                popup=folium.Popup(f"""
                    <div style='min-width: 150px'>
                        <b>{point['type'].replace('_', ' ').title()}</b><br>
                        ID: {point['id']}<br>
                        位置: {point['location']}
                    </div>
                """, max_width=250),
                icon=folium.Icon(color=icon_color, icon=icon_type)
            ).add_to(m)
        
        # 添加任务路径和航路点
        for task in status['tasks']:
            if task.get('planned_path'):
                # 绘制路径线
                color = 'red' if task.get('vehicle_type') == 'drone' else 'blue'
                path = folium.PolyLine(
                    locations=task['planned_path'],
                    color=color,
                    weight=3,
                    opacity=0.8,
                    popup=f"任务 {task['id']}"
                ).add_to(m)
                
                # 添加航路点标记
                for i, point in enumerate(task['planned_path']):
                    folium.CircleMarker(
                        location=point,
                        radius=5,
                        color=color,
                        fill=True,
                        popup=f"航路点 {i+1}",
                        opacity=0.7
                    ).add_to(m)
        
        # 保存并显示地图
        if self.temp_html:
            os.unlink(self.temp_html)
        self.temp_html = tempfile.NamedTemporaryFile(suffix='.html', delete=False).name
        m.save(self.temp_html)
        self.map_view.setUrl(QUrl.fromLocalFile(self.temp_html))
    
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
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.temp_html and os.path.exists(self.temp_html):
            try:
                os.unlink(self.temp_html)
            except:
                pass
        event.accept()