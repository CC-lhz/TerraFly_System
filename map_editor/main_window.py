from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QStatusBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QIcon

from editor import MapEditor
from tools import ToolPanel, PropertyEditor
from converter import MapConverter

class MapEditorWindow(QMainWindow):
    """地图编辑器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings('TerraFly', 'MapEditor')
        self._init_ui()
        self._init_actions()
        self._init_menubar()
        self._init_toolbar()
        self._init_statusbar()
        self._load_settings()
    
    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('TerraFly 地图编辑器')
        self.setMinimumSize(1200, 800)
        
        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        layout = QHBoxLayout(main_widget)
        
        # 工具面板
        self.tool_panel = ToolPanel()
        self.tool_panel.tool_changed.connect(self._on_tool_changed)
        layout.addWidget(self.tool_panel)
        
        # 编辑器
        self.editor = MapEditor()
        self.editor.signals.map_updated.connect(self._on_map_updated)
        self.editor.signals.object_selected.connect(self._on_object_selected)
        self.editor.signals.error_occurred.connect(self._on_error)
        self.editor.signals.status_changed.connect(self._on_status_changed)
        layout.addWidget(self.editor)
        
        # 属性编辑器
        self.property_editor = PropertyEditor()
        self.property_editor.property_changed.connect(self._on_property_changed)
        layout.addWidget(self.property_editor)
        
        # 设置布局比例
        layout.setStretch(0, 1)  # 工具面板
        layout.setStretch(1, 4)  # 编辑器
        layout.setStretch(2, 1)  # 属性编辑器
    
    def _init_actions(self):
        """初始化动作"""
        # 文件操作
        self.new_action = QAction('新建', self)
        self.new_action.setShortcut('Ctrl+N')
        self.new_action.triggered.connect(self._on_new)
        
        self.open_action = QAction('打开', self)
        self.open_action.setShortcut('Ctrl+O')
        self.open_action.triggered.connect(self._on_open)
        
        self.save_action = QAction('保存', self)
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.triggered.connect(self._on_save)
        
        self.save_as_action = QAction('另存为', self)
        self.save_as_action.setShortcut('Ctrl+Shift+S')
        self.save_as_action.triggered.connect(self._on_save_as)
        
        # 编辑操作
        self.undo_action = QAction('撤销', self)
        self.undo_action.setShortcut('Ctrl+Z')
        self.undo_action.triggered.connect(self._on_undo)
        
        self.redo_action = QAction('重做', self)
        self.redo_action.setShortcut('Ctrl+Y')
        self.redo_action.triggered.connect(self._on_redo)
        
        # 视图操作
        self.zoom_in_action = QAction('放大', self)
        self.zoom_in_action.setShortcut('Ctrl++')
        self.zoom_in_action.triggered.connect(self._on_zoom_in)
        
        self.zoom_out_action = QAction('缩小', self)
        self.zoom_out_action.setShortcut('Ctrl+-')
        self.zoom_out_action.triggered.connect(self._on_zoom_out)
        
        self.fit_view_action = QAction('适应视图', self)
        self.fit_view_action.setShortcut('Ctrl+0')
        self.fit_view_action.triggered.connect(self._on_fit_view)
    
    def _init_menubar(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        view_menu.addAction(self.fit_view_action)
    
    def _init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar()
        toolbar.setObjectName('mainToolBar')
        self.addToolBar(toolbar)
        
        # 添加动作
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.save_as_action)
        toolbar.addSeparator()
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        toolbar.addAction(self.zoom_in_action)
        toolbar.addAction(self.zoom_out_action)
        toolbar.addAction(self.fit_view_action)
    
    def _init_statusbar(self):
        """初始化状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
    
    def _load_settings(self):
        """加载设置"""
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.value('windowState')
        if state:
            self.restoreState(state)
    
    def _save_settings(self):
        """保存设置"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self._save_settings()
        super().closeEvent(event)
    
    def _on_new(self):
        """新建地图"""
        if self._check_save_changes():
            self.editor.map_data.objects.clear()
            self.editor.update()
            self.current_file = None
    
    def _on_open(self):
        """打开地图"""
        if not self._check_save_changes():
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '打开地图',
            '',
            'TerraFly 地图文件 (*.tfmap);;所有文件 (*)'
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                self.editor.load_map_data(data)
                self.current_file = file_path
            except Exception as e:
                QMessageBox.critical(self, '错误', f'打开文件失败：{str(e)}')
    
    def _on_save(self):
        """保存地图"""
        if not self.current_file:
            return self._on_save_as()
        
        try:
            data = self.editor.save_map_data()
            if data:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(data)
                return True
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存文件失败：{str(e)}')
        return False
    
    def _on_save_as(self):
        """另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '保存地图',
            '',
            'TerraFly 地图文件 (*.tfmap);;所有文件 (*)'
        )
        
        if file_path:
            self.current_file = file_path
            return self._on_save()
        return False
    
    def _check_save_changes(self) -> bool:
        """检查是否需要保存更改"""
        # TODO: 实现更改检测逻辑
        return True
    
    def _on_undo(self):
        """撤销操作"""
        # TODO: 实现撤销功能
        pass
    
    def _on_redo(self):
        """重做操作"""
        # TODO: 实现重做功能
        pass
    
    def _on_zoom_in(self):
        """放大视图"""
        self.editor.zoom_level *= 1.2
        self.editor.update()
    
    def _on_zoom_out(self):
        """缩小视图"""
        self.editor.zoom_level /= 1.2
        self.editor.update()
    
    def _on_fit_view(self):
        """适应视图"""
        # TODO: 实现视图适应功能
        pass
    
    def _on_tool_changed(self, tool_name: str):
        """工具改变处理"""
        self.editor.set_tool(tool_name)
    
    def _on_map_updated(self):
        """地图更新处理"""
        self.editor.update()
    
    def _on_object_selected(self, obj_data):
        """对象选择处理"""
        self.property_editor.set_object(obj_data)
    
    def _on_property_changed(self, name: str, value):
        """属性改变处理"""
        # TODO: 实现属性更新功能
        pass
    
    def _on_error(self, message: str):
        """错误处理"""
        QMessageBox.critical(self, '错误', message)
    
    def _on_status_changed(self, status: str):
        """状态改变处理"""
        self.statusbar.showMessage(status)