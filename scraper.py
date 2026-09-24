import json
import os
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

DATA_FILE = "data.json"

if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      history = json.load(f)
  except Exception:
    history = []
else:
  history = []

print("啟動無頭瀏覽器加載 Stockbee MM 頁面...")
all_extracted = []

with sync_playwright() as p:
  browser = p.chromium.launch(headless=True)
  page = browser.new_page()

  # 進入 Stockbee MM 頁面
  page.goto("https://stockbee.blogspot.com/p/mm.html", timeout=60000)
  page.wait_for_load_state("networkidle")

  # 遍歷頁面中的所有 frame（試算表內嵌）
  for frame in page.frames:
    try:
      # 尋找包含 2026 或 Date 的表格內容
      frame_text = frame.inner_text("body")
      if "Stockbee Market Monitor" in frame_text or "Primary Breadth" in frame_text:
        print("成功鎖定 2026 Market Monitor 嵌入表格！開始提取資料...")
        lines = frame_text.split("\n")

        for line in lines:
          parts = re.split(r"\t+|\s{2,}", line.strip())
          # 尋找類似 9/23/2026 的日期開頭行
          if parts and re.match(r"\d{1,2}/\d{1,2}/202\d", parts[0]):
            nums = []
            for item in parts[1:]:
              cleaned = re.sub(r"[^\d.]", "", item)
              if cleaned:
                nums.append(cleaned)

            if len(nums) >= 2:
              up_val = int(float(nums[0]))
              down_val = int(float(nums[1]))
              # 如果有抓到 T2108 則填入，否則取 50
              t2108_val = float(nums[4]) if len(nums) >= 5 else 50.0

              all_extracted.append({
                  "date": parts[0],
                  "up_4": up_val,
                  "down_4": down_val,
                  "t2108": t2108_val,
              })
        break
    except Exception:
      continue

  browser.close()

print(f"成功提取到 {len(all_extracted)} 筆 Stockbee 原裝數據！")

if all_extracted:
  print(f"最新一筆數據: {all_extracted[0]}")
  # 更新前 60 筆歷史
  history = all_extracted[:60]

with open(DATA_FILE, "w", encoding="utf-8") as f:
  json.dump(history, f, indent=2, ensure_ascii=False)

print("data.json 已更新成功！")
