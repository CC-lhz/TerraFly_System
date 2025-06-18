import time
import serial
import config

class GroundControl:
    """
    地面车避障控制程序。
    通过串口与Arduino通信，发送速度命令并读取传感器数据进行避障。
    """
    def __init__(self):
        # 初始化串口连接
        self.ser = serial.Serial(config.SERIAL_PORT, config.BAUDRATE, timeout=1)
        time.sleep(2)  # 等待串口稳定
        print(f"连接到 Arduino 串口: {config.SERIAL_PORT}")

    def set_speed(self, left_speed, right_speed):
        """
        设置左右电机速度。
        参数速度范围 0~255，正值前进，负值后退。
        """
        cmd = f"{left_speed},{right_speed}\n"
        self.ser.write(cmd.encode())

    def stop(self):
        """停止地面车"""
        self.set_speed(0, 0)

    def avoid_obstacle(self):
        """
        读取距离传感器数据并进行简单避障。
        假设Arduino会定期发送距离传感器读数，如 "DIST:xx"
        """
        if self.ser.in_waiting:
            line = self.ser.readline().decode('utf-8').strip()
            if line.startswith("DIST:"):
                try:
                    dist = float(line.split(":")[1])
                except ValueError:
                    return False
                if dist < config.SAFE_DISTANCE:
                    print("检测到障碍物，执行避障操作")
                    # 后退并转向
                    self.set_speed(-config.REVERSE_SPEED, -config.REVERSE_SPEED)
                    time.sleep(1)
                    self.set_speed(config.TURN_SPEED, -config.TURN_SPEED)
                    time.sleep(1)
                    self.stop()
                    return True
        return False

    def run(self):
        """
        地面车主循环。
        持续前进并避开障碍物。
        """
        print("地面车避障控制启动")
        try:
            while True:
                if not self.avoid_obstacle():
                    # 默认前进
                    self.set_speed(config.FORWARD_SPEED, config.FORWARD_SPEED)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("停止地面车控制")
            self.stop()

if __name__ == "__main__":
    gc = GroundControl()
    gc.run()
