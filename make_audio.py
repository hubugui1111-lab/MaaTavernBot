"""按 PPT 实际内容生成配音"""
import os, win32com.client, pythoncom

OUT_DIR = r"C:\Users\lenovo\Desktop\MaaTovernBot_audio"

TEXTS = [
    # 第1页：封面
    "MaaTavernBot，基于MaaFramework的炉石传说酒馆战旗全自动脚本，开源免费，仅供学习交流使用。",

    # 第2页：免责声明
    "本软件通过图像识别和模拟操作实现游戏自动化，可能违反游戏服务条款。仅供交流学习MaaFramework框架使用。使用本软件可能导致游戏账号被警告、限制或永久封禁。开发者已尽力降低检测风险，但不对任何账号问题承担责任。使用本软件即表示您已充分了解并自愿承担上述风险。",

    # 第3页：功能列表
    "在模拟器上自动运行酒馆战旗。支持英雄选择，自动选第二个英雄。每回合升级酒馆，自动购买随从，打出手牌，使用英雄技能。自动饰品选择。对局结束后自动重开。同画面卡住超过5分钟自动重启游戏。",

    # 第4页：安装步骤
    "第一步，安装MuMu模拟器，分辨率设置为1600乘900横屏，DPI240，开启ADB调试。第二步，安装炉石传说。第三步，下载MaaTavernBot压缩包，解压到任意目录。",

    # 第5页：使用步骤
    "打开MuMu模拟器，双击MaaTavernBot启动，输入ADB端口号，点击连接，点击开始。",

    # 第6页：定时运行
    "勾选启用定时运行，设置开始时间和结束时间，到时间自动连接启动游戏，到结束时间自动关闭游戏。",

    # 第7页：常见问题
    "点击连接没反应？检查ADB端口是否正确，模拟器是否已开启ADB调试。不买随从或不升级？确认模拟器分辨率1600乘900横屏，DPI240。卡住不动？Bot有卡住检测，超过5分钟自动重启游戏。",

    # 第8页：更多问答
    "会不会掉分？会。本软件未接入打牌AI或策略。有问题怎么反馈？请使用GitHub的Issues功能。会不会接入传统对战？尚不确定。被封号怎么办？本软件仅供交流学习，开发者不对任何账号问题承担责任。",
]

os.makedirs(OUT_DIR, exist_ok=True)

pythoncom.CoInitialize()
speak = win32com.client.Dispatch("SAPI.SpVoice")

for voice in speak.GetVoices():
    desc = voice.GetDescription()
    if "Chinese" in desc or "Huihui" in desc:
        speak.Voice = voice
        print(f"使用语音: {desc}")
        break

for i, text in enumerate(TEXTS):
    wav_path = os.path.join(OUT_DIR, f"配音_{i+1:02d}.wav")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    stream.Open(wav_path, 3)
    speak.AudioOutputStream = stream
    speak.Speak(text)
    stream.Close()
    print(f"{i+1}/8: {wav_path}")

pythoncom.CoUninitialize()
print(f"\n完成！{OUT_DIR}")
