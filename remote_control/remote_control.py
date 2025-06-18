import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
from mavsdk import System
import config

class RemoteControlGUI:
    """
    图形界面遥控器：用于发送无人机和地面车控制命令，以及切换模式。
    """
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(config.GUI_TITLE)
        
        # 初始化无人机控制对象
        self.drone = System()
        
        # 连接按钮
        self.btn_connect = ttk.Button(self.root, text="连接无人机", command=self.connect_drone)
        self.btn_connect.pack(pady=5)
        # 起飞按钮
        self.btn_takeoff = ttk.Button(self.root, text="起飞", command=self.takeoff)
        self.btn_takeoff.pack(pady=5)
        # 降落按钮
        self.btn_land = ttk.Button(self.root, text="降落", command=self.land)
        self.btn_land.pack(pady=5)
        # 模式切换（自动/手动）
        self.btn_mode = ttk.Button(self.root, text="切换模式", command=self.switch_mode)
        self.btn_mode.pack(pady=5)
        
        # 模式显示
        self.mode = tk.StringVar(value="AUTO")
        self.label_mode = ttk.Label(self.root, textvariable=self.mode)
        self.label_mode.pack(pady=5)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def connect_drone(self):
        """连接到无人机遥控"""
        try:
            asyncio.run(self._connect_drone_async())
            messagebox.showinfo("信息", "无人机已连接")
        except Exception as e:
            messagebox.showerror("错误", f"连接失败: {e}")

    async def _connect_drone_async(self):
        print("连接到无人机...")
        await self.drone.connect(system_address=config.DRONE_URI)
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print("无人机连接成功")
                break

    def takeoff(self):
        """遥控无人机起飞"""
        async def do_takeoff():
            await self.drone.action.arm()
            await self.drone.action.takeoff()
        try:
            asyncio.run(do_takeoff())
            messagebox.showinfo("信息", "无人机起飞命令已发送")
        except Exception as e:
            messagebox.showerror("错误", f"起飞失败: {e}")

    def land(self):
        """遥控无人机降落"""
        async def do_land():
            await self.drone.action.land()
        try:
            asyncio.run(do_land())
            messagebox.showinfo("信息", "无人机降落命令已发送")
        except Exception as e:
            messagebox.showerror("错误", f"降落失败: {e}")

    def switch_mode(self):
        """切换无人机控制模式（示例：自动<->手动）"""
        current = self.mode.get()
        if current == "AUTO":
            self.mode.set("MANUAL")
            print("切换到手动模式")
        else:
            self.mode.set("AUTO")
            print("切换到自动模式")

    def on_close(self):
        """关闭 GUI"""
        if messagebox.askokcancel("退出", "确认退出程序？"):
            self.root.destroy()

if __name__ == "__main__":
    RemoteControlGUI()
