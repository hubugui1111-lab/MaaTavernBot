"""MaaTavernBot v1.5 —— edge-tts 配音生成器"""
import asyncio, os, sys

OUT_DIR = r"C:\Users\lenovo\Desktop\MaaTavernBot_v15_audio"
os.makedirs(OUT_DIR, exist_ok=True)

# 微软晓晓 — 中文圈最火免费 AI 配音
VOICE = "zh-CN-XiaoxiaoNeural"

VOICEOVER = [
    # 第1页：封面
    "MaaTavernBot 1.5版本，基于MaaFramework的炉石传说酒馆战旗全自动脚本。开源免费，仅供学习交流使用。",

    # 第2页：免责声明
    "本软件通过图像识别和模拟操作实现游戏自动化，可能违反游戏服务条款。仅供交流学习MaaFramework框架使用。使用本软件可能导致游戏账号被警告、限制或永久封禁。开发者已尽力降低检测风险，但不对任何账号问题承担责任。使用本软件即表示您已充分了解并自愿承担上述风险。",

    # 第3页：v1.5 新功能
    "1.5版本带来了三大更新。第一，任务自动刷新功能。对局结束后自动检查日常任务，OCR识别零进度任务并自动点击刷新，每天更换一个未完成的任务。第二，全新顶部导航风格界面。顶部导航栏加左侧控制面板加右侧日志区，三栏布局，支持系统托盘后台运行。第三，本地模板匹配导航系统。可识别十一种游戏界面，不依赖任何外部API，卡住自动返回主菜单。",

    # 第4页：任务刷新原理
    "任务刷新工作流程。游戏获胜后自动检测结算界面，通过返回按钮回到主菜单，点击底部任务图标进入任务中心，点击侧边栏进入真正的任务界面，截图并用MinerU OCR读取所有任务进度，找到进度为零的日常任务，点击对应刷新箭头更换任务，最后返回主菜单继续下一局。每个账号每天只能刷新一次。千问多模态AI作为备用方案。",

    # 第5页：安装步骤
    "安装只需三步。第一步，安装MuMu模拟器，分辨率设为一千六乘九百横屏，DPI二百四，开启ADB调试。第二步，安装炉石传说并登录账号。第三步，从GitHub Releases下载最新版压缩包，解压到任意目录，双击MaaTavernBot即可运行。",

    # 第6页：使用步骤
    "使用非常简单。打开MuMu模拟器，启动炉石传说，双击MaaTavernBot，输入ADB端口号，MuMu默认端口为一六三八四或一六四一六，点击连接按钮，再点击开始。如需定时运行，勾选启用定时运行，设置开始和结束时间，到时间自动启动，到点自动关闭。",

    # 第7页：常见问题
    "点击连接没反应？请检查ADB端口是否正确，模拟器是否开启了ADB调试。不买随从或不升级？确认分辨率一千六乘九百横屏，DPI二百四。任务刷新失败？每天只能刷新一次。卡住不动？Bot有卡住检测，超过五分钟自动重启游戏。会不会掉分？会的，本软件不接入打牌AI，纯盲打策略。",

    # 第8页：技术栈
    "MaaTavernBot基于MaaFramework框架。OpenCV模板匹配和颜色检测。MinerU OCR本地文字识别。千问多模态AI作为备用方案。PySide6桌面界面。项目完全开源，GitHub搜索hubugui1111-lab MaaTavernBot。1.5版本已发布，欢迎Star支持。",
]


async def gen_one(i, text, filename):
    """用 edge-tts 生成单个 mp3"""
    import subprocess
    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", VOICE,
        "--text", text,
        "--write-media", filename,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        print(f"  出错: {stderr.decode('utf-8', errors='replace')[:200]}")
        return False
    sz = os.path.getsize(filename) / 1024
    print(f"  [{i+1}/8] OK  {sz:.0f}KB  {filename}")
    return True


async def main():
    print(f"配音: {VOICE}")
    print(f"输出: {OUT_DIR}\n")

    tasks = []
    for i, text in enumerate(VOICEOVER):
        filename = os.path.join(OUT_DIR, f"配音_{i+1:02d}.mp3")
        tasks.append(gen_one(i, text, filename))

    results = await asyncio.gather(*tasks)
    ok = sum(1 for r in results if r)
    print(f"\n完成! {ok}/{len(VOICEOVER)} 个配音文件")
    print(f"文件夹: {OUT_DIR}")
    print("打开文件夹 → 拖入剪映 → 配 PPT 截图即可")


asyncio.run(main())
