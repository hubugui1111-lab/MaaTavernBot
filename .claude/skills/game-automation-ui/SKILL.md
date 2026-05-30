---
name: game-automation-ui
description: >
  Use this skill when building game automation with MaaFramework-style ADB-based image recognition.
  Covers: finding and hardcoding button coordinates via OpenCV (template matching, HSV/R-channel color
  detection), screenshot-based user confirmation loops, dual OCR (local MinerU + cloud Qwen multimodal),
  coordinate refinement by screenshot comparison, and navigation flow verification. Use whenever the user
  mentions game bot, game automation, screenshot recognition, finding buttons/arrows in game UI,
  MaaFramework, ADB control, or hardcoding UI element positions.
---

# Game Automation UI Positioning

## Overview

This skill covers the complete workflow for building game automation UI positioning: from raw screenshot
to verified hardcoded coordinates. The core philosophy: **local image processing first, cloud AI as backup,
user confirms before irreversible actions**.

## When to Use

- Building game bots that need to find and click UI elements
- Working with MaaFramework, OpenCV template matching, or ADB-based automation
- Finding button/arrow coordinates in game screenshots
- Setting up OCR for in-game text reading
- Verifying navigation flows with screenshot comparison

## Required Tools

```bash
pip install opencv-python numpy maafw
# For OCR:
npm install -g mineru-open-api    # local OCR
pip install edge-tts               # if generating voiceovers
```

## The Core Workflow

### Phase 1: Screen Identification

Use OpenCV template matching to identify which screen the game is on. This is the foundation — all
coordinate-based actions depend on knowing the current screen.

**Template creation:**
1. Screenshot the target screen via ADB
2. Crop a distinctive region (unique UI element, not generic background)
3. Save as `screen_<name>.png` in the project's image directory

**Matching code** (add to project):
```python
import cv2, numpy as np

SCREENS = {
    "main_menu": "main_menu.png",
    "quest": "screen_quest.png",
    # ... more screens
}

_templates = {}

def identify_screen(img):
    """Return (screen_name, confidence_score)"""
    h, w = img.shape[:2]
    best_score, best_name = 0, "unknown"
    for name, filename in SCREENS.items():
        if name not in _templates:
            _templates[name] = cv2.imread(image_dir + "/" + filename)
        tpl = _templates.get(name)
        if tpl is None or tpl.shape[0] > h or tpl.shape[1] > w:
            continue
        if tpl.shape[:2] != (h, w):
            tpl = cv2.resize(tpl, (w, h))
        score = float(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)[0][0])
        if score > best_score:
            best_score, best_name = score, name
    return best_name, best_score
```

**Navigation:** For each screen, maintain a `BACK_BUTTONS` dict with hardcoded (x, y) coordinates.
When navigating to main menu, loop: identify → click back button → re-identify → repeat until
target screen reached.

### Phase 2: UI Element Detection

To find clickable elements (buttons, arrows, icons), use the following approach in order:

#### 2a. Color Filtering (primary method)

**Red/orange elements (arrows, warnings):**
```python
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# Broad red-orange range (inclusive)
mask1 = cv2.inRange(hsv, (0, 80, 80), (25, 255, 255))
mask2 = cv2.inRange(hsv, (160, 80, 80), (180, 255, 255))
mask = cv2.bitwise_or(mask1, mask2)
```

**Gold/bright elements (XP numbers, rewards):**
```python
b, g, r = cv2.split(img)
mask = ((r.astype(int) > 180) & (b.astype(int) < 140)).astype(np.uint8) * 255
```

**After masking:** Use `cv2.findContours` → filter by size → sort by position → mark candidates
with colored rectangles and index labels → save marked image for user review.

#### 2b. Structure-Based Positioning

When color alone isn't enough, use the **relative positioning** approach:
1. Find a known reference element (e.g., OCR-confirmed XP numbers "900", "1000")
2. Scan a fixed region to the right/left/below the reference
3. Look for bright regions, edge patterns, or specific shapes in that region
4. The target element is at `(reference_x + offset, reference_y)`

#### 2c. Screenshot Comparison for Verification

After each click attempt, compare screenshots before and after to verify action:
```python
diff = cv2.absdiff(img_before.astype(int), img_after.astype(int)).mean()
# diff > 10 means the screen changed (click worked)
```

### Phase 3: User Confirmation (CRITICAL)

**Never perform irreversible actions without user confirmation.** This is the most important rule.

**For daily-limited actions (quest rerolls, purchases, etc.):**
1. Take a clean screenshot of the target screen
2. Draw candidate positions with numbered labels (green boxes, red crosses)
3. Save the marked image and open it for the user
4. Also save zoomed-in crops (200x200) around each candidate
5. **Wait for user to explicitly say which number/position is correct**
6. Only then hardcode and test

**Marking function:**
```python
def mark_and_save(img, candidates, out_path):
    marked = img.copy()
    for i, (x, y, w, h) in enumerate(candidates):
        cv2.rectangle(marked, (x, y), (x+w, y+h), (0,255,0), 2)
        cv2.putText(marked, str(i), (x-20, y+h//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.imwrite(out_path, marked)
    return out_path
```

**Common pitfall:** The first set of coordinates is ALMOST ALWAYS wrong. Expect 2-4 iterations
of mark → user-rejects → refine → mark-again before finding the correct positions.

### Phase 4: OCR for Text Reading

Use a dual approach for reliability:

#### 4a. Primary: MinerU (local, free)
```python
def ocr_mineru(image_path):
    r = subprocess.run(
        f'mineru-open-api.cmd extract "{image_path}"',
        capture_output=True, timeout=120, shell=True,
    )
    # CRITICAL: MinerU outputs UTF-8, not system encoding
    return (r.stdout or b"").decode("utf-8", errors="replace")
    # NOTE: stderr contains only "Thinking.../Done" status, not text
```

**Key bug to avoid:** `subprocess.run(text=True)` uses system default encoding (GBK on Chinese
Windows), which corrupts UTF-8 output. Always use `capture_output=True` (bytes) + `.decode('utf-8')`.

#### 4b. Backup: Qwen Multimodal (cloud, higher accuracy)
```python
def ocr_qwen(image_path, api_key):
    """Use when MinerU output is garbled or incomplete"""
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    response = client.chat.completions.create(
        model="qwen-vl-max",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                {"type": "text", "text": "List all text visible in this game screenshot, especially numbers in X/Y format like 0/30."}
            ]
        }]
    )
    return response.choices[0].message.content
```

### Phase 5: Navigation Flow Verification

After each coordinate is set, verify the full navigation loop end-to-end:

1. Navigate to screen A → click button → verify screen B appeared (template match)
2. Click back → verify returned to screen A
3. Full round-trip: main menu → target screen → action → back → main menu
4. Log every navigation step with screen name and confidence score

### Phase 6: Hardcoding and Code Structure

Once verified, hardcode coordinates in a dedicated constants file:

```python
# All hardcoded coordinates for 1280x720 resolution
QUEST_BTN = (330, 645)       # Quest icon on mode_select
QUEST_SIDEBAR = (234, 245)   # Sidebar tab in quest_hub
REFRESH_ARROWS = [(474, 191), (646, 191), (818, 191)]  # 3 quest refresh buttons
```

**Structure pattern:**
- `screen_match.py` — template matching + BACK_BUTTONS dict
- `quest_reroll.py` — specific feature logic (navigation + OCR + action)
- Test script — separate file for one-shot testing

## Common Problems and Solutions

### "Template matches but back button doesn't work"
- The back button might be in a different position on this specific screen
- Use OpenCV to find bright regions (likely buttons): threshold grayscale at 200+
- Test one candidate at a time with screenshot comparison

### "OCR returns garbled text"
- Check encoding: MinerU uses UTF-8, subprocess defaults to system encoding
- Check you're reading STDOUT not STDERR (MinerU puts text in stdout)
- Filter out MinerU's own status messages ("Thinking...", "Parsing X/Y pages")

### "User rejected all candidate positions"
- Broaden color detection thresholds
- Try a different detection method (edge detection instead of color)
- Ask user for a reference point ("what's near the target?")
- Use OCR text position to estimate target location

### "Click seems to work but quest didn't change"
- Daily-limited actions may have already been consumed
- Verify with screenshot comparison before and after
- Check game's cooldown/reset timer

## Deliverables Checklist

After completing UI positioning for a feature:
- [ ] Template images for all involved screens
- [ ] BACK_BUTTONS verified for all screens
- [ ] Navigation flow verified end-to-end (round trip)
- [ ] UI element coordinates hardcoded and confirmed by user
- [ ] OCR working (MinerU primary + cloud backup)
- [ ] Test script produces expected results
- [ ] Devlog updated with all attempts (successful and failed)
