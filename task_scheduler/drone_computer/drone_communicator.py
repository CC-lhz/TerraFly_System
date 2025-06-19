from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
import logging
import asyncio
import json
import websockets
from enum import Enum

class MessageType(Enum):
    """消息类型"""
    HEARTBEAT = 'heartbeat'  # 心跳消息
    STATUS = 'status'  # 状态消息
    COMMAND = 'command'  # 控制命令
    TASK = 'task'  # 任务消息
    TELEMETRY = 'telemetry'  # 遥测数据
    LOG = 'log'  # 日志消息
    ERROR = 'error'  # 错误消息

class DroneCommunicator:
    """无人机通信器"""
    def __init__(
        self,
        drone_id: str,
        master_url: str,
        drone_port: int,
        status_callback: Callable = None,
        command_callback: Callable = None,
        task_callback: Callable = None
    ):
        self.drone_id = drone_id
        self.master_url = master_url
        self.drone_port = drone_port
        self.logger = logging.getLogger(f'DroneCommunicator_{drone_id}')
        
        # 回调函数
        self.status_callback = status_callback
        self.command_callback = command_callback
        self.task_callback = task_callback
        
        # 连接状态
        self.master_connected = False
        self.drone_connected = False
        self.last_heartbeat = datetime.now()
        
        # 消息队列
        self.send_queue = asyncio.Queue()
        self.receive_queue = asyncio.Queue()
        
        # 连接对象
        self.master_ws = None
        self.drone_socket = None
        
        # 心跳间隔（秒）
        self.heartbeat_interval = 1.0
    
    async def initialize(self):
        """初始化通信器"""
        self.logger.info(f'初始化通信器 {self.drone_id}')
        
        # 启动通信任务
        asyncio.create_task(self.connect_master())
        asyncio.create_task(self.connect_drone())
        asyncio.create_task(self.process_messages())
        asyncio.create_task(self.send_heartbeat())
    
    async def connect_master(self):
        """连接主控电脑"""
        while True:
            try:
                if not self.master_connected:
                    self.master_ws = await websockets.connect(self.master_url)
                    self.master_connected = True
                    self.logger.info('已连接到主控电脑')
                    
                    # 发送注册消息
                    await self.send_message({
                        'type': MessageType.STATUS.value,
                        'drone_id': self.drone_id,
                        'status': 'connected'
                    })
                    
                    # 启动接收消息任务
                    asyncio.create_task(self.receive_master_messages())
            except Exception as e:
                self.logger.error(f'连接主控电脑失败: {str(e)}')
                self.master_connected = False
            
            # 等待重连
            if not self.master_connected:
                await asyncio.sleep(5)
    
    async def connect_drone(self):
        """连接无人机"""
        while True:
            try:
                if not self.drone_connected:
                    # 实现无人机连接逻辑
                    self.drone_connected = True
                    self.logger.info('已连接到无人机')
                    
                    # 启动接收消息任务
                    asyncio.create_task(self.receive_drone_messages())
            except Exception as e:
                self.logger.error(f'连接无人机失败: {str(e)}')
                self.drone_connected = False
            
            # 等待重连
            if not self.drone_connected:
                await asyncio.sleep(5)
    
    async def disconnect(self):
        """断开连接"""
        try:
            if self.master_ws:
                await self.master_ws.close()
                self.master_connected = False
            
            if self.drone_socket:
                # 实现无人机断开连接逻辑
                self.drone_connected = False
            
            self.logger.info('已断开所有连接')
        except Exception as e:
            self.logger.error(f'断开连接失败: {str(e)}')
    
    async def send_message(self, message: Dict):
        """发送消息到主控电脑"""
        if not self.master_connected:
            return False
        
        try:
            await self.master_ws.send(json.dumps(message))
            return True
        except Exception as e:
            self.logger.error(f'发送消息失败: {str(e)}')
            self.master_connected = False
            return False
    
    async def send_drone_command(self, command: Dict):
        """发送命令到无人机"""
        if not self.drone_connected:
            return False
        
        try:
            # 实现无人机命令发送逻辑
            return True
        except Exception as e:
            self.logger.error(f'发送无人机命令失败: {str(e)}')
            self.drone_connected = False
            return False
    
    async def receive_master_messages(self):
        """接收主控电脑消息"""
        while True:
            try:
                if not self.master_connected:
                    break
                
                message = await self.master_ws.recv()
                data = json.loads(message)
                await self.receive_queue.put(data)
            except Exception as e:
                self.logger.error(f'接收主控电脑消息失败: {str(e)}')
                self.master_connected = False
                break
    
    async def receive_drone_messages(self):
        """接收无人机消息"""
        while True:
            try:
                if not self.drone_connected:
                    break
                
                # 实现无人机消息接收逻辑
                # data = await self.drone_socket.recv()
                # await self.receive_queue.put(data)
                await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.error(f'接收无人机消息失败: {str(e)}')
                self.drone_connected = False
                break
    
    async def process_messages(self):
        """处理消息队列"""
        while True:
            try:
                message = await self.receive_queue.get()
                message_type = message.get('type')
                
                if message_type == MessageType.HEARTBEAT.value:
                    self.last_heartbeat = datetime.now()
                elif message_type in self.message_handlers:
                    await self.message_handlers[message_type](message)
                
                self.receive_queue.task_done()
            except Exception as e:
                self.logger.error(f'处理消息失败: {str(e)}')
            
            await asyncio.sleep(0.1)
    
    async def handle_task_message(self, message: Dict):
        """处理任务消息"""
        try:
            if 'waypoints' in message:
                # 解析路径航点
                waypoints = message['waypoints']
                if self.task_callback:
                    await self.task_callback({
                        'type': 'set_path',
                        'waypoints': waypoints
                    })
                self.logger.info(f'收到新路径，共{len(waypoints)}个航点')
        except Exception as e:
            self.logger.error(f'处理任务消息失败: {str(e)}')
    
    async def handle_command_message(self, message: Dict):
        """处理命令消息"""
        try:
            if self.command_callback:
                await self.command_callback(message)
            self.logger.info(f'收到命令消息: {message}')
        except Exception as e:
            self.logger.error(f'处理命令消息失败: {str(e)}')
    
    async def handle_status_message(self, message: Dict):
        """处理状态消息"""
        try:
            if self.status_callback:
                await self.status_callback(message)
            self.logger.info(f'收到状态消息: {message}')
        except Exception as e:
            self.logger.error(f'处理状态消息失败: {str(e)}')
    
    async def send_heartbeat(self):
        """发送心跳消息"""
        while True:
            try:
                if self.master_connected:
                    await self.send_message({
                        'type': MessageType.HEARTBEAT.value,
                        'drone_id': self.drone_id,
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                self.logger.error(f'发送心跳消息失败: {str(e)}')
            
            await asyncio.sleep(self.heartbeat_interval)
    
    async def send_status(self, status: Dict):
        """发送状态信息"""
        message = {
            'type': MessageType.STATUS.value,
            'drone_id': self.drone_id,
            'timestamp': datetime.now().isoformat(),
            'data': status
        }
        return await self.send_message(message)
    
    async def send_telemetry(self, telemetry: Dict):
        """发送遥测数据"""
        message = {
            'type': MessageType.TELEMETRY.value,
            'drone_id': self.drone_id,
            'timestamp': datetime.now().isoformat(),
            'data': telemetry
        }
        return await self.send_message(message)
    
    async def send_log(self, level: str, text: str):
        """发送日志消息"""
        message = {
            'type': MessageType.LOG.value,
            'drone_id': self.drone_id,
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'text': text
        }
        return await self.send_message(message)
    
    async def send_error(self, error: str):
        """发送错误消息"""
        message = {
            'type': MessageType.ERROR.value,
            'drone_id': self.drone_id,
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
        return await self.send_message(message)