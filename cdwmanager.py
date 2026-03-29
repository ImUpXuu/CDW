#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
倒计时壁纸管理器
功能：配置管理、定时任务设置、开机自启
作者：UpXuu
GitHub: https://github.com/ImUpXuu
"""

import sys
import os
import json
import subprocess
import winreg
from pathlib import Path
from datetime import datetime

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                  QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                                  QCheckBox, QTableWidget, QTableWidgetItem,
                                  QMessageBox, QGroupBox, QFormLayout, QTabWidget)
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
except ImportError:
    print("错误：需要安装 PyQt5")
    print("运行：pip install PyQt5")
    sys.exit(1)

# 配置文件路径
def get_resource_path(filename):
    """获取资源文件路径（兼容打包后的环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        return Path(sys.executable).parent / filename
    else:
        # 开发环境
        return Path(__file__).parent / filename

CONFIG_FILE = get_resource_path("cdw.json")
WALLPAPER_EXE = get_resource_path("CountdownWallpaper.exe")
WALLPAPER_SCRIPT = get_resource_path("CountdownWallpaper.py")

# 默认配置
DEFAULT_CONFIG = {
    "countdowns": [
        {
            "name": "地生会考",
            "date": "2026-06-23",
            "enabled": True
        }
    ],
    "wallpaper": {
        "update_time": "07:40",
        "auto_start": True,  # 默认开启开机自启
        "font_path": "font.ttf",
        "theme": "blue"
    },
    "hitokoto": {
        "enabled": True,
        "types": ["i"]  # 只使用诗词类型
    }
}


def load_config():
    """加载配置文件"""
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def register_auto_start(enable=True):
    """注册开机自启（通过注册表）"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key_name = "CountdownWallpaper"
        
        if enable:
            # 添加开机自启 - 启动主程序
            if getattr(sys, 'frozen', False):
                # 打包后的环境
                exe_path = str(Path(sys.executable).absolute())
            else:
                # 开发环境 - 启动主程序 exe
                exe_path = str(get_resource_path("CountdownWallpaper.exe").absolute())
            
            command = f'"{exe_path}"'
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)
            print(f"✓ 开机自启已启用：{command}")
            return True
        else:
            # 移除开机自启
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, key_name)
                winreg.CloseKey(key)
                print("✓ 开机自启已禁用")
                return True
            except FileNotFoundError:
                return True
    except Exception as e:
        print(f"✗ 注册表操作失败：{e}")
        return False





class CountdownManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('倒计时壁纸管理器 v2.1.6')
        self.setGeometry(100, 100, 600, 500)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # 标题
        title = QLabel('倒计时壁纸管理器')
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 倒计时列表
        self.countdown_table = QTableWidget()
        self.countdown_table.setColumnCount(3)
        self.countdown_table.setHorizontalHeaderLabels(['名称', '日期', '启用'])
        self.countdown_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.countdown_table)
        
        # 倒计时按钮
        btn_layout = QHBoxLayout()
        add_btn = QPushButton('添加倒计时')
        add_btn.clicked.connect(self.add_countdown)
        del_btn = QPushButton('删除选中')
        del_btn.clicked.connect(self.delete_countdown)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)
        
        # 设置组
        settings_group = QGroupBox('设置')
        settings_layout = QFormLayout()
        
        self.update_time_edit = QLineEdit()
        self.update_time_edit.setPlaceholderText('HH:MM (24 小时制)')
        settings_layout.addRow('更新时间:', self.update_time_edit)
        
        self.auto_start_check = QCheckBox('开机自启（注册表）')
        settings_layout.addRow(self.auto_start_check)
        
        self.hitokoto_check = QCheckBox('启用一言 API')
        settings_layout.addRow(self.hitokoto_check)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        save_btn = QPushButton('保存配置')
        save_btn.clicked.connect(self.save_config_handler)
        save_btn.setStyleSheet('padding: 10px; font-size: 14px; background-color: #4CAF50; color: white;')
        
        run_btn = QPushButton('立即生成壁纸')
        run_btn.clicked.connect(self.run_wallpaper)
        run_btn.setStyleSheet('padding: 10px; font-size: 14px; background-color: #2196F3; color: white;')
        
        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(run_btn)
        layout.addLayout(bottom_layout)
        
        self.load_data_to_ui()
        
    def load_data_to_ui(self):
        """加载数据到 UI"""
        # 加载倒计时
        self.countdown_table.setRowCount(0)
        for countdown in self.config.get('countdowns', []):
            row = self.countdown_table.rowCount()
            self.countdown_table.insertRow(row)
            
            name_item = QTableWidgetItem(countdown.get('name', ''))
            self.countdown_table.setItem(row, 0, name_item)
            
            date_item = QTableWidgetItem(countdown.get('date', ''))
            self.countdown_table.setItem(row, 1, date_item)
            
            check_item = QTableWidgetItem('✓' if countdown.get('enabled', True) else '')
            check_item.setFlags(check_item.flags() & ~Qt.ItemIsEditable)
            check_item.setTextAlignment(Qt.AlignCenter)
            self.countdown_table.setItem(row, 2, check_item)
        
        # 加载设置
        wallpaper = self.config.get('wallpaper', {})
        self.update_time_edit.setText(wallpaper.get('update_time', '07:40'))
        self.auto_start_check.setChecked(wallpaper.get('auto_start', False))
        
        hitokoto = self.config.get('hitokoto', {})
        self.hitokoto_check.setChecked(hitokoto.get('enabled', True))
    
    def add_countdown(self):
        """添加倒计时"""
        row = self.countdown_table.rowCount()
        self.countdown_table.insertRow(row)
        
        name_item = QTableWidgetItem('新倒计时')
        self.countdown_table.setItem(row, 0, name_item)
        
        date_item = QTableWidgetItem(datetime.now().strftime('%Y-%m-%d'))
        self.countdown_table.setItem(row, 1, date_item)
        
        check_item = QTableWidgetItem('✓')
        check_item.setFlags(check_item.flags() & ~Qt.ItemIsEditable)
        check_item.setTextAlignment(Qt.AlignCenter)
        self.countdown_table.setItem(row, 2, check_item)
    
    def delete_countdown(self):
        """删除选中的倒计时"""
        current_row = self.countdown_table.currentRow()
        if current_row >= 0:
            self.countdown_table.removeRow(current_row)
        else:
            QMessageBox.warning(self, '提示', '请先选择要删除的倒计时')
    
    def save_config_handler(self):
        """保存配置并启动壁纸生成"""
        # 保存倒计时
        countdowns = []
        for row in range(self.countdown_table.rowCount()):
            name = self.countdown_table.item(row, 0).text()
            date = self.countdown_table.item(row, 1).text()
            enabled = self.countdown_table.item(row, 2).text() == '✓'
            countdowns.append({
                'name': name,
                'date': date,
                'enabled': enabled
            })
        
        self.config['countdowns'] = countdowns
        
        # 保存壁纸设置
        self.config['wallpaper'] = {
            'update_time': self.update_time_edit.text(),
            'auto_start': self.auto_start_check.isChecked(),  # 保存用户选择
            'font_path': 'font.ttf',
            'theme': 'blue'
        }
        
        # 保存一言设置
        self.config['hitokoto'] = {
            'enabled': self.hitokoto_check.isChecked(),
            'types': ['i']  # 只使用诗词
        }
        
        # 保存配置文件
        save_config(self.config)
        

        
        QMessageBox.information(self, '保存成功', '配置已保存！\n即将启动壁纸生成器...')
        
        # 启动壁纸生成器（优先使用 exe）
        try:
            if WALLPAPER_EXE.exists():
                subprocess.Popen([str(WALLPAPER_EXE)])
                print("已启动 CountdownWallpaper.exe")
            else:
                subprocess.Popen([sys.executable, str(WALLPAPER_SCRIPT)])
                print("已启动 CountdownWallpaper.py")
        except Exception as e:
            print(f"启动壁纸生成器失败：{e}")
        
        # 关闭管理器并删除自己（一次性使用）
        self.close()
        try:
            import os
            if getattr(sys, 'frozen', False):
                # 打包后的 exe，删除自己
                exe_path = sys.executable
                print(f"管理器配置完成，将删除自身：{exe_path}")
                # 使用命令行延迟删除
                subprocess.Popen(f'timeout /t 2 /nobreak >nul & del \"{exe_path}\"', shell=True)
        except Exception as e:
            print(f"删除管理器失败：{e}")
    
    def run_wallpaper(self):
        """立即运行壁纸生成"""
        try:
            subprocess.Popen([sys.executable, str(WALLPAPER_SCRIPT)])
            QMessageBox.information(self, '提示', '壁纸生成程序已启动！')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'启动失败：{e}')


def main():
    """主函数"""
    # 检查配置文件
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
    
    app = QApplication(sys.argv)
    manager = CountdownManager()
    manager.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
