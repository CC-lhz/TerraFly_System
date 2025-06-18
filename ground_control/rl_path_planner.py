import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque, namedtuple
import random
import math
from typing import List, Tuple, Dict

Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])

class DQN(nn.Module):
    """深度Q网络模型"""
    def __init__(self, state_dim: int, action_dim: int):
        super(DQN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim)
        )
    
    def forward(self, x):
        return self.network(x)

class RLPathPlanner:
    """基于强化学习的局部路径规划器"""
    def __init__(self):
        # 状态空间：[当前速度, 当前航向角, 与预定路径的偏差, 8个方向的障碍物距离]
        self.state_dim = 11
        # 动作空间：[加速, 减速, 左转, 右转, 保持]
        self.action_dim = 5
        
        # DQN网络
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = DQN(self.state_dim, self.action_dim).to(self.device)
        self.target_net = DQN(self.state_dim, self.action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # 优化器
        self.optimizer = optim.Adam(self.policy_net.parameters())
        
        # 经验回放缓冲区
        self.memory = deque(maxlen=10000)
        self.batch_size = 64
        
        # 训练参数
        self.gamma = 0.99  # 折扣因子
        self.epsilon = 1.0  # 探索率
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.target_update = 10  # 目标网络更新频率
        self.training_step = 0
        
    def get_state(self, current_pos: Tuple[float, float], current_vel: float, current_heading: float,
                  path_deviation: float, sensor_data: Dict) -> torch.Tensor:
        """构建状态向量"""
        # 获取当前速度和航向角
        velocity = min(current_vel, 2.0)  # 限制最大速度为2米/秒
        heading = current_heading
        
        # 获取与预定路径的偏差（限制最大偏差为2米）
        deviation = min(abs(path_deviation), 2.0)
        
        # 获取8个方向的障碍物距离
        obstacle_distances = [float('inf')] * 8
        if 'ultrasonic' in sensor_data and sensor_data['ultrasonic']:
            for i, dist in enumerate(sensor_data['ultrasonic']):
                obstacle_distances[i] = min(dist, 5.0)  # 限制最大距离为5米
        
        # 构建状态向量
        state = [velocity, heading, deviation] + obstacle_distances
        return torch.FloatTensor(state).unsqueeze(0).to(self.device)
    
    def select_action(self, state: torch.Tensor) -> int:
        """选择动作（epsilon-贪婪策略）"""
        if random.random() > self.epsilon:
            with torch.no_grad():
                return self.policy_net(state).max(1)[1].item()
        else:
            return random.randrange(self.action_dim)
    
    def store_experience(self, state, action, reward, next_state, done):
        """存储经验到回放缓冲区"""
        self.memory.append(Experience(state, action, reward, next_state, done))
    
    def train(self):
        """训练DQN网络"""
        if len(self.memory) < self.batch_size:
            return
        
        # 随机采样batch_size个经验
        experiences = random.sample(self.memory, self.batch_size)
        batch = Experience(*zip(*experiences))
        
        # 准备批量数据
        state_batch = torch.cat(batch.state)
        action_batch = torch.LongTensor([batch.action]).to(self.device)
        reward_batch = torch.FloatTensor(batch.reward).to(self.device)
        next_state_batch = torch.cat(batch.next_state)
        done_batch = torch.FloatTensor(batch.done).to(self.device)
        
        # 计算当前Q值
        current_q_values = self.policy_net(state_batch).gather(1, action_batch)
        
        # 计算目标Q值
        with torch.no_grad():
            max_next_q_values = self.target_net(next_state_batch).max(1)[0]
            target_q_values = reward_batch + (1 - done_batch) * self.gamma * max_next_q_values
        
        # 计算损失并优化
        loss = nn.MSELoss()(current_q_values, target_q_values.unsqueeze(1))
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # 更新目标网络
        self.training_step += 1
        if self.training_step % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # 衰减探索率
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def get_action_commands(self, action: int, current_vel: float) -> Tuple[float, float]:
        """将动作转换为速度命令"""
        base_vel = current_vel
        if action == 0:  # 加速
            return (base_vel + 0.2, base_vel + 0.2)
        elif action == 1:  # 减速
            return (base_vel - 0.2, base_vel - 0.2)
        elif action == 2:  # 左转
            return (base_vel * 0.5, base_vel)
        elif action == 3:  # 右转
            return (base_vel, base_vel * 0.5)
        else:  # 保持
            return (base_vel, base_vel)
    
    def calculate_reward(self, path_deviation: float, current_vel: float, sensor_data: Dict) -> Tuple[float, bool]:
        """计算奖励和是否完成"""
        # 检查是否碰撞
        min_distance = float('inf')
        if 'ultrasonic' in sensor_data and sensor_data['ultrasonic']:
            min_distance = min(sensor_data['ultrasonic'])
        if min_distance < 0.2:  # 碰撞
            return -100.0, True
        
        # 路径偏差惩罚（偏离预定路径越远惩罚越大）
        deviation_penalty = -abs(path_deviation)
        
        # 安全奖励（与障碍物保持安全距离）
        safety_reward = 0.0
        if min_distance < 1.0:  # 小于1米时给予奖励
            safety_reward = (min_distance - 0.2) / 0.8  # 归一化到[0,1]
        
        # 速度奖励（保持合理速度）
        velocity_reward = 0.0
        if 0.5 <= current_vel <= 1.5:  # 速度在合理范围内
            velocity_reward = 1.0
        
        # 综合奖励
        total_reward = deviation_penalty + 2.0 * safety_reward + velocity_reward
        
        return total_reward, False
    
    def save_model(self, path: str):
        """保存模型"""
        torch.save({
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, path)
    
    def load_model(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']