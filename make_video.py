"""PPT + 系统TTS → 视频（无需安装任何语音包）"""
import os, sys, glob, subprocess, wave, struct

IMG_DIR = r"C:\Users\lenovo\Desktop\MaaTovernBot"
OUTPUT = r"C:\Users\lenovo\Desktop\MaaTavernBot.mp4"

TEXTS = [
    "大家好，今天给大家介绍一款开源免费的炉石传说酒馆战旗全自动脚本——MaaTavernBot。",
    "首先确保你的模拟器分辨率为1600乘900横屏，DPI设置为240，开启ADB调试。",
    "打开MaaTavernBot，输入模拟器的ADB端口号，点击连接，连接成功后点击开始。",
    "Bot会自动检测当前画面，从主菜单进入模式选择，选择酒馆战旗，点击寻找对局。",
    "进入英雄选择界面后，Bot会自动选择第二个英雄并确认。",
    "进入招募阶段，Bot会优先升级酒馆，然后自动购买随从，把手牌拖到场上打出，还会使用英雄技能。",
    "支持定时运行，设置时间后到点自动启动和停止，关闭窗口可以最小化到系统托盘。",
    "完全免费开源，GitHub搜索MaaTavernBot即可下载，感谢观看，求个三连。",
]


def generate_audio_sapi(text, wav_path):
    """用 Windows SAPI (Microsoft Huihui voice) 生成音频"""
    import win32com.client
    from win32com.client import constants

    speak = win32com.client.Dispatch("SAPI.SpVoice")
    # 尝试用中文女声
    for voice in speak.GetVoices():
        if "Chinese" in voice.GetDescription() or "Zira" in voice.GetDescription() or "Huihui" in voice.GetDescription():
            speak.Voice = voice
            print(f"  使用语音: {voice.GetDescription()}")
            break

    # 输出到 WAV 文件
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    stream.Open(wav_path, constants.SSFMCreateForWrite)

    speak.AudioOutputStream = stream
    speak.Speak(text)
    stream.Close()
    print(f"  已生成: {wav_path}")


def wav_to_mp3(wav_path, mp3_path):
    """WAV → MP3 (用 ffmpeg)"""
    subprocess.run([
        "ffmpeg", "-y", "-i", wav_path, "-b:a", "128k", mp3_path,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    images = sorted(
        glob.glob(os.path.join(IMG_DIR, "*.png")),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split("_")[-1])
    )
    print(f"找到 {len(images)} 张图片")

    # 生成配音
    audio_files = []
    for i, (text, img) in enumerate(zip(TEXTS, images)):
        wav = f"/tmp/slide_{i}.wav"
        mp3 = f"/tmp/slide_{i}.mp3"
        print(f"配音 {i+1}/8 ...")
        generate_audio_sapi(text, wav)
        wav_to_mp3(wav, mp3)
        audio_files.append(mp3)

    # 用 moviepy 合成视频
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
    clips = []
    for i, img_path in enumerate(images):
        mp3 = audio_files[i]
        audio = AudioFileClip(mp3)
        clip = ImageClip(img_path, duration=audio.duration)
        clip = clip.with_audio(audio)
        clip = clip.resized(height=1080)
        clips.append(clip)
        print(f"幻灯片 {i+1}: {audio.duration:.1f}s")

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(OUTPUT, fps=24, codec="libx264", audio_codec="aac")
    print(f"\n视频生成完成: {OUTPUT}")


if __name__ == "__main__":
    main()
