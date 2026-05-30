"""OpenCV 颜色检测工具 —— 在游戏截图中找特定颜色的 UI 元素"""
import cv2, numpy as np, os, sys

def find_red_orange(img_path, min_area=20):
    """找红/橙色区域 (HP, 箭头, 警告)
    返回: [(center_x, center_y, width, height), ...] 按 y 坐标排序
    """
    img = cv2.imread(img_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, (0, 80, 80), (25, 255, 255))
    mask2 = cv2.inRange(hsv, (160, 80, 80), (180, 255, 255))
    mask = cv2.bitwise_or(mask1, mask2)
    return _extract_regions(mask, min_area)

def find_gold_bright(img_path, min_area=20):
    """找金/亮色区域 (XP 数字, 金币, 奖励)
    返回: [(center_x, center_y, width, height), ...]
    """
    img = cv2.imread(img_path)
    b, g, r = cv2.split(img)
    mask = ((r.astype(int) > 180) & (b.astype(int) < 140)).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return _extract_regions(mask, min_area)

def _extract_regions(mask, min_area):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h >= min_area:
            regions.append((x + w//2, y + h//2, w, h))
    regions.sort(key=lambda r: (r[1], r[0]))
    return regions

def mark_candidates(img_path, regions, out_path, labels=None):
    """在截图上标记候选区域，编号后保存"""
    img = cv2.imread(img_path)
    for i, (cx, cy, w, h) in enumerate(regions):
        x, y = cx - w//2, cy - h//2
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        label = str(labels[i]) if labels else str(i)
        cv2.putText(img, label, (x-20, cy+5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)
    cv2.imwrite(out_path, img)
    return out_path

def diff_screenshots(before_path, after_path):
    """比较两张截图，返回差异值。>10 说明画面变了(点击生效)"""
    a = cv2.imread(before_path)
    b = cv2.imread(after_path)
    if a.shape != b.shape:
        return float('inf')
    return float(cv2.absdiff(a.astype(int), b.astype(int)).mean())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python color_detect.py <截图路径> [red|gold]")
        sys.exit(1)
    method = sys.argv[2] if len(sys.argv) > 2 else "red"
    regions = find_red_orange(sys.argv[1]) if method == "red" else find_gold_bright(sys.argv[1])
    for i, r in enumerate(regions):
        print(f"[{i}] ({r[0]}, {r[1]}) {r[2]}x{r[3]}")
