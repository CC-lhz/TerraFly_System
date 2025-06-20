from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from typing import Optional, Dict

class ToolButton(QPushButton):
    """工具按钮类"""
    def __init__(self, name: str, icon_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(32, 32)
        self.setToolTip(name)
        if icon_path:
            self.setIcon(QIcon(icon_path))

class PropertyEditor(QWidget):
    """属性编辑器类"""
    property_changed = pyqtSignal(str, object)  # 属性名，新值
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
    
    def set_object(self, obj_data: Optional[Dict]):
        """设置要编辑的对象"""
        # 清除现有控件
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)
        
        if not obj_data:
            return
        
        # 添加通用属性
        self._add_property('名称', 'name', obj_data.get('name', ''), str)
        self._add_property('描述', 'description', obj_data.get('description', ''), str)
        
        # 根据对象类型添加特定属性
        obj_type = obj_data.get('type')
        if obj_type in ['obstacle', 'building']:
            self._add_property('半径', 'radius', obj_data.get('radius', 0.0), float)
            self._add_property('高度', 'height', obj_data.get('height', 0.0), float)
    
    def _add_property(self, label: str, name: str, value: object, value_type: type):
        """添加属性编辑控件"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签
        label_widget = QLabel(label)
        label_widget.setFixedWidth(60)
        layout.addWidget(label_widget)
        
        # 编辑控件
        if value_type == str:
            editor = QLineEdit(str(value))
            editor.textChanged.connect(
                lambda text: self.property_changed.emit(name, text)
            )
        elif value_type == int:
            editor = QSpinBox()
            editor.setRange(-1000000, 1000000)
            editor.setValue(int(value))
            editor.valueChanged.connect(
                lambda val: self.property_changed.emit(name, val)
            )
        elif value_type == float:
            editor = QDoubleSpinBox()
            editor.setRange(-1000000.0, 1000000.0)
            editor.setDecimals(2)
            editor.setValue(float(value))
            editor.valueChanged.connect(
                lambda val: self.property_changed.emit(name, val)
            )
        
        layout.addWidget(editor)
        self.layout.addWidget(container)

class ToolPanel(QWidget):
    """工具面板类"""
    tool_changed = pyqtSignal(str)  # 工具名称
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tool = None
        self.tool_buttons = []
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        import os
        package_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 选择工具
        select_btn = ToolButton('选择', os.path.join(package_dir, 'icons', 'select.svg'))
        select_btn.toggled.connect(lambda checked: self._on_tool_toggled('select', select_btn, checked))
        layout.addWidget(select_btn)
        self.tool_buttons.append(select_btn)
        
        # 静态对象工具
        layout.addWidget(QLabel('静态对象'))
        for tool in ['obstacle', 'building', 'landmark', 'station']:
            btn = ToolButton(tool.capitalize(), os.path.join(package_dir, 'icons', f'{tool}.svg'))
            btn.toggled.connect(lambda checked, t=tool, b=btn: self._on_tool_toggled(t, b, checked))
            layout.addWidget(btn)
            self.tool_buttons.append(btn)
        
        # 区域工具
        layout.addWidget(QLabel('区域'))
        for tool in ['restricted', 'traffic', 'weather', 'custom']:
            btn = ToolButton(tool.capitalize(), os.path.join(package_dir, 'icons', f'{tool}.svg'))
            btn.toggled.connect(lambda checked, t=tool, b=btn: self._on_tool_toggled(t, b, checked))
            layout.addWidget(btn)
            self.tool_buttons.append(btn)
        
        # 路径工具
        layout.addWidget(QLabel('路径'))
        for tool in ['road', 'air', 'hybrid']:
            btn = ToolButton(tool.capitalize(), os.path.join(package_dir, 'icons', f'{tool}.svg'))
            btn.toggled.connect(lambda checked, t=tool, b=btn: self._on_tool_toggled(t, b, checked))
            layout.addWidget(btn)
            self.tool_buttons.append(btn)
        
        # 保存所有工具按钮的引用
        self.tool_buttons = layout.parentWidget().findChildren(ToolButton)
        
        layout.addStretch()
    
    def _on_tool_toggled(self, tool_name: str, toggled_button: ToolButton, checked: bool):
        """工具按钮状态改变处理"""
        if checked:
            # 选中新工具
            self.current_tool = tool_name
            # 取消其他按钮的选中状态
            for btn in self.tool_buttons:
                if btn != toggled_button:
                    btn.setChecked(False)
            # 发送工具改变信号
            self.tool_changed.emit(tool_name)
        elif toggled_button.isChecked() != checked:
            # 如果是取消选中当前工具，恢复选择工具
            toggled_button.setChecked(True)