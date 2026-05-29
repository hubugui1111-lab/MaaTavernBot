"""命令行模式 —— 供 --cli 参数使用"""

import os
import sys
import time
import argparse

from maa.toolkit import Toolkit
from maa.resource import Resource
from maa.controller import AdbController
from maa.tasker import Tasker

from bot.phase_detector import PhaseDetector
from bot.game_bot import BotAction


def get_app_dir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def pick_device_interactive(devices):
    print(f"\n找到 {len(devices)} 个 ADB 设备:")
    for i, d in enumerate(devices):
        print(f"  [{i+1}] {d.address}")
    while True:
        try:
            choice = input(f"\n请选择设备 [1-{len(devices)}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(devices):
                return devices[idx]
        except (ValueError, KeyboardInterrupt):
            pass
        print("输入无效，请重试")


def find_device(preferred_port=None):
    devices = Toolkit.find_adb_devices()
    if not devices:
        print("\n[错误] 未找到 ADB 设备！")
        sys.exit(1)
    if preferred_port:
        port_str = str(preferred_port)
        for d in devices:
            if port_str in d.address:
                return d
        print(f"[警告] 未找到端口 {preferred_port} 的设备")
    return pick_device_interactive(devices)


def main():
    parser = argparse.ArgumentParser(description="炉石传说酒馆战旗 Bot")
    parser.add_argument("--port", type=str, help="ADB 端口号")
    parser.add_argument("--cli", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    print("=" * 45)
    print("  炉石传说酒馆战旗 Bot v1.1")
    print("=" * 45)

    app_dir = get_app_dir()
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = app_dir
    user_path = os.path.join(exe_dir, ".maa")
    os.makedirs(user_path, exist_ok=True)
    Toolkit.init_option(user_path)

    device = find_device(preferred_port=args.port)

    print(f"\n[信息] 正在连接 {device.address} ...")
    controller = AdbController(
        adb_path=device.adb_path, address=device.address,
        screencap_methods=device.screencap_methods,
        input_methods=device.input_methods, config=device.config,
    )
    controller.post_connection().wait()
    if not controller.connected:
        print("[错误] 设备连接失败！")
        sys.exit(1)
    print("[信息] 设备已连接")

    BotAction.adb_device = device.address

    resource_dir = os.path.join(app_dir, "resource")
    print("[信息] 正在加载资源...")
    resource = Resource()
    resource.post_bundle(resource_dir).wait()
    resource.register_custom_recognition("PhaseDetector", PhaseDetector())
    resource.register_custom_action("BotAction", BotAction())
    print("[信息] 资源加载完成")

    tasker = Tasker()
    tasker.bind(resource, controller)
    if not tasker.inited:
        print("[错误] Tasker 初始化失败！")
        sys.exit(1)

    print("\n" + "=" * 45)
    print("  Bot 正在运行... 按 Ctrl+C 停止")
    print("=" * 45 + "\n")

    tasker.post_task("MainLoop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[信息] 正在停止...")
        tasker.post_stop().wait()
        print("[完成] Bot 已停止")


if __name__ == "__main__":
    main()
