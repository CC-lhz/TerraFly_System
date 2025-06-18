import cv2
import asyncio
import numpy as np
from mavsdk import System
from mavsdk.offboard import (OffboardError, VelocityNedYaw)
import config

async def run():
    """
    自动对接程序：使用摄像头识别地面标志物，
    并通过无人机姿态调整完成精确对接和着陆。
    """
    print("连接到无人机进行对接任务...")
    drone = System()
    await drone.connect(system_address=config.CONNECTION_URI)
    # 等待连接
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("无人机已连接，开始对接任务")
            break

    # 启动Offboard控制
    print("开始Offboard模式")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    await drone.offboard.start()

    # 打开摄像头
    cap = cv2.VideoCapture(config.CAMERA_ID)
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    frame_center = None
    # 主循环：持续检测标志物并调整无人机位置
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            height, width = frame.shape[:2]
            if frame_center is None:
                frame_center = (width // 2, height // 2)
            # 转为灰度并检测 ArUco 标记
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = cv2.aruco.detectMarkers(
                gray, config.ARUCO_DICT, parameters=config.ARUCO_PARAMS)
            if ids is not None:
                # 使用第一个检测到的标记计算中心位置
                c = corners[0][0]
                marker_center = (int(np.mean(c[:, 0])), int(np.mean(c[:, 1])))
                error_x = marker_center[0] - frame_center[0]
                error_y = marker_center[1] - frame_center[1]
                print(f"标记中心误差: ({error_x}, {error_y})")
                # 判断是否对齐
                if abs(error_x) < config.CENTER_THRESHOLD and abs(error_y) < config.CENTER_THRESHOLD:
                    print("已对齐，准备着陆")
                    await drone.offboard.stop()
                    await drone.action.land()
                    break
                # 计算控制指令，简单比例控制
                vx = -config.P_GAIN * error_y
                vy = config.P_GAIN * error_x
                print(f"发送速度指令: vx={vx:.2f}, vy={vy:.2f}")
                # 发送 Offboard 速度指令
                await drone.offboard.set_velocity_ned(
                    VelocityNedYaw(vx, vy, 0.0, 0.0))
            else:
                # 未检测到标记，可选择原地悬停或缓慢旋转寻找
                print("未检测到标记，保持悬停")
                # 保持静止位置
                await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
            # 小延时
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"对接中发生错误: {e}")
    finally:
        cap.release()
        print("对接任务结束")

if __name__ == "__main__":
    asyncio.run(run())
