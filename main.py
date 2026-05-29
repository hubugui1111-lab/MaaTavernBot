"""MaaTavernBot - 基于 MaaFramework 的炉石传说酒馆战旗 Bot

用法:
    MaaTavernBot.exe              # GUI 模式
    MaaTavernBot.exe --cli        # 命令行模式
    MaaTavernBot.exe --cli --port 16416
"""

import sys


def main():
    if "--cli" in sys.argv:
        import cli
        cli.main()
    else:
        import gui
        gui.main()


if __name__ == "__main__":
    main()
