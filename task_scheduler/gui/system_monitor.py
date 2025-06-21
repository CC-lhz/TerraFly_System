from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QTextEdit, QTabWidget,
    QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
import pyqtgraph as pg
import numpy as np
from datetime import datetime, timedelta
import config

class MetricsWidget(QWidget):
    """性能指标显示组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.history_data = {
            'time': [],
            'cpu_usage': [],
            'memory_usage': [],
            'network_latency': []
        }
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # CPU使用率
        cpu_group = QGroupBox('CPU使用率')
        cpu_layout = QVBoxLayout(cpu_group)
        self.cpu_plot = pg.PlotWidget()
        self.cpu_plot.setBackground('w')
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.showGrid(x=True, y=True)
        cpu_layout.addWidget(self.cpu_plot)
        layout.addWidget(cpu_group)
        
        # 内存使用率
        memory_group = QGroupBox('内存使用率')
        memory_layout = QVBoxLayout(memory_group)
        self.memory_plot = pg.PlotWidget()
        self.memory_plot.setBackground('w')
        self.memory_plot.setYRange(0, 100)
        self.memory_plot.showGrid(x=True, y=True)
        memory_layout.addWidget(self.memory_plot)
        layout.addWidget(memory_group)
        
        # 网络延迟
        network_group = QGroupBox('网络延迟')
        network_layout = QVBoxLayout(network_group)
        self.network_plot = pg.PlotWidget()
        self.network_plot.setBackground('w')
        self.network_plot.setYRange(0, 1000)
        self.network_plot.showGrid(x=True, y=True)
        network_layout.addWidget(self.network_plot)
        layout.addWidget(network_group)
    
    def update_metrics(self, metrics):
        """更新性能指标显示"""
        current_time = datetime.now()
        
        # 更新历史数据
        self.history_data['time'].append(current_time)
        self.history_data['cpu_usage'].append(metrics['cpu_usage'])
        self.history_data['memory_usage'].append(metrics['memory_usage'])
        self.history_data['network_latency'].append(metrics['network_latency'])
        
        # 只保留最近30分钟的数据
        cutoff_time = current_time - timedelta(minutes=30)
        while self.history_data['time'] and self.history_data['time'][0] < cutoff_time:
            for key in self.history_data:
                self.history_data[key].pop(0)
        
        # 更新图表
        time_axis = [(t - self.history_data['time'][0]).total_seconds() / 60
                     for t in self.history_data['time']]
        
        self.cpu_plot.clear()
        self.cpu_plot.plot(time_axis, self.history_data['cpu_usage'],
                          pen=pg.mkPen('b', width=2))
        
        self.memory_plot.clear()
        self.memory_plot.plot(time_axis, self.history_data['memory_usage'],
                             pen=pg.mkPen('g', width=2))
        
        self.network_plot.clear()
        self.network_plot.plot(time_axis, self.history_data['network_latency'],
                              pen=pg.mkPen('r', width=2))

class LogViewer(QWidget):
    """日志查看器组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(['ALL', 'INFO', 'WARNING', 'ERROR'])
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        toolbar.addWidget(QLabel('日志级别:'))
        toolbar.addWidget(self.level_combo)
        
        clear_button = QPushButton('清除')
        clear_button.clicked.connect(self.clear_logs)
        toolbar.addWidget(clear_button)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
    
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
        
        # 如果当前筛选级别不匹配，则隐藏该条目
        if self.level_combo.currentText() != 'ALL' and level != self.level_combo.currentText():
            self.filter_logs()
    
    def filter_logs(self):
        """根据日志级别筛选显示"""
        selected_level = self.level_combo.currentText()
        if selected_level == 'ALL':
            return
        
        # 实现日志筛选逻辑
        pass
    
    def clear_logs(self):
        """清除所有日志"""
        self.log_text.clear()

class SystemMonitorWidget(QWidget):
    """系统监控界面"""
    refresh_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()
        self.refresh_signal.connect(self.refresh)
        
        # 创建更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh)
        self.update_timer.start(1000)  # 每秒更新一次
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 系统状态选项卡
        status_tab = QWidget()
        status_layout = QVBoxLayout(status_tab)
        
        # 状态概览
        overview_group = QGroupBox('系统概览')
        overview_layout = QHBoxLayout(overview_group)
        
        self.task_count_label = QLabel('活动任务: 0')
        self.vehicle_count_label = QLabel('活动车辆: 0')
        self.system_status_label = QLabel('系统状态: 正常')
        
        overview_layout.addWidget(self.task_count_label)
        overview_layout.addWidget(self.vehicle_count_label)
        overview_layout.addWidget(self.system_status_label)
        overview_layout.addStretch()
        
        status_layout.addWidget(overview_group)
        
        # 性能指标
        self.metrics_widget = MetricsWidget()
        status_layout.addWidget(self.metrics_widget)
        
        tab_widget.addTab(status_tab, '系统状态')
        
        # 日志选项卡
        self.log_viewer = LogViewer()
        tab_widget.addTab(self.log_viewer, '系统日志')
        
        layout.addWidget(tab_widget)
    
    def refresh(self):
        """刷新系统监控信息"""
        if not self.main_window.scheduler:
            return
        
        try:
            # 获取系统状态
            status = self.main_window.scheduler.get_system_status()
            
            # 更新状态概览
            active_tasks = sum(1 for task in status['tasks']
                              if task['status'] != 'completed')
            active_vehicles = sum(1 for vehicle in status['vehicles']
                                 if vehicle['status'] != 'idle')
            
            self.task_count_label.setText(f'活动任务: {active_tasks}')
            self.vehicle_count_label.setText(f'活动车辆: {active_vehicles}')
            self.system_status_label.setText(
                f'系统状态: {status.get("system_status", "正常")}'
            )
            
            # 更新性能指标
            metrics = status.get('metrics', {
                'cpu_usage': 0,
                'memory_usage': 0,
                'network_latency': 0
            })
            self.metrics_widget.update_metrics(metrics)
            
            # 更新日志
            for log in status.get('logs', []):
                self.log_viewer.add_log(log['level'], log['message'])
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, '错误', f'更新系统状态失败: {str(e)}')
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self.update_timer.stop()
        event.accept()