import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QTabWidget, QMenuBar, QStatusBar,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon

from task_scheduler.gui.device_manager import DeviceManagerWidget
from task_scheduler.gui.task_manager import TaskManagerWidget
from task_scheduler.gui.path_planner import PathPlannerWidget
from task_scheduler.gui.system_monitor import SystemMonitorWidget
from task_scheduler.gui.map_view import MapView
from task_scheduler.unified_scheduler import UnifiedScheduler
from task_scheduler.system_map_planner import SystemMapPlanner
from task_scheduler.flight_scheduler import FlightScheduler
from task_scheduler import config
from car.ground_control.environment_init import EnvironmentManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scheduler = None
        self.init_ui()
        self.init_scheduler()
        # 加载示例地图并刷新视图
        self.load_map('d:\\毕业设计\\TerraFly_System\\example_map.tfmap')
        self.refresh_all()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('TerraFly调度管理系统')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建选项卡部件
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 添加各功能模块的选项卡
        self.vehicle_manager = DeviceManagerWidget(self)
        self.task_manager = TaskManagerWidget(self)
        self.path_planner = PathPlannerWidget(self)
        self.system_monitor = SystemMonitorWidget(self)
        self.map_view = MapView(self)
        
        self.tab_widget.addTab(self.map_view, '地图视图')
        self.tab_widget.addTab(self.vehicle_manager, '设备管理')
        self.tab_widget.addTab(self.task_manager, '任务管理')
        self.tab_widget.addTab(self.path_planner, '路径规划')
        self.tab_widget.addTab(self.system_monitor, '系统监控')
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('系统就绪')
        
        # 创建定时器用于更新状态
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # 每秒更新一次
        
    def load_map(self, map_file):
        """加载地图文件"""
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                map_data = f.read()
                self.map_view.load_map_data(map_data)
                self.statusBar.showMessage(f'成功加载地图：{map_file}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'加载地图文件失败：{str(e)}')
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        save_action = QAction('保存状态', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_state)
        file_menu.addAction(save_action)
        
        load_action = QAction('加载状态', self)
        load_action.setShortcut('Ctrl+L')
        load_action.triggered.connect(self.load_state)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        
        refresh_action = QAction('刷新', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_all)
        view_menu.addAction(refresh_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def init_scheduler(self):
        """初始化调度器"""
        try:
            # 读取示例地图数据
            with open('d:\\毕业设计\\TerraFly_System\\example_map.tfmap', 'r', encoding='utf-8') as f:
                map_data = json.loads(f.read())
            
            map_planner = SystemMapPlanner(config.config['map_center'], config.config['zoom_start'])
            # 初始化地图管理器
            map_planner.initialize_sync()
            # 加载示例地图数据到地图管理器
            map_planner.map_manager.load_map_data(map_data['objects'])
            
            # 创建环境管理器实例
            env_manager = EnvironmentManager()
            # 初始化环境管理器
            env_manager.ground_height = 0.0  # 设置地面基准高度
            # 创建飞行调度器并传入环境管理器
            flight_scheduler = FlightScheduler(env_manager)
            self.scheduler = UnifiedScheduler(map_planner, flight_scheduler)
            
            # 尝试加载之前的系统状态
            try:
                self.scheduler.load_state(config.config['storage']['state_file_path'])
                self.statusBar.showMessage('已加载系统状态')
            except Exception as e:
                self.statusBar.showMessage(f'加载系统状态失败: {str(e)}，使用初始状态')
            
            # 启动调度器
            self.scheduler.run()
            self.scheduler.run_monitor_loop()
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'初始化调度器失败: {str(e)}')
    
    def save_state(self):
        """保存系统状态"""
        try:
            if self.scheduler:
                self.scheduler.save_state(config.config['storage']['state_file_path'])
                self.statusBar.showMessage('系统状态已保存')
        except Exception as e:
            QMessageBox.warning(self, '警告', f'保存状态失败: {str(e)}')
    
    def load_state(self):
        """加载系统状态"""
        try:
            if self.scheduler:
                self.scheduler.load_state(config.config['storage']['state_file_path'])
                self.statusBar.showMessage('系统状态已加载')
                self.refresh_all()
        except Exception as e:
            QMessageBox.warning(self, '警告', f'加载状态失败: {str(e)}')
    
    def refresh_all(self):
        """刷新所有视图"""
        self.vehicle_manager.refresh()
        self.task_manager.refresh()
        self.path_planner.refresh()
        self.system_monitor.refresh()
        self.map_view.refresh()
        self.statusBar.showMessage('已刷新所有视图')
    
    def update_status(self):
        """更新状态栏信息"""
        if self.scheduler:
            status = self.scheduler.get_system_status()
            active_tasks = sum(1 for task in status['tasks'] if task['status'] != 'completed')
            active_vehicles = sum(1 for vehicle in status['vehicles'] if vehicle['status'] != 'idle')
            self.statusBar.showMessage(
                f'活动任务: {active_tasks} | 活动设备: {active_vehicles} | '
                f'系统状态: {status.get("system_status", "正常")}'
            )
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            '关于TerraFly调度管理系统',
            '这是一个用于管理和调度无人机和无人车的系统。\n\n'
            '功能包括：\n'
            '- 设备管理\n'
            '- 任务调度\n'
            '- 路径规划\n'
            '- 系统监控'
        )
    
    def closeEvent(self, event):
        """关闭窗口事件处理"""
        reply = QMessageBox.question(
            self, '确认',
            '是否要退出系统？\n注意：这将停止所有正在运行的任务。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 停止所有运行中的任务
            if self.scheduler:
                try:
                    # 保存当前状态
                    self.scheduler.save_state(config.config['storage']['state_file_path'])
                    
                    # 停止所有运行中的车辆
                    status = self.scheduler.get_system_status()
                    for vehicle in status['vehicles']:
                        if vehicle['status'] != 'idle':
                            self.scheduler.stop_vehicle(vehicle['id'])
                except Exception as e:
                    print(f'关闭系统时出错: {str(e)}')
            event.accept()
        else:
            event.ignore()

def main():
    """启动GUI应用"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()