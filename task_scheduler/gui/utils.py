from PyQt6.QtWidgets import QMessageBox, QInputDialog, QFileDialog
from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtGui import QColor
import json
import os

def format_datetime(dt):
    """格式化日期时间"""
    return dt.toString('yyyy-MM-dd hh:mm:ss')

def format_duration(seconds):
    """格式化持续时间"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f'{hours}小时{minutes}分钟'
    elif minutes > 0:
        return f'{minutes}分钟{seconds}秒'
    else:
        return f'{seconds}秒'

def get_status_color(status):
    """获取状态对应的颜色"""
    status_colors = {
        'active': QColor(76, 175, 80),  # 绿色
        'pending': QColor(255, 152, 0),  # 橙色
        'completed': QColor(33, 150, 243),  # 蓝色
        'failed': QColor(244, 67, 54),  # 红色
        'cancelled': QColor(158, 158, 158),  # 灰色
        'idle': QColor(158, 158, 158),  # 灰色
        'charging': QColor(255, 193, 7),  # 黄色
        'low_battery': QColor(255, 87, 34),  # 深橙色
        'maintenance': QColor(156, 39, 176)  # 紫色
    }
    return status_colors.get(status.lower(), QColor(33, 33, 33))  # 默认深灰色

def show_error_dialog(parent, title, message):
    """显示错误对话框"""
    QMessageBox.critical(parent, title, message)

def show_warning_dialog(parent, title, message):
    """显示警告对话框"""
    QMessageBox.warning(parent, title, message)

def show_info_dialog(parent, title, message):
    """显示信息对话框"""
    QMessageBox.information(parent, title, message)

def show_confirmation_dialog(parent, title, message):
    """显示确认对话框"""
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    return reply == QMessageBox.StandardButton.Yes

def get_text_input(parent, title, label, default_text=''):
    """获取文本输入"""
    text, ok = QInputDialog.getText(
        parent,
        title,
        label,
        text=default_text
    )
    return (text, ok)

def get_file_save_path(parent, title, directory, filter_):
    """获取文件保存路径"""
    return QFileDialog.getSaveFileName(
        parent,
        title,
        directory,
        filter_
    )[0]

def get_file_open_path(parent, title, directory, filter_):
    """获取文件打开路径"""
    return QFileDialog.getOpenFileName(
        parent,
        title,
        directory,
        filter_
    )[0]

def save_json_file(data, file_path):
    """保存JSON文件"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f'保存JSON文件失败: {str(e)}')
        return False

def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'加载JSON文件失败: {str(e)}')
        return None

def validate_coordinates(lat, lon):
    """验证坐标是否有效"""
    try:
        lat = float(lat)
        lon = float(lon)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except:
        return False

def validate_positive_number(value):
    """验证是否为正数"""
    try:
        num = float(value)
        return num > 0
    except:
        return False

def validate_non_negative_number(value):
    """验证是否为非负数"""
    try:
        num = float(value)
        return num >= 0
    except:
        return False

def validate_integer_range(value, min_val, max_val):
    """验证整数是否在指定范围内"""
    try:
        num = int(value)
        return min_val <= num <= max_val
    except:
        return False

def format_file_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f'{size_bytes:.2f} {unit}'
        size_bytes /= 1024
    return f'{size_bytes:.2f} TB'

def format_percentage(value):
    """格式化百分比"""
    return f'{value:.1f}%'

def format_speed(value):
    """格式化速度"""
    if value >= 1000:
        return f'{value/1000:.1f} km/h'
    return f'{value:.1f} m/s'

def format_distance(meters):
    """格式化距离"""
    if meters >= 1000:
        return f'{meters/1000:.2f} km'
    return f'{meters:.0f} m'

def format_weight(grams):
    """格式化重量"""
    if grams >= 1000:
        return f'{grams/1000:.2f} kg'
    return f'{grams:.0f} g'

def format_battery(value):
    """格式化电池电量"""
    return f'{value:.0f}%'

def get_battery_status_color(percentage):
    """获取电池状态对应的颜色"""
    if percentage >= 60:
        return QColor(76, 175, 80)  # 绿色
    elif percentage >= 30:
        return QColor(255, 152, 0)  # 橙色
    else:
        return QColor(244, 67, 54)  # 红色