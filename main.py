"""MaaTavernBot - 基于 MaaFramework 的炉石传说酒馆战旗 Bot

用法:
    MaaTavernBot.exe              # GUI 模式
    MaaTavernBot.exe --cli        # 命令行模式
    MaaTavernBot.exe --cli --port 16416
"""

import sys, os, subprocess


def kill_old_instance():
    """启动时自动杀掉旧的 Bot 进程"""
    try:
        name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        # 杀所有同名进程（排除自己）
        me = os.getpid()
        r = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {name}.exe', '/FO', 'CSV'],
                          capture_output=True, text=True, timeout=5)
        for line in r.stdout.split('\n'):
            if '.exe' in line:
                pid = line.split(',')[1].strip('"')
                if pid.isdigit() and int(pid) != me:
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
    except:
        pass


def main():
    kill_old_instance()
    if "--cli" in sys.argv:
        import cli
        cli.main()
    else:
        import gui
        gui.main()


if __name__ == "__main__":
    main()
