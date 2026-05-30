"""
MaaTavernBot 图标 v2 —— 炉石主题: 橙金石碑 + 漩涡纹
"""
from PIL import Image, ImageDraw, ImageFont
import math, os

OUT_DIR = r"C:\Users\lenovo\Desktop\MaaTavernBot_icons"
os.makedirs(OUT_DIR, exist_ok=True)

# 炉石配色
GOLD_EDGE = (230, 150, 30)
GOLD_MID = (255, 185, 40)
GOLD_CENTER = (255, 210, 80)
BROWN = (120, 60, 20)
BROWN_LIGHT = (160, 90, 30)
BG = (20, 12, 5)
GLOW_BLUE = (60, 140, 255, 180)

def hex_to_rgba(hex_str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def draw_icon(size):
    """炉石主题: 八角石碑 + 金色漩涡 + M"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = size / 2
    outer = size * 0.43

    # ── 1. 石碑底座 (八角形) ──
    # 用多边形近圆
    n = 16
    outer_pts = []
    inner_pts = []
    for i in range(n):
        angle = (i * 360 / n - 90) * math.pi / 180
        # 外圈 - 略有起伏模拟石头
        r_var = outer * (1 + 0.04 * math.sin(i * 5))
        x = cx + r_var * math.cos(angle)
        y = cx + r_var * math.sin(angle)
        outer_pts.append((x, y))
        # 内圈 (漩涡边界)
        inner_r = outer * 0.78
        ix = cx + inner_r * math.cos(angle)
        iy = cx + inner_r * math.sin(angle)
        inner_pts.append((ix, iy))

    # 石碑底
    draw.polygon(outer_pts, fill=BROWN)
    # 石碑亮面
    draw.polygon(inner_pts, fill=BROWN_LIGHT)

    # ── 2. 金色边框 ──
    border_r = outer * 0.95
    draw.ellipse([cx - border_r, cx - border_r, cx + border_r, cx + border_r],
                 outline=GOLD_EDGE, width=max(2, size // 18))
    draw.ellipse([cx - border_r + max(1, size//64), cx - border_r + max(1, size//64),
                 cx + border_r - max(1, size//64), cx + border_r - max(1, size//64)],
                 outline=GOLD_MID, width=max(1, size // 40))

    # ── 3. 中心漩涡 (炉石标志性蓝色漩涡) ──
    swirl_r = outer * 0.55
    draw.ellipse([cx - swirl_r, cx - swirl_r, cx + swirl_r, cx + swirl_r],
                 fill=(30, 80, 180, 180))

    # 漩涡纹理 - 几条弧线
    for a in range(0, 360, 45):
        angle = a * math.pi / 180
        sr = swirl_r * 0.65
        draw.arc([cx - sr, cx - sr, cx + sr, cx + sr],
                 a - 30, a + 30, fill=(100, 180, 255, 120), width=max(1, size // 50))

    # 漩涡核心亮点
    core_r = swirl_r * 0.25
    draw.ellipse([cx - core_r, cx - core_r, cx + core_r, cx + core_r],
                 fill=(255, 255, 255, 200))

    # ── 4. 金色外圈光晕 ──
    halo_r = outer * 0.70
    draw.ellipse([cx - halo_r, cx - halo_r, cx + halo_r, cx + halo_r],
                 outline=(255, 200, 80, 120), width=max(2, size // 24))

    # ── 5. 中心 "M" ──
    m_size = max(8, size // 7)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", m_size)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "M", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # 白色阴影
    draw.text((cx - tw/2 + 1, cx - th/2 + 1 - m_size*0.05), "M",
              fill=(0, 0, 0, 180), font=font)
    # 金色主体
    draw.text((cx - tw/2, cx - th/2 - m_size*0.05), "M",
              fill=(255, 220, 80, 255), font=font)

    # ── 6. 顶部高光 ──
    hl_y = cx - outer * 0.5
    hl_r = outer * 0.15
    draw.ellipse([cx - hl_r, hl_y - hl_r, cx + hl_r, hl_y + hl_r],
                 fill=(255, 255, 255, 50))

    return img


# ── 生成各尺寸 ──
sizes = [16, 24, 32, 48, 64, 128, 256]
images = {}

for s in sizes:
    img = draw_icon(s)
    images[s] = img
    img.save(os.path.join(OUT_DIR, f"icon_{s}x{s}.png"))
    print(f"  icon_{s}x{s}.png")

# EXE 图标
images[256].save(
    os.path.join(OUT_DIR, "MaaTavernBot.ico"),
    format='ICO',
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
)
print("  MaaTavernBot.ico")

# 托盘 + 任务栏
images[16].save(os.path.join(OUT_DIR, "tray_16.png"))
images[32].save(os.path.join(OUT_DIR, "tray_32.png"))
images[48].save(os.path.join(OUT_DIR, "taskbar_48.png"))
print("  tray_16/32.png, taskbar_48.png")

print(f"\nDone: {OUT_DIR}")
