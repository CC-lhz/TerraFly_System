from typing import Dict, List, Optional
from datetime import datetime
import logging
from enum import Enum

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    URGENT = 3

class TaskStatus(Enum):
    """任务状态"""
    PENDING = 'pending'
    ASSIGNED = 'assigned'
    PICKUP = 'pickup'
    DELIVERING = 'delivering'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class Task:
    """任务类"""
    def __init__(
        self,
        task_id: str,
        pickup_point: Dict,
        delivery_point: Dict,
        weight: float,
        priority: TaskPriority = TaskPriority.MEDIUM,
        deadline: Optional[datetime] = None,
        required_capabilities: List[str] = None
    ):
        self.id = task_id
        self.pickup_point = pickup_point
        self.delivery_point = delivery_point
        self.weight = weight
        self.priority = priority
        self.deadline = deadline
        self.required_capabilities = required_capabilities or []
        
        self.status = TaskStatus.PENDING
        self.assigned_vehicle = None
        self.assigned_time = None
        self.pickup_time = None
        self.delivery_time = None
        self.completion_time = None
        self.error_message = None
        
        self.create_time = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'pickup_point': self.pickup_point,
            'delivery_point': self.delivery_point,
            'weight': self.weight,
            'priority': self.priority.value,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'required_capabilities': self.required_capabilities,
            'status': self.status.value,
            'assigned_vehicle': self.assigned_vehicle,
            'assigned_time': self.assigned_time.isoformat() if self.assigned_time else None,
            'pickup_time': self.pickup_time.isoformat() if self.pickup_time else None,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'completion_time': self.completion_time.isoformat() if self.completion_time else None,
            'error_message': self.error_message,
            'create_time': self.create_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """从字典创建任务对象"""
        task = cls(
            task_id=data['id'],
            pickup_point=data['pickup_point'],
            delivery_point=data['delivery_point'],
            weight=data['weight'],
            priority=TaskPriority(data['priority']),
            deadline=datetime.fromisoformat(data['deadline']) if data['deadline'] else None,
            required_capabilities=data['required_capabilities']
        )
        
        task.status = TaskStatus(data['status'])
        task.assigned_vehicle = data['assigned_vehicle']
        task.assigned_time = datetime.fromisoformat(data['assigned_time']) if data['assigned_time'] else None
        task.pickup_time = datetime.fromisoformat(data['pickup_time']) if data['pickup_time'] else None
        task.delivery_time = datetime.fromisoformat(data['delivery_time']) if data['delivery_time'] else None
        task.completion_time = datetime.fromisoformat(data['completion_time']) if data['completion_time'] else None
        task.error_message = data['error_message']
        task.create_time = datetime.fromisoformat(data['create_time'])
        
        return task

class TaskManager:
    """任务管理器"""
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.logger = logging.getLogger('TaskManager')
    
    async def initialize(self):
        """初始化任务管理器"""
        self.logger.info('任务管理器初始化')
    
    def create_task(
        self,
        pickup_point: Dict,
        delivery_point: Dict,
        weight: float,
        priority: TaskPriority = TaskPriority.MEDIUM,
        deadline: Optional[datetime] = None,
        required_capabilities: List[str] = None
    ) -> Task:
        """创建新任务"""
        # 生成任务ID
        task_id = f'TASK_{len(self.tasks) + 1}'
        
        # 创建任务对象
        task = Task(
            task_id=task_id,
            pickup_point=pickup_point,
            delivery_point=delivery_point,
            weight=weight,
            priority=priority,
            deadline=deadline,
            required_capabilities=required_capabilities
        )
        
        # 添加到任务列表
        self.tasks[task_id] = task
        
        self.logger.info(f'创建新任务: {task_id}')
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取指定任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def get_pending_tasks(self) -> List[Task]:
        """获取待分配的任务"""
        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
        ]
    
    def get_active_tasks(self) -> List[Task]:
        """获取活动任务"""
        return [
            task for task in self.tasks.values()
            if task.status in [
                TaskStatus.ASSIGNED,
                TaskStatus.PICKUP,
                TaskStatus.DELIVERING
            ]
        ]
    
    def get_completed_tasks(self) -> List[Task]:
        """获取已完成的任务"""
        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.COMPLETED
        ]
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """更新任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.status = status
        
        # 更新相关时间戳
        now = datetime.now()
        if status == TaskStatus.PICKUP:
            task.pickup_time = now
        elif status == TaskStatus.COMPLETED:
            task.completion_time = now
        elif status == TaskStatus.FAILED:
            task.error_message = error_message
        
        self.logger.info(f'更新任务 {task_id} 状态: {status.value}')
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task or task.status == TaskStatus.COMPLETED:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completion_time = datetime.now()
        
        self.logger.info(f'取消任务: {task_id}')
        return True
    
    def remove_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.logger.info(f'删除任务: {task_id}')
            return True
        return False
    
    def serialize(self) -> Dict:
        """序列化任务数据"""
        return {
            task_id: task.to_dict()
            for task_id, task in self.tasks.items()
        }
    
    def deserialize(self, data: Dict):
        """反序列化任务数据"""
        self.tasks = {
            task_id: Task.from_dict(task_data)
            for task_id, task_data in data.items()
        }