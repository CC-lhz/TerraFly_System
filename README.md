# TerraFly System - 无人机与无人车协同配送系统

## 项目简介
TerraFly System是一个创新的无人机与无人车协同配送系统，旨在提供高效、智能的物流配送解决方案。系统整合了无人机空中配送和无人车地面配送的优势，实现了全自动化的配送服务。

## 系统架构
系统分为三个主要部分：

### 1. 主控计算机 (Master Computer)
- 负责全局任务规划和调度
- 管理配送任务分配
- 路径规划优化
- 实时监控系统状态

### 2. 无人机伴随计算机 (Companion Computer)
- 控制无人机飞行
- 监控飞行状态
- 处理任务执行
- 实时通信管理

### 3. 无人车计算机 (Car Computer)
- 控制无人车运动
- 监控车辆状态
- 处理装卸任务
- 障碍物避免

## 主要功能模块

### 任务调度系统 (Task Scheduler)
- 智能任务分配
- 实时调度优化
- 多车协同调度
- 任务优先级管理

### 自主控制系统 (Autonomous Control)
- 无人机飞行控制
- 无人车运动控制
- 自主导航
- 状态监控

### 通信系统
- 实时数据传输
- 心跳检测
- 状态同步
- 错误处理

### 地图规划系统 (Map Planner)
- 路径规划
- 避障算法
- 地理信息处理
- 实时路径优化

## 技术特点
- 基于Python的模块化设计
- WebSocket实时通信
- 多线程任务处理
- 实时状态监控
- 自动故障恢复
- 可扩展的插件系统

## 安装与使用

### 环境要求
- Python 3.8+
- MAVSDK
- 相关Python包（详见requirements.txt）

### 安装步骤
1. 克隆仓库
```bash
git clone https://github.com/CC-lhz/TerraFly_System.git
```

2. 安装依赖
```bash
cd TerraFly_System
pip install -r requirements.txt
```

3. 配置系统
- 修改config.py中的配置参数
- 设置通信端口和地址
- 配置地图API密钥

### 启动系统
```bash
python task_scheduler/main.py
```

## 测试
系统提供了完整的测试框架：
```bash
python task_scheduler/test_scheduler.py
```

## 贡献
欢迎提交问题和改进建议！

## 许可证
MIT License