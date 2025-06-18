from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QTextEdit, QTabWidget,
    QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
import pyqtgraph as pg
import numpy as np
from datetime import datetime
from utils import (
    format_datetime, format_percentage, format_speed,
    format_distance, get_status_color, show_error_dialog
)

class VehicleComputerWidget(QWidget):
    """车载/机载电脑界面"""
    refresh_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()
        
        # 创建更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh)
        self.update_timer.start(1000)  # 每秒更新一次
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 状态监控选项卡
        status_tab = QWidget()
        status_layout = QVBoxLayout(status_tab)
        
        # 基本信息
        info_group = QGroupBox('基本信息')
        info_layout = QGridLayout(info_group)
        
        self.vehicle_id_label = QLabel('车辆ID: -')
        self.vehicle_type_label = QLabel('类型: -')
        self.status_label = QLabel('状态: -')
        self.battery_label = QLabel('电量: -')
        self.location_label = QLabel('位置: -')
        self.speed_label = QLabel('速度: -')
        self.altitude_label = QLabel('高度: -')
        self.heading_label = QLabel('航向: -')
        
        info_layout.addWidget(self.vehicle_id_label, 0, 0)
        info_layout.addWidget(self.vehicle_type_label, 0, 1)
        info_layout.addWidget(self.status_label, 1, 0)
        info_layout.addWidget(self.battery_label, 1, 1)
        info_layout.addWidget(self.location_label, 2, 0)
        info_layout.addWidget(self.speed_label, 2, 1)
        info_layout.addWidget(self.altitude_label, 3, 0)
        info_layout.addWidget(self.heading_label, 3, 1)
        
        status_layout.addWidget(info_group)
        
        # 传感器数据
        sensor_group = QGroupBox('传感器数据')
        sensor_layout = QVBoxLayout(sensor_group)
        
        self.sensor_plot = pg.PlotWidget()
        self.sensor_plot.setBackground('w')
        self.sensor_plot.showGrid(x=True, y=True)
        sensor_layout.addWidget(self.sensor_plot)
        
        status_layout.addWidget(sensor_group)
        
        # 系统日志
        log_group = QGroupBox('系统日志')
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        status_layout.addWidget(log_group)
        
        tab_widget.addTab(status_tab, '状态监控')
        
        # 参数配置选项卡
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)
        
        # 飞行参数
        flight_group = QGroupBox('飞行参数')
        flight_layout = QGridLayout(flight_group)
        
        self.max_speed_spin = QDoubleSpinBox()
        self.max_speed_spin.setRange(0, 100)
        self.max_speed_spin.setSuffix(' m/s')
        
        self.max_altitude_spin = QDoubleSpinBox()
        self.max_altitude_spin.setRange(0, 1000)
        self.max_altitude_spin.setSuffix(' m')
        
        self.return_altitude_spin = QDoubleSpinBox()
        self.return_altitude_spin.setRange(0, 1000)
        self.return_altitude_spin.setSuffix(' m')
        
        flight_layout.addWidget(QLabel('最大速度:'), 0, 0)
        flight_layout.addWidget(self.max_speed_spin, 0, 1)
        flight_layout.addWidget(QLabel('最大高度:'), 1, 0)
        flight_layout.addWidget(self.max_altitude_spin, 1, 1)
        flight_layout.addWidget(QLabel('返航高度:'), 2, 0)
        flight_layout.addWidget(self.return_altitude_spin, 2, 1)
        
        config_layout.addWidget(flight_group)
        
        # 安全参数
        safety_group = QGroupBox('安全参数')
        safety_layout = QGridLayout(safety_group)
        
        self.low_battery_spin = QSpinBox()
        self.low_battery_spin.setRange(0, 100)
        self.low_battery_spin.setSuffix('%')
        
        self.critical_battery_spin = QSpinBox()
        self.critical_battery_spin.setRange(0, 100)
        self.critical_battery_spin.setSuffix('%')
        
        self.return_distance_spin = QDoubleSpinBox()
        self.return_distance_spin.setRange(0, 10000)
        self.return_distance_spin.setSuffix(' m')
        
        safety_layout.addWidget(QLabel('低电量警告:'), 0, 0)
        safety_layout.addWidget(self.low_battery_spin, 0, 1)
        safety_layout.addWidget(QLabel('紧急返航电量:'), 1, 0)
        safety_layout.addWidget(self.critical_battery_spin, 1, 1)
        safety_layout.addWidget(QLabel('最大返航距离:'), 2, 0)
        safety_layout.addWidget(self.return_distance_spin, 2, 1)
        
        config_layout.addWidget(safety_group)
        
        # 通信参数
        comm_group = QGroupBox('通信参数')
        comm_layout = QGridLayout(comm_group)
        
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(['自动', '2.4GHz', '5.8GHz'])
        
        self.power_combo = QComboBox()
        self.power_combo.addItems(['自动', '低功率', '中功率', '高功率'])
        
        self.encryption_check = QCheckBox('启用加密')
        
        comm_layout.addWidget(QLabel('通信频道:'), 0, 0)
        comm_layout.addWidget(self.channel_combo, 0, 1)
        comm_layout.addWidget(QLabel('发射功率:'), 1, 0)
        comm_layout.addWidget(self.power_combo, 1, 1)
        comm_layout.addWidget(self.encryption_check, 2, 0, 1, 2)
        
        config_layout.addWidget(comm_group)
        
        # 保存按钮
        save_button = QPushButton('保存配置')
        save_button.clicked.connect(self.save_config)
        config_layout.addWidget(save_button)
        
        tab_widget.addTab(config_tab, '参数配置')
        
        # 控制选项卡
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)
        
        # 飞行控制
        control_group = QGroupBox('飞行控制')
        control_grid = QGridLayout(control_group)
        
        takeoff_button = QPushButton('起飞')
        land_button = QPushButton('降落')
        return_button = QPushButton('返航')
        hover_button = QPushButton('悬停')
        
        control_grid.addWidget(takeoff_button, 0, 0)
        control_grid.addWidget(land_button, 0, 1)
        control_grid.addWidget(return_button, 1, 0)
        control_grid.addWidget(hover_button, 1, 1)
        
        control_layout.addWidget(control_group)
        
        # 任务控制
        task_group = QGroupBox('任务控制')
        task_grid = QGridLayout(task_group)
        
        start_button = QPushButton('开始任务')
        pause_button = QPushButton('暂停任务')
        resume_button = QPushButton('继续任务')
        abort_button = QPushButton('终止任务')
        
        task_grid.addWidget(start_button, 0, 0)
        task_grid.addWidget(pause_button, 0, 1)
        task_grid.addWidget(resume_button, 1, 0)
        task_grid.addWidget(abort_button, 1, 1)
        
        control_layout.addWidget(task_group)
        
        # 紧急控制
        emergency_group = QGroupBox('紧急控制')
        emergency_layout = QVBoxLayout(emergency_group)
        
        emergency_button = QPushButton('紧急停止')
        emergency_button.setStyleSheet('background-color: red; color: white;')
        emergency_layout.addWidget(emergency_button)
        
        control_layout.addWidget(emergency_group)
        
        tab_widget.addTab(control_tab, '控制面板')
        
        layout.addWidget(tab_widget)
    
    def refresh(self):
        """刷新界面数据"""
        if not self.main_window.scheduler:
            return
        
        try:
            # 获取车辆状态
            vehicle = self.main_window.scheduler.get_vehicle_status()
            if not vehicle:
                return
            
            # 更新基本信息
            self.vehicle_id_label.setText(f'车辆ID: {vehicle["id"]}')
            self.vehicle_type_label.setText(f'类型: {vehicle["type"]}')
            self.status_label.setText(f'状态: {vehicle["status"]}')
            self.battery_label.setText(f'电量: {format_percentage(vehicle["battery"])}')
            self.location_label.setText(
                f'位置: ({vehicle["location"]["lat"]:.6f}, '
                f'{vehicle["location"]["lon"]:.6f})'
            )
            self.speed_label.setText(f'速度: {format_speed(vehicle["speed"])}')
            self.altitude_label.setText(f'高度: {format_distance(vehicle["altitude"])}')
            self.heading_label.setText(f'航向: {vehicle["heading"]}°')
            
            # 更新传感器数据
            self.update_sensor_plot(vehicle.get('sensor_data', {}))
            
            # 更新系统日志
            for log in vehicle.get('logs', []):
                self.add_log(log['level'], log['message'])
            
        except Exception as e:
            show_error_dialog(self, '错误', f'更新车辆状态失败: {str(e)}')
    
    def update_sensor_plot(self, sensor_data):
        """更新传感器数据图表"""
        self.sensor_plot.clear()
        
        # 添加传感器数据曲线
        for name, data in sensor_data.items():
            self.sensor_plot.plot(
                data['time'],
                data['values'],
                name=name,
                pen=pg.mkPen(data.get('color', 'b'), width=2)
            )
    
    def add_log(self, level, message):
        """添加日志条目"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        color = {
            'INFO': 'black',
            'WARNING': 'orange',
            'ERROR': 'red'
        }.get(level, 'black')
        
        self.log_text.append(
            f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span>'
        )
    
    def save_config(self):
        """保存参数配置"""
        try:
            config = {
                'flight': {
                    'max_speed': self.max_speed_spin.value(),
                    'max_altitude': self.max_altitude_spin.value(),
                    'return_altitude': self.return_altitude_spin.value()
                },
                'safety': {
                    'low_battery': self.low_battery_spin.value(),
                    'critical_battery': self.critical_battery_spin.value(),
                    'return_distance': self.return_distance_spin.value()
                },
                'communication': {
                    'channel': self.channel_combo.currentText(),
                    'power': self.power_combo.currentText(),
                    'encryption': self.encryption_check.isChecked()
                }
            }
            
            # 调用调度器保存配置
            self.main_window.scheduler.update_vehicle_config(config)
            
            show_info_dialog(self, '成功', '配置已保存')
            
        except Exception as e:
            show_error_dialog(self, '错误', f'保存配置失败: {str(e)}')
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self.update_timer.stop()
        event.accept()