import time
import serial
import config
import math
from typing import List, Tuple
from enum import Enum
import random
from rl_path_planner import RLPathPlanner
import torch

class PathStatus(Enum):
    """路径执行状态"""
    IDLE = 'idle'  # 空闲
    FOLLOWING = 'following'  # 跟踪路径中
    AVOIDING = 'avoiding'  # 避障中
    REPLANNING = 'replanning'  # 重规划中
    FINISHED = 'finished'  # 完成

class GroundControl:
    """
    地面车路径跟踪和避障控制程序。
    通过串口与Arduino通信，发送速度命令并读取传感器数据进行避障。
    支持超声波传感器和激光雷达的可选配置。
    """
    def __init__(self, use_ultrasonic=True, use_lidar=True, rl_model_path=None):
        self.use_ultrasonic = use_ultrasonic
        self.use_lidar = use_lidar
        
        # 初始化串口连接
        self.ser = serial.Serial(config.SERIAL_PORT, config.BAUDRATE, timeout=1)
        time.sleep(2)  # 等待串口稳定
        print(f"连接到 Arduino 串口: {config.SERIAL_PORT}")
        
        # 传感器数据
        self.sensor_data = {
            'ultrasonic': [float('inf')] * 4 if use_ultrasonic else None,
            'lidar': float('inf') if use_lidar else None
        }
        
        # 路径跟踪状态
        self.path_status = PathStatus.IDLE
        self.current_waypoint_index = 0
        self.waypoints = []
        self.original_waypoints = []
        
        # 避障参数
        self.avoiding = False
        self.last_avoid_time = 0
        self.avoid_cooldown = 1.0  # 避障冷却时间（秒）
        self.avoid_turn_direction = 1  # 1表示右转，-1表示左转
        self.local_path = []  # 局部避障路径
        
        # 运动控制参数
        self.current_speed = 0
        self.current_heading = 0  # 当前航向角（弧度）
        self.position = (0, 0)  # 当前位置(x, y)
        
        # 初始化强化学习模型
        self.rl_planner = RLPathPlanner()
        if rl_model_path:
            self.rl_planner.load_model(rl_model_path)
            print(f"加载强化学习模型: {rl_model_path}")
        self.use_rl = rl_model_path is not None

    def set_speed(self, left_speed, right_speed):
        """
        设置左右电机速度。
        参数速度范围 0~255，正值前进，负值后退。
        """
        cmd = f"M,{left_speed},{left_speed},{right_speed},{right_speed}\n"
        self.ser.write(cmd.encode())

    def stop(self):
        """停止地面车"""
        self.set_speed(0, 0)
        self.avoiding = False

    def update_sensor_data(self):
        """
        更新传感器数据。
        解析Arduino发送的传感器数据，格式：
        - 超声波：US,dist1,dist2,dist3,dist4
        - 激光雷达：LD,dist
        """
        if not self.ser.in_waiting:
            return
            
        try:
            line = self.ser.readline().decode('utf-8').strip()
            if self.use_ultrasonic and line.startswith("US,"):
                # 更新超声波数据
                values = [float(x) for x in line[3:].split(",")]
                if len(values) == 4:
                    self.sensor_data['ultrasonic'] = values
            elif self.use_lidar and line.startswith("LD,"):
                # 更新激光雷达数据
                self.sensor_data['lidar'] = float(line[3:])
        except (ValueError, IndexError) as e:
            print(f"解析传感器数据错误: {e}")

    def check_obstacles(self):
        """
        检查是否存在障碍物。
        根据可用的传感器进行综合判断。
        """
        min_distance = float('inf')
        
        # 检查超声波数据
        if self.use_ultrasonic and self.sensor_data['ultrasonic']:
            min_distance = min(min_distance, min(self.sensor_data['ultrasonic']))
        
        # 检查激光雷达数据
        if self.use_lidar and self.sensor_data['lidar'] is not None:
            min_distance = min(min_distance, self.sensor_data['lidar'])
        
        return min_distance < config.SAFE_DISTANCE

    def follow_path(self, waypoints: List[Tuple[float, float]]):
        """
        开始路径跟踪。
        :param waypoints: 路径点列表，每个点为(x, y)坐标
        """
        if not waypoints:
            return
            
        self.waypoints = waypoints
        self.original_waypoints = waypoints.copy()
        self.current_waypoint_index = 0
        self.path_status = PathStatus.FOLLOWING
        print(f"开始路径跟踪，共{len(waypoints)}个路径点")
    
    def update_position(self, dx, dy):
        """
        更新当前位置
        :param dx: x方向位移
        :param dy: y方向位移
        """
        x, y = self.position
        self.position = (x + dx, y + dy)
    
    def calculate_target_heading(self) -> float:
        """
        计算指向当前目标点的航向角
        :return: 目标航向角（弧度）
        """
        if self.current_waypoint_index >= len(self.waypoints):
            return self.current_heading
            
        target = self.waypoints[self.current_waypoint_index]
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        return math.atan2(dy, dx)
    
    def get_heading_error(self) -> float:
        """
        计算航向误差
        :return: 航向误差（弧度）
        """
        target_heading = self.calculate_target_heading()
        error = target_heading - self.current_heading
        # 归一化到[-pi, pi]
        return (error + math.pi) % (2 * math.pi) - math.pi
    
    def avoid_obstacle(self):
        """
        执行避障操作。
        根据是否启用强化学习模型选择避障策略。
        """
        current_time = time.time()
        
        # 避障冷却检查
        if current_time - self.last_avoid_time < self.avoid_cooldown:
            return
        
        if self.check_obstacles():
            print("检测到障碍物，执行避障操作")
            self.avoiding = True
            self.last_avoid_time = current_time
            self.path_status = PathStatus.AVOIDING
            
            if self.use_rl and len(self.waypoints) > self.current_waypoint_index:
                # 使用强化学习模型进行避障决策
                target_pos = self.waypoints[self.current_waypoint_index]
                state = self.rl_planner.get_state(self.position, target_pos, self.sensor_data)
                
                with torch.no_grad():
                    action_idx = self.rl_planner.select_action(state)
                    action = self.rl_planner.get_action_commands(action_idx)
                
                # 将RL动作转换为实际速度命令
                left_speed = action[0] * config.FORWARD_SPEED
                right_speed = action[1] * config.FORWARD_SPEED
                self.set_speed(left_speed, right_speed)
                
                # 更新局部路径
                self.replan_local_path()
            else:
                # 使用传统避障策略
                # 随机选择避障方向
                self.avoid_turn_direction = random.choice([-1, 1])
                
                # 停止并后退
                self.stop()
                time.sleep(0.5)
                self.set_speed(-config.REVERSE_SPEED, -config.REVERSE_SPEED)
                time.sleep(1.0)
                
                # 转向避障
                turn_speed = config.TURN_SPEED * self.avoid_turn_direction
                self.set_speed(-turn_speed, turn_speed)
                time.sleep(1.0)
                
                # 继续前进
                self.set_speed(config.FORWARD_SPEED, config.FORWARD_SPEED)
                
                # 更新局部路径
                self.replan_local_path()
        elif self.avoiding:
            # 检查是否可以返回原路径
            if not self.check_obstacles():
                self.avoiding = False
                self.path_status = PathStatus.FOLLOWING
                print("避障完成，返回原路径")
    
    def replan_local_path(self):
        """
        重新规划局部路径，避开障碍物
        """
        if self.current_waypoint_index >= len(self.waypoints):
            return
            
        # 创建避障路径点
        current_target = self.waypoints[self.current_waypoint_index]
        avoid_distance = 1.0  # 避障距离（米）
        
        # 计算避障点
        angle = self.current_heading + math.pi/2 * self.avoid_turn_direction
        avoid_x = self.position[0] + avoid_distance * math.cos(angle)
        avoid_y = self.position[1] + avoid_distance * math.sin(angle)
        
        # 更新局部路径
        self.local_path = [
            self.position,
            (avoid_x, avoid_y),
            current_target
        ]
        
        print(f"重新规划局部路径: {self.local_path}")
    
    def update_path_following(self):
        """
        更新路径跟踪状态
        """
        if self.path_status not in [PathStatus.FOLLOWING, PathStatus.AVOIDING]:
            return
            
        # 检查是否到达当前路径点
        if self.current_waypoint_index < len(self.waypoints):
            target = self.waypoints[self.current_waypoint_index]
            dx = target[0] - self.position[0]
            dy = target[1] - self.position[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 0.5:  # 到达阈值（米）
                self.current_waypoint_index += 1
                print(f"到达路径点 {self.current_waypoint_index}/{len(self.waypoints)}")
                
                if self.current_waypoint_index >= len(self.waypoints):
                    self.path_status = PathStatus.FINISHED
                    self.stop()
                    print("路径跟踪完成")
                    return
        
        # 更新运动控制
        self.update_motion_control()
    
    def update_motion_control(self):
        """
        更新运动控制指令
        """
        # 计算航向误差
        heading_error = self.get_heading_error()
        
        # 根据航向误差调整左右轮速度
        base_speed = config.FORWARD_SPEED
        turn_ratio = min(abs(heading_error) / math.pi, 1.0)
        
        if heading_error > 0:  # 需要左转
            left_speed = base_speed * (1 - turn_ratio)
            right_speed = base_speed
        else:  # 需要右转
            left_speed = base_speed
            right_speed = base_speed * (1 - turn_ratio)
        
        # 发送速度指令
        self.set_speed(left_speed, right_speed)
        
        # 更新位置（简化的位置推算）
        speed = (left_speed + right_speed) / 2
        distance = speed * 0.1  # 假设控制周期为0.1秒
        dx = distance * math.cos(self.current_heading)
        dy = distance * math.sin(self.current_heading)
        self.update_position(dx, dy)
    
    def run(self):
        """
        主循环，处理传感器数据和路径跟踪
        """
        try:
            while True:
                # 更新传感器数据
                self.update_sensor_data()
                
                # 处理避障
                if self.check_obstacles():
                    self.avoid_obstacle()
                
                # 更新路径跟踪
                if self.path_status != PathStatus.IDLE:
                    self.update_path_following()
                
                # 控制循环延时
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("程序终止")
            self.stop()
        except Exception as e:
            print(f"运行错误: {str(e)}")
            self.stop()
        finally:
            self.ser.close()
    
    def get_status(self) -> dict:
        """
        获取当前状态信息
        """
        return {
            'path_status': self.path_status.value,
            'current_waypoint': self.current_waypoint_index,
            'total_waypoints': len(self.waypoints),
            'position': self.position,
            'heading': self.current_heading,
            'avoiding': self.avoiding,
            'sensor_data': self.sensor_data
        }

    def avoid_obstacle(self):
        """
        避障控制。
        如果检测到障碍物，执行避障动作。
        返回True表示正在避障，False表示无需避障。
        """
        if self.avoiding:
            return True

        # 检查传感器数据
        if self.sensor_data['distance'] < config.SAFE_DISTANCE:
            self.avoiding = True
            
            # 后退
            self.set_speed(-config.REVERSE_SPEED, -config.REVERSE_SPEED)
            time.sleep(1.0)
            
            # 随机选择转向方向
            import random
            turn_direction = 1 if random.random() > 0.5 else -1
            self.set_speed(
                turn_direction * config.TURN_SPEED,
                -turn_direction * config.TURN_SPEED
            )
            time.sleep(1.5)
            
            self.stop()
            return True
        
        self.avoiding = False
        return False

    def run(self):
        """
        地面车主循环。
        持续前进并避开障碍物。
        """
        print("地面车避障控制启动")
        try:
            while True:
                if not self.avoid_obstacle():
                    # 默认前进
                    self.set_speed(config.FORWARD_SPEED, config.FORWARD_SPEED)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("停止地面车控制")
            self.stop()

if __name__ == "__main__":
    gc = GroundControl()
    gc.run()
