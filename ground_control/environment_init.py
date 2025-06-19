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
    position: Tuple[float, float, float]  # 位置坐标(x, y, z)
    radius: float  # 障碍物半径
    height: float  # 障碍物高度
    type: str  # 障碍物类型（建筑物、设施等）

@dataclass
class DynamicZone:
    """动态区域"""
    center: Tuple[float, float, float]  # 区域中心坐标(x, y, z)
    radius: float  # 区域半径
    height: float  # 区域高度
    type: str  # 区域类型（人流密集区、装卸货区等）
    time_windows: List[Tuple[str, str]]  # 活跃时间窗口列表 [(开始时间, 结束时间)]

class EnvironmentManager:
    """园区环境管理器"""
    def __init__(self):
        self.static_obstacles: List[StaticObstacle] = []
        self.dynamic_zones: List[DynamicZone] = []
        self.boundary: List[Tuple[float, float, float]] = []  # 园区边界点(包含高度)
        self.paths: List[List[Tuple[float, float, float]]] = []  # 预定义路径(包含高度)
        self.charging_stations: List[Tuple[float, float, float]] = []  # 充电站位置(包含高度)
        self.ground_height: float = 0.0  # 地面基准高度
        
    def add_static_obstacle(self, position: Tuple[float, float, float], radius: float, height: float, type: str):
        """添加静态障碍物"""
        obstacle = StaticObstacle(position=position, radius=radius, height=height, type=type)
        self.static_obstacles.append(obstacle)
        
    def add_dynamic_zone(self, center: Tuple[float, float, float], radius: float, 
                         height: float, type: str, time_windows: List[Tuple[str, str]]):
        """添加动态区域"""
        zone = DynamicZone(center=center, radius=radius, height=height, type=type, time_windows=time_windows)
        self.dynamic_zones.append(zone)
        
    def set_boundary(self, points: List[Tuple[float, float, float]]):
        """设置园区边界"""
        self.boundary = points
        
    def add_path(self, path: List[Tuple[float, float, float]]):
        """添加预定义路径"""
        self.paths.append(path)
        
    def add_charging_station(self, position: Tuple[float, float, float]):
        """添加充电站"""
        self.charging_stations.append(position)
        
    def save_environment(self, filepath: str):
        """保存环境配置到文件"""
        env_data = {
            'static_obstacles': [
                {
                    'position': list(obs.position),
                    'radius': obs.radius,
                    'height': obs.height,
                    'type': obs.type
                }
                for obs in self.static_obstacles
            ],
            'dynamic_zones': [
                {
                    'center': list(zone.center),
                    'radius': zone.radius,
                    'height': zone.height,
                    'type': zone.type,
                    'time_windows': zone.time_windows
                }
                for zone in self.dynamic_zones
            ],
            'boundary': [list(point) for point in self.boundary],
            'paths': [[list(point) for point in path] for path in self.paths],
            'charging_stations': [list(station) for station in self.charging_stations],
            'ground_height': self.ground_height
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
                height=obs['height'],
                type=obs['type']
            )
            for obs in env_data['static_obstacles']
        ]
        
        # 加载动态区域
        self.dynamic_zones = [
            DynamicZone(
                center=tuple(zone['center']),
                radius=zone['radius'],
                height=zone['height'],
                type=zone['type'],
                time_windows=zone['time_windows']
            )
            for zone in env_data['dynamic_zones']
        ]
        
        self.boundary = [tuple(point) for point in env_data['boundary']]
        self.paths = [[tuple(point) for point in path] for path in env_data['paths']]
        self.charging_stations = [tuple(station) for station in env_data['charging_stations']]
        self.ground_height = env_data.get('ground_height', 0.0)
        
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
        
        # 创建图形
        fig = Figure(figsize=(8, 6))
        self.ax = fig.add_subplot(111, projection='3d')
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
    
    def get_3d_point(self, event):
        """将2D鼠标点击转换为3D坐标"""
        if event.inaxes != self.ax:
            return None
        
        # 获取当前高度
        height = self.current_height.get()
        return (event.xdata, event.ydata, height)
    
    def on_mouse_press(self, event):
        point = self.get_3d_point(event)
        if not point:
            return
        
        tool = self.current_tool.get()
        if not tool:
            return
        
        if tool == '边界':
            self.drawing = True
            self.current_path = [point]
            self.last_point = point
        elif tool == '路径':
            self.drawing = True
            self.current_path = [point]
            self.last_point = point
        elif tool == '障碍物':
            self.add_static_obstacle(point, radius=1.0, height=2.0, type='建筑物')
            self.update_plot()
            self.canvas.draw()
        elif tool == '动态区域':
            self.add_dynamic_zone(point, radius=2.0, height=3.0,
                                 type='活动区域', time_windows=[('08:00', '18:00')])
            self.update_plot()
            self.canvas.draw()
        elif tool == '充电站':
            self.add_charging_station(point)
            self.update_plot()
            self.canvas.draw()
    
    def on_mouse_release(self, event):
        if not self.drawing:
            return
        
        point = self.get_3d_point(event)
        if not point:
            return
        
        tool = self.current_tool.get()
        if tool == '边界':
            if len(self.current_path) > 2:  # 至少需要3个点形成有效边界
                self.set_boundary(self.current_path)
        elif tool == '路径':
            if len(self.current_path) > 1:  # 至少需要2个点形成有效路径
                self.add_path(self.current_path)
        
        self.drawing = False
        self.current_path = []
        self.last_point = None
        self.update_plot()
        self.canvas.draw()
    
    def on_mouse_move(self, event):
        point = self.get_3d_point(event)
        if not self.drawing or not point:
            return
        
        # 计算与上一个点的距离
        if self.last_point:
            dx = point[0] - self.last_point[0]
            dy = point[1] - self.last_point[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            # 如果距离太小，不添加新点
            if distance < 0.5:
                return
        
        self.current_path.append(point)
        self.last_point = point
        self.update_plot()
        
        # 绘制当前路径
        if self.current_path:
            path = np.array(self.current_path)
            self.ax.plot3D(path[:, 0], path[:, 1], path[:, 2], 'r--')
        
        self.canvas.draw()

def create_example_environment():
    """创建示例环境配置"""
    env = EnvironmentManager()
    
    # 设置园区边界（包含高度信息）
    boundary = [
        (0, 0, 0), (0, 100, 0), (150, 100, 0), (150, 0, 0)
    ]
    env.set_boundary(boundary)
    
    # 添加静态障碍物（建筑物和设施，包含高度）
    env.add_static_obstacle((30, 40, 0), 5, 15, '建筑物')  # 15米高的建筑物
    env.add_static_obstacle((80, 60, 0), 8, 12, '设施')   # 12米高的设施
    env.add_static_obstacle((120, 30, 0), 6, 10, '设施')  # 10米高的设施
    
    # 添加动态区域（包含高度限制）
    env.add_dynamic_zone(
        (50, 50, 0), 10, 5, '人流密集区',  # 5米高的活动区域
        [('08:00', '10:00'), ('12:00', '14:00'), ('17:00', '19:00')]
    )
    env.add_dynamic_zone(
        (100, 70, 0), 15, 8, '装卸货区',  # 8米高的活动区域
        [('09:00', '11:00'), ('14:00', '16:00')]
    )
    
    # 添加预定义路径（包含高度变化）
    path1 = [(0, 20, 0), (40, 20, 0), (40, 80, 0), (140, 80, 0)]
    path2 = [(0, 80, 0), (60, 80, 0), (60, 20, 0), (140, 20, 0)]
    env.add_path(path1)
    env.add_path(path2)
    
    # 添加充电站（地面位置）
    env.add_charging_station((10, 10, 0))
    env.add_charging_station((140, 90, 0))
    
    return env

if __name__ == '__main__':
    # 创建示例环境
    env = create_example_environment()
    
    # 保存环境配置
    env.save_environment('environment_config.json')
    
    # 可视化环境
    env.visualize_environment()