from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Optional

class MapEditorSignals(QObject):
    """地图编辑器信号类"""
    
    # 地图更新信号
    map_updated = pyqtSignal()  # 当地图数据发生变化时触发
    
    # 对象选择信号
    object_selected = pyqtSignal(object)  # 当选择地图对象时触发，传递对象数据字典或None（取消选择）
    
    # 错误信号
    error_occurred = pyqtSignal(str)  # 当发生错误时触发，传递错误信息
    
    # 状态信号
    status_changed = pyqtSignal(str)  # 当编辑器状态改变时触发，传递状态信息
    
    # 工具信号
    tool_changed = pyqtSignal(str)  # 当切换编辑工具时触发，传递工具名称
    
    # 视图信号
    view_changed = pyqtSignal(dict)  # 当视图参数（如缩放、中心点）改变时触发
    
    # 保存信号
    save_requested = pyqtSignal()  # 当请求保存地图数据时触发
    save_completed = pyqtSignal(bool)  # 当保存操作完成时触发，传递是否成功
    
    # 加载信号
    load_requested = pyqtSignal()  # 当请求加载地图数据时触发
    load_completed = pyqtSignal(bool)  # 当加载操作完成时触发，传递是否成功
    
    # 撤销/重做信号
    undo_available = pyqtSignal(bool)  # 当撤销状态改变时触发
    redo_available = pyqtSignal(bool)  # 当重做状态改变时触发
    
    # 网格信号
    grid_changed = pyqtSignal(dict)  # 当网格参数改变时触发
    
    # 图层信号
    layer_visibility_changed = pyqtSignal(str, bool)  # 当图层可见性改变时触发
    layer_opacity_changed = pyqtSignal(str, float)  # 当图层透明度改变时触发
    
    def __init__(self):
        super().__init__()