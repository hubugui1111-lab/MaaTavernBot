"""屏幕坐标 —— 全部为 MaaFramework 1280×720 截图坐标"""

import numpy as np

REF_WIDTH = 1280
REF_HEIGHT = 720


def scale_coords(screenshot, *points):
    h, w = screenshot.shape[:2]
    sx, sy = w / REF_WIDTH, h / REF_HEIGHT
    return [(int(x * sx), int(y * sy)) for x, y in points]


def rect_center(rect):
    return ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)


# ===== 导航 =====
MODE_BG_BTN = (640, 270)
BG_LOBBY_START_BTN = rect_center([928, 536, 1000, 600])  # 开始下棋
ENTER_BG_BTN = rect_center([544, 264, 736, 280])

# ===== 英雄选择（实测） =====
HERO_SELECT_SECOND = (570, 300)
HERO_CONFIRM_BTN = (600, 580)

# ===== 招募 =====
TAVERN_UPGRADE_RECT = [516, 120, 544, 156]
TAVERN_REFRESH_RECT = [736, 120, 772, 156]

# 购买（实测）：从酒馆位拖到手牌区，需 500ms 慢拖
BUY_FROM_RECTS = [[400, 240, 460, 280], [480, 240, 540, 280], [560, 240, 620, 280], [640, 240, 700, 280]]
BUY_TO_RECT = [580, 620, 700, 660]

HAND_CARD_RECTS = [[588, 640, 648, 700], [464, 640, 528, 700], [672, 640, 712, 700]]
PLAY_TO_RECT = [620, 364, 668, 416]

SELL_FROM_RECT = [920, 364, 968, 416]
SELL_TO_RECT = [620, 152, 668, 172]

HERO_POWER_RECT = [864, 400, 920, 432]

TRINKET_RECTS = [[304, 320, 432, 416], [496, 320, 608, 416], [688, 320, 784, 416], [860, 320, 960, 416]]
TRINKET_CONFIRM_RECT = [604, 496, 676, 512]

TRIPLE_RECT = [624, 360, 656, 440]
POPUP_CHOICE_RECT = [496, 320, 608, 416]
GAME_END_TAP_RECT = [400, 64, 760, 360]
SKIP_DARKMOON_RECT = [16, 560, 40, 600]
CLICK_ANYWHERE = (216, 320)

POPUP_OK_RECTS = [
    [604, 424, 664, 440],
    [620, 568, 676, 584],
    [620, 568, 676, 584],
    [608, 572, 680, 592],
]
