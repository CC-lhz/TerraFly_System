from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QFormLayout, QDialog, QMessageBox, QHeaderView, QDateTimeEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from ..unified_scheduler import Task, Priority
import config

class AddTaskDialog(QDialog):
    """添加任务对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent.main_window
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('添加新任务')
        layout = QFormLayout(self)
        
        # 任务ID
        self.id_input = QComboBox()
        self.id_input.setEditable(True)
        self.id_input.addItems([f'task{i}' for i in range(1, 11)])
        layout.addRow('任务ID:', self.id_input)
        
        # 取件点
        self.pickup_combo = QComboBox()
        self.delivery_combo = QComboBox()
        self.update_delivery_points()
        layout.addRow('取件点:', self.pickup_combo)
        layout.addRow('送件点:', self.delivery_combo)
        
        # 重量
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 1000)
        self.weight_input.setValue(1.0)
        layout.addRow('重量(kg):', self.weight_input)
        
        # 优先级
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([p.name for p in Priority])
        layout.addRow('优先级:', self.priority_combo)
        
        # 截止时间
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.deadline_input.setCalendarPopup(True)
        layout.addRow('截止时间:', self.deadline_input)
        
        # 所需能力
        self.capabilities_combo = QComboBox()
        self.capabilities_combo.addItems([
            'ground_delivery',
            'aerial_delivery',
            'ground_delivery,aerial_delivery'
        ])
        layout.addRow('所需能力:', self.capabilities_combo)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton('确定')
        cancel_button = QPushButton('取消')
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
    
    def update_delivery_points(self):
        """更新取件点和送件点列表"""
        if not self.main_window.scheduler:
            return
        
        status = self.main_window.scheduler.get_system_status()
        points = status['delivery_points']
        
        self.pickup_combo.clear()
        self.delivery_combo.clear()
        
        for point in points:
            if point['type'] in ['pickup', 'drone_station']:
                self.pickup_combo.addItem(point['id'])
            if point['type'] in ['delivery', 'drone_station']:
                self.delivery_combo.addItem(point['id'])
    
    def get_task_data(self):
        """获取输入的任务数据"""
        return {
            'id': self.id_input.currentText(),
            'pickup_point': self.pickup_combo.currentText(),
            'delivery_point': self.delivery_combo.currentText(),
            'weight': self.weight_input.value(),
            'priority': Priority[self.priority_combo.currentText()],
            'deadline': self.deadline_input.dateTime().toPyDateTime(),
            'required_capabilities': self.capabilities_combo.currentText().split(',')
        }

class TaskManagerWidget(QWidget):
    """任务管理界面"""
    refresh_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()
        self.refresh_signal.connect(self.refresh)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        add_button = QPushButton('添加任务')
        add_button.clicked.connect(self.add_task)
        toolbar.addWidget(add_button)
        
        cancel_button = QPushButton('取消任务')
        cancel_button.clicked.connect(self.cancel_task)
        toolbar.addWidget(cancel_button)
        
        refresh_button = QPushButton('刷新')
        refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_button)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 任务列表
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'ID', '取件点', '送件点', '重量', '优先级',
            '状态', '分配车辆', '截止时间', '所需能力'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
        # 初始刷新
        self.refresh()
    
    def refresh(self):
        """刷新任务列表"""
        if not self.main_window.scheduler:
            return
        
        status = self.main_window.scheduler.get_system_status()
        tasks = status['tasks']
        
        self.table.setRowCount(len(tasks))
        for i, task in enumerate(tasks):
            self.table.setItem(i, 0, QTableWidgetItem(task['id']))
            self.table.setItem(i, 1, QTableWidgetItem(task['pickup_point']))
            self.table.setItem(i, 2, QTableWidgetItem(task['delivery_point']))
            self.table.setItem(i, 3, QTableWidgetItem(f"{task['weight']}kg"))
            self.table.setItem(i, 4, QTableWidgetItem(task['priority']))
            self.table.setItem(i, 5, QTableWidgetItem(task['status']))
            self.table.setItem(i, 6, QTableWidgetItem(task.get('assigned_to', '-')))
            self.table.setItem(i, 7, QTableWidgetItem(
                task['deadline'].strftime('%Y-%m-%d %H:%M:%S') if task['deadline'] else '-'
            ))
            self.table.setItem(i, 8, QTableWidgetItem(
                ', '.join(task['required_capabilities'])
            ))
    
    def add_task(self):
        """添加新任务"""
        dialog = AddTaskDialog(self)
        if dialog.exec():
            try:
                task_data = dialog.get_task_data()
                task = Task(**task_data)
                self.main_window.scheduler.add_task(task)
                self.refresh()
                QMessageBox.information(self, '成功', f'已添加任务: {task.id}')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'添加任务失败: {str(e)}')
    
    def cancel_task(self):
        """取消选中的任务"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', '请先选择要取消的任务')
            return
        
        task_id = self.table.item(selected_items[0].row(), 0).text()
        task_status = self.table.item(selected_items[0].row(), 5).text()
        
        if task_status == 'completed':
            QMessageBox.warning(self, '警告', '该任务已完成，无法取消')
            return
        
        reply = QMessageBox.question(
            self, '确认',
            f'是否要取消任务 {task_id}？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.main_window.scheduler.cancel_task(task_id)
                self.refresh()
                QMessageBox.information(self, '成功', f'已取消任务: {task_id}')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'取消任务失败: {str(e)}')