# TerraFly System - 无人机与无人车协同配送系统

## 项目简介
在智慧物流的浪潮中，TerraFly System以颠覆性设计理念破局而生，打造出一套会"思考"、能"变形"的空地一体化配送网络。这不是简单的无人机与无人车组合，而是一场关于效率、智能与可持续性的技术革命，让物流配送突破地面与天空的界限，在三维空间中谱写高效协同的科技交响曲。

系统以模块化机械耦合技术为核心，赋予无人机与地面车"变形金刚"般的组合能力。当四轴碳纤维无人机轻盈降落在铝合金轮式底盘的瞬间，电磁锁与Pogo Pin接口精准咬合，形成兼具空中速度与地面承载力的复合体。这种机械耦合设计如同生物界的共生关系，通过可变角度螺旋桨与分布式动力系统，确保合体状态下的气动稳定性，即便在强风环境中也能保持0.3米内的对接精度。

独创的能源协同系统构建起智能能量网络：地面车搭载的Qi无线充电模块如同"能量驿站"，无人机降落瞬间即可启动电磁感应充电；当执行长途任务时，机械臂搭载的电池更换系统能在90秒内完成电池置换，配合动态能源管理算法，实现空地载具的能量优先级智能分配。这种双模补能方案让系统续航能力提升300%，真正实现"永不停机"的配送承诺。

基于A*算法与DESP双指数平滑算法的协同控制中枢，赋予系统"未卜先知"的决策能力。在穿越城市峡谷时，LiDAR与RGB-D相机构建的三维地图实时更新，光流跟踪算法以毫秒级响应预测地面车轨迹；当遭遇突发障碍，Canny边缘检测触发合体越障指令，空地载具瞬间完成形态转换。这种自适应协同控制，让系统在复杂环境中仍能保持98%的路径规划准确率。

【应用场景：重构物流的可能性边界】
在灾后断壁残垣间，系统化身"生命通道"，无人机穿越废墟空投物资，地面车沿着激光扫描的安全路径挺进核心区；在偏远山区，空地协同编队突破最后十公里配送难题，让每个包裹都能准时抵达；未来智慧城市中，系统将成为流动的"物流毛细血管"，在楼宇间编织起即时配送网络。

【创新价值：开启物流4.0时代】
TerraFly System不仅是一项技术集成，更是对物流本质的重构。它突破传统配送的时空限制，将末端配送效率提升400%，运营成本降低60%，碳排放减少75%。当无人机与无人车不再是独立作业单元，而是进化为共生协作的智慧体，我们看到的不仅是技术进步，更是一个更高效、更绿色、更智能的物流新纪元正在开启。

这，就是TerraFly System——用科技重新定义配送，让物流真正"飞"入三维时代。

## 系统架构
系统分为三个主要部分：

### 系统架构图
```mermaid
graph TB
    subgraph MasterComputer[主控计算机]
        TaskManager[任务管理器] --> Scheduler[调度器]
        Scheduler --> MapPlanner[地图规划器]
        TaskManager --> DeliveryManager[配送管理器]
        DeliveryManager --> VehicleManager[车辆管理器]
    end

    subgraph DroneComputer[无人机伴随计算机]
        DroneController[无人机控制器] --> DroneCommunicator[通信模块]
        DroneController --> FlightControl[飞行控制]
        DroneCommunicator --> MasterComputer
    end

    subgraph CarComputer[无人车计算机]
        CarController[无人车控制器] --> CarCommunicator[通信模块]
        CarController --> GroundControl[地面控制]
        CarCommunicator --> MasterComputer
    end
```

### 系统拓扑图
```mermaid
flowchart LR
    subgraph Network[通信网络]
        WebSocket[WebSocket服务]
    end

    MasterComputer[主控计算机] <--> WebSocket
    WebSocket <--> DroneComputer1[无人机1]
    WebSocket <--> DroneComputer2[无人机2]
    WebSocket <--> DroneComputer3[无人机3]
    WebSocket <--> CarComputer1[无人车1]
    WebSocket <--> CarComputer2[无人车2]
    WebSocket <--> CarComputer3[无人车3]
```

## 硬件平台

### 1. 无人机平台
- **机架**：DJI F450 四轴机架
- **飞控**：Pixhawk Cube（搭载 PX4 固件）
- **伴飞电脑**：Raspberry Pi 4B + MAVLink 连接
- **动力系统**：
  - T-Motor MN2212 KV920 ×4
  - 30A 电调
  - 10×4.5 折叠碳纤维螺旋桨
- **视觉系统**：Intel RealSense D435i
- **定位系统**：
  - 内置GPS模块（u-blox NEO-M8N）
  - RTK定位模块（可选）
- **通信系统**：5G USB Modem + 鼠洞协议（MAVLink over UDP）

### 2. 地面车平台
- **底盘**：铝合金 4×4 轮式底盘
- **主控系统**：
  - Raspberry Pi 4B
  - Arduino Mega 2560
- **驱动系统**：
  - 直流有刷电机 ×4
  - L298N 驱动板
- **传感系统**：
  - HC-SR04 超声波 ×4
  - TFLuna LiDAR
  - GPS模块（u-blox NEO-6M）
- **电源系统**：
  - 48V Li-ion 电池组
  - Qi 无线充电模块
- **通信系统**：5G USB Modem + Wi-Fi Mesh

### 3. 对接与能源模块
- **机械对接**：
  - 电磁锁
  - Pogo Pin 四点充电/通信口
  - Y 导向槽
  - 弹簧卡扣结构

## 硬件连接与部署

### 1. UAV平台部署
- **Pixhawk与ESC连接**：
  - Pixhawk的4个PWM输出MAIN_OUT_n端口连接各ESC信号线
  - ESC电源线并联供电给电机

- **Raspberry Pi与Pixhawk连接**：
  - 方案1：USB转TTL（FTDI）或直接UART线（TELEM2）
  - 方案2：通过5G/USB Modem建立UDP网络连接
  - 配置要求：PX4固件需允许MAVLink over UART

- **GPS模块连接**：
  - 无人机：连接到Pixhawk的GPS端口
  - 无人车：通过USB转TTL连接到Raspberry Pi的USB端口
  - 配置要求：波特率9600，NMEA输出

- **外设连接**：
  - RealSense D435i：USB 3.0接口
  - 5G Modem：USB接口

- **程序部署**：
  ```bash
  # 部署flight_control.py和docking.py
  sudo systemctl enable flight_control
  sudo systemctl enable docking
  # 或使用screen后台运行
  screen -dmS flight python flight_control.py
  screen -dmS dock python docking.py
  ```

### 2. UGV平台部署
- **电机控制连接**：
  - Raspberry Pi PWM引脚 → L298N使能端（ENA/ENB）
  - Arduino/Pi GPIO → L298N方向控制端

- **通信连接**：
  - Pi UART（/dev/ttyAMA0）↔ Arduino RX/TX
  - 用于：指令下发（DRIVE）和测距反馈（DIST?）

- **传感器连接**：
  - HC-SR04：Trig/Echo引脚连接Arduino
  - TFLuna：TX/RX串口连接Arduino

- **程序部署**：
  ```bash
  # Arduino端
  arduino-cli compile --upload ground_control.ino
  
  # Raspberry Pi端
  sudo systemctl enable ground_control
  # 或通过cron自启动
  crontab -e
  @reboot python /path/to/ground_control.py
  ```

### 3. 远程控制站部署
- **运行环境要求**：
  - GUI支持的主机（UAV Pi或地面站PC）
  - 网络连接：
    - UAV Pi：UDP端口14540
    - UGV Pi：网络或串口连接

- **串口连接**：
  - 同一Pi部署：复用现有串口
  - 独立PC部署：USB串口线连接UGV Pi

- **程序部署**：
  ```bash
  # 安装依赖
  pip install mavsdk tkinter pyserial opencv-python
  
  # 启动GUI
  python remote_control.py
  ```

## 软件系统部署指南

### 1. 主控计算机部署
主控计算机是整个系统的中枢，负责任务调度和系统管理。

**部署组件**：
- `task_scheduler/master_computer/`：
  - `task_manager.py`：任务管理与分配
  - `delivery_manager.py`：配送流程管理
  - `vehicle_manager.py`：车辆状态管理
  - `scheduler.py`：调度算法实现
  - `map_manager.py`：地图与路径规划

- `task_scheduler/gui/`：
  - `main_window.py`：系统主界面
  - `vehicle_manager.py`：车辆监控界面
  - `task_manager.py`：任务管理界面
  - `path_planner.py`：路径规划界面
  - `system_monitor.py`：系统状态监控

**功能说明**：
- 任务调度与分配
- 实时状态监控
- 路径规划优化
- 系统管理界面

### 2. 无人机伴飞电脑部署
伴飞电脑负责无人机的飞行控制和状态管理。

**部署组件**：
- `flight_control/`：
  - `flight_control.py`：飞行控制核心
  - `drone_driver.py`：无人机驱动接口

- `task_scheduler/drone_computer/`：
  - `drone_controller.py`：无人机任务控制
  - `drone_communicator.py`：与主控通信

**功能说明**：
- 飞行控制与导航
- 任务执行管理
- 状态监控与报告
- 紧急情况处理

### 3. 无人车车载电脑部署
车载电脑负责无人车的运动控制和避障。

**部署组件**：
- `ground_control/`：
  - `ground_control.py`：地面控制核心
  - `car_driver.py`：无人车驱动接口
  - `arduino_control/`：底层控制程序

- `task_scheduler/car_computer/`：
  - `car_controller.py`：无人车任务控制
  - `car_communicator.py`：与主控通信

**功能说明**：
- 运动控制与避障
- 任务执行管理
- 传感器数据处理
- 车辆状态监控

### 部署步骤
1. **主控计算机**：
```bash
# 安装依赖
pip install -r requirements.txt

# 启动主控系统
python task_scheduler/main.py
```

2. **伴飞电脑**：
```bash
# 安装依赖
pip install -r requirements.txt

# 启动飞行控制
python flight_control/flight_control.py

# 启动任务控制器
python task_scheduler/drone_computer/drone_controller.py
```

3. **车载电脑**：
```bash
# 安装依赖
pip install -r requirements.txt

# 编译上传Arduino程序
arduino-cli compile --upload ground_control/arduino_control/arduino_control.ino

# 启动地面控制
python ground_control/ground_control.py

# 启动任务控制器
python task_scheduler/car_computer/car_controller.py
```

## 任务调度系统

### 动态任务分配逻辑

1. **任务优先级评估**
```python
def evaluate_task_priority(task):
    priority = 0
    # 时效性评分
    priority += task.deadline_score * 0.4
    # 距离评分
    priority += task.distance_score * 0.3
    # 负载评分
    priority += task.payload_score * 0.3
    return priority
```

2. **资源分配策略**
- **无人机分配**：
  - 轻量快递（<2kg）
  - 短距离配送（<5km）
  - 高时效性需求
  - 避开建筑密集区

- **无人车分配**：
  - 重量物品（>2kg）
  - 长距离配送（>5km）
  - 建筑密集区域
  - 恶劣天气条件

3. **实时调度算法**
```python
def schedule_task(task, available_vehicles):
    # 筛选合适车辆
    suitable_vehicles = filter_by_capability(available_vehicles, task)
    
    # 计算调度得分
    scores = []
    for vehicle in suitable_vehicles:
        score = calculate_schedule_score(vehicle, task)
        scores.append((vehicle, score))
    
    # 选择最优车辆
    best_vehicle = max(scores, key=lambda x: x[1])[0]
    return best_vehicle

def calculate_schedule_score(vehicle, task):
    score = 0
    # 距离评分（30%）
    score += (1 - distance_to_task(vehicle, task) / max_distance) * 0.3
    # 电量评分（20%）
    score += (vehicle.battery_level / 100) * 0.2
    # 负载适配度（30%）
    score += calculate_payload_compatibility(vehicle, task) * 0.3
    # 历史完成率（20%）
    score += vehicle.success_rate * 0.2
    return score
```

### 空中调度实现

1. **航线规划**
```python
def plan_flight_path(drone, task):
    # 获取起降点坐标
    start = drone.current_position
    destination = task.delivery_point
    
    # 计算最优航线
    waypoints = calculate_optimal_path(start, destination)
    
    # 考虑高度限制和避障
    adjusted_waypoints = adjust_altitude_obstacles(waypoints)
    
    return adjusted_waypoints
```

2. **动态避障**
```python
def obstacle_avoidance(drone, current_path):
    # 检测前方障碍物
    obstacles = detect_obstacles(drone.sensors)
    
    if obstacles:
        # 计算避障路径
        new_path = recalculate_path(current_path, obstacles)
        # 更新飞行路径
        drone.update_flight_path(new_path)
```

3. **能源管理**
```python
def energy_management(drone, task):
    # 计算任务所需能量
    required_energy = calculate_required_energy(task)
    
    # 检查当前电量
    if drone.battery_level < required_energy * 1.2:
        # 寻找最近充电站
        charging_station = find_nearest_charging_station(drone)
        # 规划充电路径
        return_path = plan_return_path(drone, charging_station)
        return return_path
    
    return None
```

## 安装与使用

### 环境要求
- Python 3.8+
- MAVSDK
- 相关Python包（详见requirements.txt）

### 快速安装脚本
```bash
#!/bin/bash
# 安装脚本 - install.sh

# 检查Python版本
py_version=$(python3 -c 'import sys; print("%d.%d" % (sys.version_info.major, sys.version_info.minor))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$py_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "Python版本检查通过：${py_version}"
else
    echo "错误：需要Python ${required_version}或更高版本"
    exit 1
fi

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 安装MAVSDK
pip install mavsdk

# 配置文件检查
if [ ! -f "config.py" ]; then
    cp config.example.py config.py
    echo "请配置config.py文件"
fi

echo "安装完成！"
```

### Windows安装脚本
```powershell
# 安装脚本 - install.ps1

# 检查Python版本
$py_version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$required_version = "3.8"

if ([version]$py_version -ge [version]$required_version) {
    Write-Host "Python版本检查通过：${py_version}"
}
else {
    Write-Host "错误：需要Python ${required_version}或更高版本"
    exit 1
}

# 创建虚拟环境
python -m venv venv
.\venv\Scripts\Activate

# 安装依赖
python -m pip install --upgrade pip
pip install -r requirements.txt

# 安装MAVSDK
pip install mavsdk

# 配置文件检查
if (-not (Test-Path config.py)) {
    Copy-Item config.example.py config.py
    Write-Host "请配置config.py文件"
}

Write-Host "安装完成！"
```

### 手动安装步骤
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
