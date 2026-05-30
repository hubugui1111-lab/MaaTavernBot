"""本地屏幕识别 —— 模板匹配，不依赖外部 API"""

import os, cv2, numpy as np

IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resource", "image")

SCREENS = {
    # 特征最明显的优先
    "quest_hub": "screen_quest_hub.png",  # 任务/日志中心（必须比quest优先）
    "quest": "screen_quest.png",     # 任务界面
    "stats": "screen_stats.png",      # 单人完整战绩
    "main_menu": "main_menu.png",
    "mode_select": "mode_select.png",
    "bg_lobby": "bg_lobby.png",
    "hero_select": "hero_select.png",
    "recruit": "recruit_phase.png",
    "combat": "combat_phase.png",
    "game_end": "game_end.png",
    "shop": "screen_shop.png",        # 商店界面
    "collection": "screen_collection.png",  # 我的收藏
}

# 每个界面的返回按钮坐标
BACK_BUTTONS = {
    "quest": (50, 50),      # 任务界面返回箭头
    "quest_hub": (50, 50),  # 任务中心返回箭头
    "stats": (1037, 663),
    "main_menu": None,
    "mode_select": (60, 60),
    "bg_lobby": (1044, 671),
    "hero_select": None,
    "recruit": None,
    "combat": None,
    "game_end": (100, 660),
    "shop": (1040, 636),
    "collection": (1060, 666),  # 我的收藏返回按钮
    "unknown": (60, 60),
}

_templates = {}


def identify_screen(img):
    """用模板匹配识别当前画面"""
    h, w = img.shape[:2]
    best_score = 0
    best_name = "unknown"

    for name, filename in SCREENS.items():
        if name not in _templates:
            path = os.path.join(IMAGE_DIR, filename)
            if os.path.exists(path):
                _templates[name] = cv2.imread(path)
        tpl = _templates.get(name)
        if tpl is None or tpl.shape[0] > h or tpl.shape[1] > w:
            continue
        if tpl.shape[:2] != (h, w):
            tpl = cv2.resize(tpl, (w, h))
        score = float(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)[0][0])
        if score > best_score:
            best_score = score
            best_name = name

    return best_name, best_score


def get_back_button(img):
    """返回当前界面的返回按钮坐标"""
    name, _ = identify_screen(img)
    return BACK_BUTTONS.get(name, (60, 60))
