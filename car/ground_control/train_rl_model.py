import numpy as np
import torch
from rl_path_planner import RLPathPlanner
from environment_mapper import EnvironmentMapper
import random
import math
import time
from typing import List, Tuple

class RLTrainingEnvironment:
    """强化学习训练环境"""
    def __init__(self):
        self.env_mapper = EnvironmentMapper()
        self.reset()
    
    def reset(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """重置环境，返回：(起点坐标, 终点坐标)"""
        # 随机生成起点和终点
        self.start_pos = (random.uniform(-5, 5), random.uniform(-5, 5))
        self.target_pos = (random.uniform(-5, 5), random.uniform(-5, 5))
        
        # 随机生成障碍物
        self.obstacles = []
        for _ in range(random.randint(3, 8)):
            pos = (random.uniform(-5, 5), random.uniform(-5, 5))
            radius = random.uniform(0.2, 0.5)
            self.obstacles.append({'position': pos, 'radius': radius})
        
        # 重置当前位置
        self.current_pos = self.start_pos
        
        return self.current_pos, self.target_pos
    
    def step(self, action: Tuple[float, float]) -> Tuple[Dict, Tuple[float, float]]:
        """执行动作，返回：(传感器数据, 新位置)"""
        # 更新位置
        speed = 0.1  # 每步移动距离
        dx = (action[0] + action[1]) * speed / 2  # 前进分量
        dy = (action[0] - action[1]) * speed / 2  # 转向分量
        new_x = self.current_pos[0] + dx
        new_y = self.current_pos[1] + dy
        self.current_pos = (new_x, new_y)
        
        # 模拟传感器数据
        sensor_data = {'ultrasonic': []}
        angles = [-60, -30, 0, 30, 60]  # 5个超声波传感器角度
        
        for angle in angles:
            # 计算传感器朝向
            rad_angle = math.radians(angle)
            direction = (math.cos(rad_angle), math.sin(rad_angle))
            
            # 计算与障碍物的距离
            min_distance = float('inf')
            for obs in self.obstacles:
                # 计算障碍物相对位置
                dx = obs['position'][0] - self.current_pos[0]
                dy = obs['position'][1] - self.current_pos[1]
                
                # 计算投影距离
                proj_dist = dx * direction[0] + dy * direction[1]
                if proj_dist > 0:  # 只考虑前方的障碍物
                    # 计算垂直距离
                    perp_dist = abs(dx * direction[1] - dy * direction[0])
                    if perp_dist < obs['radius']:
                        # 计算实际距离
                        dist = math.sqrt(dx*dx + dy*dy) - obs['radius']
                        min_distance = min(min_distance, dist)
            
            sensor_data['ultrasonic'].append(min_distance)
        
        return sensor_data, self.current_pos

def train_rl_model(episodes: int = 1000, steps_per_episode: int = 200):
    """训练强化学习模型"""
    # 初始化环境和智能体
    env = RLTrainingEnvironment()
    agent = RLPathPlanner()
    
    # 训练循环
    for episode in range(episodes):
        # 重置环境
        current_pos, target_pos = env.reset()
        episode_reward = 0
        
        for step in range(steps_per_episode):
            # 获取当前状态
            sensor_data, _ = env.step((0, 0))  # 获取初始传感器数据
            state = agent.get_state(current_pos, target_pos, sensor_data)
            
            # 选择动作
            action_idx = agent.select_action(state)
            action = agent.get_action_commands(action_idx)
            
            # 执行动作
            next_sensor_data, next_pos = env.step(action)
            
            # 计算奖励
            reward, done = agent.calculate_reward(next_pos, target_pos, next_sensor_data)
            episode_reward += reward
            
            # 获取下一个状态
            next_state = agent.get_state(next_pos, target_pos, next_sensor_data)
            
            # 存储经验
            agent.store_experience(state, action_idx, reward, next_state, done)
            
            # 训练智能体
            agent.train()
            
            # 更新状态
            current_pos = next_pos
            
            if done:
                break
        
        # 打印训练进度
        if (episode + 1) % 10 == 0:
            print(f"Episode {episode + 1}/{episodes}, Reward: {episode_reward:.2f}, Epsilon: {agent.epsilon:.3f}")
        
        # 保存模型
        if (episode + 1) % 100 == 0:
            agent.save_model(f"rl_model_episode_{episode + 1}.pth")

def test_rl_model(model_path: str, episodes: int = 10):
    """测试训练好的模型"""
    # 初始化环境和智能体
    env = RLTrainingEnvironment()
    agent = RLPathPlanner()
    agent.load_model(model_path)
    agent.epsilon = 0  # 测试时不使用探索
    
    total_reward = 0
    success_count = 0
    
    for episode in range(episodes):
        current_pos, target_pos = env.reset()
        episode_reward = 0
        
        for step in range(200):
            # 获取当前状态
            sensor_data, _ = env.step((0, 0))
            state = agent.get_state(current_pos, target_pos, sensor_data)
            
            # 选择动作
            action_idx = agent.select_action(state)
            action = agent.get_action_commands(action_idx)
            
            # 执行动作
            next_sensor_data, next_pos = env.step(action)
            
            # 计算奖励
            reward, done = agent.calculate_reward(next_pos, target_pos, next_sensor_data)
            episode_reward += reward
            
            # 更新状态
            current_pos = next_pos
            
            if done:
                if reward > 0:  # 成功到达目标
                    success_count += 1
                break
        
        total_reward += episode_reward
        print(f"Test Episode {episode + 1}, Reward: {episode_reward:.2f}")
    
    print(f"\nAverage Reward: {total_reward/episodes:.2f}")
    print(f"Success Rate: {success_count/episodes*100:.1f}%")

if __name__ == "__main__":
    # 训练模型
    print("开始训练强化学习模型...")
    train_rl_model(episodes=1000)
    
    # 测试模型
    print("\n开始测试模型...")
    test_rl_model("rl_model_episode_1000.pth")