from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QFormLayout, QDialog, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from ..unified_scheduler import Vehicle
import config

class AddVehicleDialog(QDialog):
    """添加车辆对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('添加新车辆')
        layout = QFormLayout(self)
        
        # 车辆ID
        self.id_input = QComboBox()
        self.id_input.setEditable(True)
        self.id_input.addItems([f'drone{i}' for i in range(1, 6)])
        self.id_input.addItems([f'car{i}' for i in range(1, 6)])
        layout.addRow('车辆ID:', self.id_input)
        
        # 车辆类型
        self.type_combo = QComboBox()
        self.type_combo.addItems(['drone', 'car'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addRow('车辆类型:', self.type_combo)
        
        # 位置
        self.lat_input = QDoubleSpinBox()
        self.lat_input.setRange(-90, 90)
        self.lat_input.setDecimals(6)
        self.lat_input.setValue(config.config['map']['center_lat'])
        layout.addRow('纬度:', self.lat_input)
        
        self.lon_input = QDoubleSpinBox()
        self.lon_input.setRange(-180, 180)
        self.lon_input.setDecimals(6)
        self.lon_input.setValue(config.config['map']['center_lon'])
        layout.addRow('经度:', self.lon_input)
        
        # 电量
        self.battery_input = QSpinBox()
        self.battery_input.setRange(0, 100)
        self.battery_input.setValue(100)
        layout.addRow('电量(%):', self.battery_input)
        
        # 最大载重
        self.max_payload_input = QDoubleSpinBox()
        self.max_payload_input.setRange(0, 1000)
        self.max_payload_input.setValue(config.config['vehicle']['drone']['max_payload'])
        layout.addRow('最大载重(kg):', self.max_payload_input)
        
        # 能力
        self.capabilities = []
        self.update_capabilities()
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton('确定')
        cancel_button = QPushButton('取消')
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
    
    def on_type_changed(self, vehicle_type):
        """车辆类型改变时更新相关设置"""
        if vehicle_type == 'drone':
            self.max_payload_input.setValue(config.config['vehicle']['drone']['max_payload'])
            self.update_capabilities(['aerial_delivery'])
        else:
            self.max_payload_input.setValue(config.config['vehicle']['car']['max_payload'])
            self.update_capabilities(['ground_delivery', 'first_mile', 'last_mile'])
    
    def update_capabilities(self, capabilities=None):
        """更新车辆能力"""
        self.capabilities = capabilities or []
    
    def get_vehicle_data(self):
        """获取输入的车辆数据"""
        return {
            'id': self.id_input.currentText(),
            'type': self.type_combo.currentText(),
            'location': (self.lat_input.value(), self.lon_input.value()),
            'status': 'idle',
            'battery_level': self.battery_input.value(),
            'max_payload': self.max_payload_input.value(),
            'current_payload': 0,
            'capabilities': self.capabilities
        }

class VehicleManagerWidget(QWidget):
    """车辆管理界面"""
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
        
        add_button = QPushButton('添加车辆')
        add_button.clicked.connect(self.add_vehicle)
        toolbar.addWidget(add_button)
        
        remove_button = QPushButton('移除车辆')
        remove_button.clicked.connect(self.remove_vehicle)
        toolbar.addWidget(remove_button)
        
        refresh_button = QPushButton('刷新')
        refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_button)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 车辆列表
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'ID', '类型', '状态', '电量', '位置',
            '最大载重', '当前载重', '能力'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
        # 初始刷新
        self.refresh()
    
    def refresh(self):
        """刷新车辆列表"""
        if not self.main_window.scheduler:
            return
        
        status = self.main_window.scheduler.get_system_status()
        vehicles = status['vehicles']
        
        self.table.setRowCount(len(vehicles))
        for i, vehicle in enumerate(vehicles):
            self.table.setItem(i, 0, QTableWidgetItem(vehicle['id']))
            self.table.setItem(i, 1, QTableWidgetItem(vehicle['type']))
            self.table.setItem(i, 2, QTableWidgetItem(vehicle['status']))
            self.table.setItem(i, 3, QTableWidgetItem(f"{vehicle['battery_level']}%"))
            self.table.setItem(i, 4, QTableWidgetItem(
                f"({vehicle['location'][0]:.4f}, {vehicle['location'][1]:.4f})"
            ))
            self.table.setItem(i, 5, QTableWidgetItem(f"{vehicle['max_payload']}kg"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{vehicle['current_payload']}kg"))
            self.table.setItem(i, 7, QTableWidgetItem(
                ', '.join(vehicle['capabilities'])
            ))
    
    def add_vehicle(self):
        """添加新车辆"""
        dialog = AddVehicleDialog(self)
        if dialog.exec():
            try:
                vehicle_data = dialog.get_vehicle_data()
                vehicle = Vehicle(**vehicle_data)
                self.main_window.scheduler.register_vehicle(vehicle)
                self.refresh()
                QMessageBox.information(self, '成功', f'已添加车辆: {vehicle.id}')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'添加车辆失败: {str(e)}')
    
    def remove_vehicle(self):
        """移除选中的车辆"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', '请先选择要移除的车辆')
            return
        
        vehicle_id = self.table.item(selected_items[0].row(), 0).text()
        reply = QMessageBox.question(
            self, '确认',
            f'是否要移除车辆 {vehicle_id}？\n注意：如果车辆正在执行任务，移除可能会导致任务失败。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.main_window.scheduler.unregister_vehicle(vehicle_id)
                self.refresh()
                QMessageBox.information(self, '成功', f'已移除车辆: {vehicle_id}')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'移除车辆失败: {str(e)}')