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

class CarCommunicator:
    """无人车通信器"""
    def __init__(
        self,
        car_id: str,
        master_url: str,
        car_port: int,
        status_callback: Callable = None,
        command_callback: Callable = None,
        task_callback: Callable = None
    ):
        self.car_id = car_id
        self.master_url = master_url
        self.car_port = car_port
        self.logger = logging.getLogger(f'CarCommunicator_{car_id}')
        
        # 回调函数
        self.status_callback = status_callback
        self.command_callback = command_callback
        self.task_callback = task_callback
        
        # 连接状态
        self.master_connected = False
        self.car_connected = False
        self.last_heartbeat = datetime.now()
        
        # 消息队列
        self.send_queue = asyncio.Queue()
        self.receive_queue = asyncio.Queue()
        
        # 连接对象
        self.master_ws = None
        self.car_socket = None
        
        # 心跳间隔（秒）
        self.heartbeat_interval = 1.0
    
    async def initialize(self):
        """初始化通信器"""
        self.logger.info(f'初始化通信器 {self.car_id}')
        
        # 启动通信任务
        asyncio.create_task(self.connect_master())
        asyncio.create_task(self.connect_car())
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
                        'car_id': self.car_id,
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
    
    async def connect_car(self):
        """连接无人车"""
        while True:
            try:
                if not self.car_connected:
                    # 实现无人车连接逻辑
                    self.car_connected = True
                    self.logger.info('已连接到无人车')
                    
                    # 启动接收消息任务
                    asyncio.create_task(self.receive_car_messages())
            except Exception as e:
                self.logger.error(f'连接无人车失败: {str(e)}')
                self.car_connected = False
            
            # 等待重连
            if not self.car_connected:
                await asyncio.sleep(5)
    
    async def disconnect(self):
        """断开连接"""
        try:
            if self.master_ws:
                await self.master_ws.close()
                self.master_connected = False
            
            if self.car_socket:
                # 实现无人车断开连接逻辑
                self.car_connected = False
            
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
    
    async def send_car_command(self, command: Dict):
        """发送命令到无人车"""
        if not self.car_connected:
            return False
        
        try:
            # 实现无人车命令发送逻辑
            return True
        except Exception as e:
            self.logger.error(f'发送无人车命令失败: {str(e)}')
            self.car_connected = False
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
    
    async def receive_car_messages(self):
        """接收无人车消息"""
        while True:
            try:
                if not self.car_connected:
                    break
                
                # 实现无人车消息接收逻辑
                # data = await self.car_socket.recv()
                # await self.receive_queue.put(data)
                await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.error(f'接收无人车消息失败: {str(e)}')
                self.car_connected = False
                break
    
    async def process_messages(self):
        """处理消息"""
        while True:
            try:
                message = await self.receive_queue.get()
                message_type = message.get('type')
                
                if message_type == MessageType.COMMAND.value:
                    if self.command_callback:
                        await self.command_callback(message)
                    await self.send_car_command(message)
                
                elif message_type == MessageType.TASK.value:
                    if self.task_callback:
                        await self.task_callback(message)
                
                elif message_type == MessageType.STATUS.value:
                    if self.status_callback:
                        await self.status_callback(message)
                
                elif message_type == MessageType.HEARTBEAT.value:
                    self.last_heartbeat = datetime.now()
                
            except Exception as e:
                self.logger.error(f'处理消息失败: {str(e)}')
            
            await asyncio.sleep(0.01)
    
    async def send_heartbeat(self):
        """发送心跳消息"""
        while True:
            try:
                if self.master_connected:
                    await self.send_message({
                        'type': MessageType.HEARTBEAT.value,
                        'car_id': self.car_id,
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                self.logger.error(f'发送心跳消息失败: {str(e)}')
            
            await asyncio.sleep(self.heartbeat_interval)
    
    async def send_status(self, status: Dict):
        """发送状态信息"""
        message = {
            'type': MessageType.STATUS.value,
            'car_id': self.car_id,
            'timestamp': datetime.now().isoformat(),
            'data': status
        }
        return await self.send_message(message)
    
    async def send_telemetry(self, telemetry: Dict):
        """发送遥测数据"""
        message = {
            'type': MessageType.TELEMETRY.value,
            'car_id': self.car_id,
            'timestamp': datetime.now().isoformat(),
            'data': telemetry
        }
        return await self.send_message(message)
    
    async def send_log(self, level: str, text: str):
        """发送日志消息"""
        message = {
            'type': MessageType.LOG.value,
            'car_id': self.car_id,
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'text': text
        }
        return await self.send_message(message)
    
    async def send_error(self, error: str):
        """发送错误消息"""
        message = {
            'type': MessageType.ERROR.value,
            'car_id': self.car_id,
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
        return await self.send_message(message)