import numpy as np
import json
from typing import List, Tuple, Dict
from dataclasses import dataclass
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

@dataclass
class StaticObstacle:
    """静态障碍物"""
    position: Tuple[float, float]  # 位置坐标(x, y)
    radius: float  # 障碍物半径
    type: str  # 障碍物类型（建筑物、设施等）

@dataclass
class DynamicZone:
    """动态区域"""
    center: Tuple[float, float]  # 区域中心坐标
    radius: float  # 区域半径
    type: str  # 区域类型（人流密集区、装卸货区等）
    time_windows: List[Tuple[str, str]]  # 活跃时间窗口列表 [(开始时间, 结束时间)]

class EnvironmentManager:
    """园区环境管理器"""
    def __init__(self):
        self.static_obstacles: List[StaticObstacle] = []
        self.dynamic_zones: List[DynamicZone] = []
        self.boundary: List[Tuple[float, float]] = []  # 园区边界点
        self.paths: List[List[Tuple[float, float]]] = []  # 预定义路径
        self.charging_stations: List[Tuple[float, float]] = []  # 充电站位置
        
    def add_static_obstacle(self, position: Tuple[float, float], radius: float, type: str):
        """添加静态障碍物"""
        obstacle = StaticObstacle(position=position, radius=radius, type=type)
        self.static_obstacles.append(obstacle)
        
    def add_dynamic_zone(self, center: Tuple[float, float], radius: float, 
                         type: str, time_windows: List[Tuple[str, str]]):
        """添加动态区域"""
        zone = DynamicZone(center=center, radius=radius, type=type, time_windows=time_windows)
        self.dynamic_zones.append(zone)
        
    def set_boundary(self, points: List[Tuple[float, float]]):
        """设置园区边界"""
        self.boundary = points
        
    def add_path(self, path: List[Tuple[float, float]]):
        """添加预定义路径"""
        self.paths.append(path)
        
    def add_charging_station(self, position: Tuple[float, float]):
        """添加充电站"""
        self.charging_stations.append(position)
        
    def save_environment(self, filepath: str):
        """保存环境配置到文件"""
        env_data = {
            'static_obstacles': [
                {'position': list(obs.position), 'radius': obs.radius, 'type': obs.type}
                for obs in self.static_obstacles
            ],
            'dynamic_zones': [
                {
                    'center': list(zone.center),
                    'radius': zone.radius,
                    'type': zone.type,
                    'time_windows': zone.time_windows
                }
                for zone in self.dynamic_zones
            ],
            'boundary': self.boundary,
            'paths': self.paths,
            'charging_stations': self.charging_stations
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(env_data, f, indent=4, ensure_ascii=False)
            
    def load_environment(self, filepath: str):
        """从文件加载环境配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            env_data = json.load(f)
            
        # 加载静态障碍物
        self.static_obstacles = [
            StaticObstacle(
                position=tuple(obs['position']),
                radius=obs['radius'],
                type=obs['type']
            )
            for obs in env_data['static_obstacles']
        ]
        
        # 加载动态区域
        self.dynamic_zones = [
            DynamicZone(
                center=tuple(zone['center']),
                radius=zone['radius'],
                type=zone['type'],
                time_windows=zone['time_windows']
            )
            for zone in env_data['dynamic_zones']
        ]
        
        self.boundary = env_data['boundary']
        self.paths = env_data['paths']
        self.charging_stations = env_data['charging_stations']
        
    def visualize_environment(self):
        """可视化环境配置"""
        root = tk.Tk()
        root.title('园区环境编辑器')
        
        # 创建主框架
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(side=tk.LEFT, fill=tk.Y)
        
        # 创建绘图区域
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvasTkAgg(fig, master=main_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 添加工具按钮
        ttk.Label(toolbar, text='工具').pack(pady=5)
        tools = [
            ('边界', '绘制园区边界'),
            ('障碍物', '添加静态障碍物'),
            ('动态区域', '添加动态区域'),
            ('路径', '绘制预定义路径'),
            ('充电站', '添加充电站')
        ]
        
        self.current_tool = tk.StringVar(value='')
        for name, desc in tools:
            btn = ttk.Radiobutton(toolbar, text=name, value=name,
                                variable=self.current_tool)
            btn.pack(pady=2)
            ttk.Label(toolbar, text=desc, wraplength=100).pack(pady=(0, 10))
        
        # 添加保存和加载按钮
        ttk.Button(toolbar, text='保存', command=lambda: self.save_environment('environment_config.json')).pack(pady=5)
        ttk.Button(toolbar, text='加载', command=lambda: self.load_environment('environment_config.json')).pack(pady=5)
        
        # 初始化图形
        self.ax = fig.add_subplot(111)
        self.update_plot()
        
        # 绑定鼠标事件
        self.canvas = canvas
        self.fig = fig
        self.drawing = False
        self.current_path = []
        
        canvas.mpl_connect('button_press_event', self.on_mouse_press)
        canvas.mpl_connect('button_release_event', self.on_mouse_release)
        canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        root.mainloop()
    
    def update_plot(self):
        """更新图形显示"""
        self.ax.clear()
        
        # 绘制边界
        if self.boundary:
            boundary = np.array(self.boundary + [self.boundary[0]])
            self.ax.plot(boundary[:, 0], boundary[:, 1], 'k-', label='边界')
        
        # 绘制静态障碍物
        for obs in self.static_obstacles:
            circle = plt.Circle(obs.position, obs.radius, color='red', alpha=0.5)
            self.ax.add_patch(circle)
        
        # 绘制动态区域
        for zone in self.dynamic_zones:
            circle = plt.Circle(zone.center, zone.radius, color='yellow', alpha=0.3)
            self.ax.add_patch(circle)
        
        # 绘制预定义路径
        for path in self.paths:
            path_array = np.array(path)
            self.ax.plot(path_array[:, 0], path_array[:, 1], 'b--', alpha=0.5)
        
        # 绘制充电站
        if self.charging_stations:
            stations = np.array(self.charging_stations)
            self.ax.plot(stations[:, 0], stations[:, 1], 'g^', label='充电站')
        
        self.ax.grid(True)
        self.ax.legend()
        self.ax.set_title('园区环境配置')
        self.ax.set_aspect('equal')
        self.canvas.draw()
    
    def on_mouse_press(self, event):
        """鼠标按下事件处理"""
        if event.inaxes != self.ax:
            return
        
        tool = self.current_tool.get()
        if tool == '边界' or tool == '路径':
            self.drawing = True
            self.current_path = [(event.xdata, event.ydata)]
        elif tool == '障碍物':
            self.add_static_obstacle((event.xdata, event.ydata), 5, '建筑物')
            self.update_plot()
        elif tool == '动态区域':
            self.add_dynamic_zone(
                (event.xdata, event.ydata), 10, '人流密集区',
                [('08:00', '10:00'), ('12:00', '14:00')]
            )
            self.update_plot()
        elif tool == '充电站':
            self.add_charging_station((event.xdata, event.ydata))
            self.update_plot()
    
    def on_mouse_move(self, event):
        """鼠标移动事件处理"""
        if not self.drawing or event.inaxes != self.ax:
            return
        
        tool = self.current_tool.get()
        if tool in ['边界', '路径']:
            self.current_path.append((event.xdata, event.ydata))
            self.ax.clear()
            self.update_plot()
            path_array = np.array(self.current_path)
            self.ax.plot(path_array[:, 0], path_array[:, 1], 'r--')
            self.canvas.draw()
    
    def on_mouse_release(self, event):
        """鼠标释放事件处理"""
        if not self.drawing:
            return
        
        tool = self.current_tool.get()
        if tool == '边界':
            self.set_boundary(self.current_path)
        elif tool == '路径':
            self.add_path(self.current_path)
        
        self.drawing = False
        self.current_path = []
        self.update_plot()

def create_example_environment():
    """创建示例环境"""
    env = EnvironmentManager()
    
    # 设置园区边界
    boundary = [
        (0, 0), (0, 100), (150, 100), (150, 0)
    ]
    env.set_boundary(boundary)
    
    # 添加静态障碍物
    env.add_static_obstacle((30, 40), 5, '建筑物')
    env.add_static_obstacle((80, 60), 8, '设施')
    env.add_static_obstacle((120, 30), 6, '设施')
    
    # 添加动态区域
    env.add_dynamic_zone(
        (50, 50), 10, '人流密集区',
        [('08:00', '10:00'), ('12:00', '14:00'), ('17:00', '19:00')]
    )
    env.add_dynamic_zone(
        (100, 70), 15, '装卸货区',
        [('09:00', '11:00'), ('14:00', '16:00')]
    )
    
    # 添加预定义路径
    path1 = [(0, 20), (40, 20), (40, 80), (140, 80)]
    path2 = [(0, 80), (60, 80), (60, 20), (140, 20)]
    env.add_path(path1)
    env.add_path(path2)
    
    # 添加充电站
    env.add_charging_station((10, 10))
    env.add_charging_station((140, 90))
    
    return env

if __name__ == '__main__':
    # 创建示例环境
    env = create_example_environment()
    
    # 保存环境配置
    env.save_environment('environment_config.json')
    
    # 可视化环境
    env.visualize_environment()