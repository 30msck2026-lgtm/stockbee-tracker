import json
import os
import re
from playwright.sync_api import sync_playwright

SHEET_URL = "https://docs.google.com/spreadsheet/pub?key=0Am_cU8NLIU20dEhiQnVEN3Nnc3B1S3J6eGhKZFowN3c&output=html&widget=true"
DATA_FILE = "data.json"

if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      history = json.load(f)
  except Exception:
    history = []
else:
  history = []

print(f"啟動瀏覽器載入 Stockbee 試算表: {SHEET_URL}")
extracted = []

with sync_playwright() as p:
  browser = p.chromium.launch(headless=True)
  page = browser.new_page()

  # 前往試算表頁面，等待網路閒置
  page.goto(SHEET_URL, timeout=60000)
  page.wait_for_load_state("networkidle")
  page.wait_for_timeout(3000)  # 額外停留 3 秒確保文字渲染完成

  # 直接獲取整個頁面所有文字（避開 table/tr 結構問題）
  all_text = page.inner_text("body")
  browser.close()

# 逐行分析文字內容
lines = all_text.split("\n")
print(f"成功讀取頁面文字，共 {len(lines)} 行，開始匹配寬度數據...")

for line in lines:
  line = line.strip()
  if not line:
    continue

  # 尋找包含日期特徵的行 (如 9/24/2026, 09/24, 2026-09-24)
  # Stockbee 格式通常為: 日期 4%Up 4%Down T2108 ...
  parts = re.split(r"\s+|\t+", line)
  if parts and re.search(r"\d{1,2}[/-]\d{1,2}", parts[0]):
    # 提取該行後續的所有數字
    nums = []
    for p_item in parts[1:]:
      cleaned = re.sub(r"[^\d.]", "", p_item)
      if cleaned:
        nums.append(cleaned)

    if len(nums) >= 3:
      try:
        up_4 = int(float(nums[0]))
        down_4 = int(float(nums[1]))
        t2108 = float(nums[2])
        extracted.append({
            "date": parts[0],
            "up_4": up_4,
            "down_4": down_4,
            "t2108": t2108,
        })
      except Exception:
        continue

print(f"成功提取到 {len(extracted)} 筆 Stockbee 歷史數據！")

if extracted:
  print(f"最新一筆數據: {extracted[0]}")
  history = extracted[:60]
else:
  print("未匹配到標準列，保留原數據以防覆蓋。")

with open(DATA_FILE, "w", encoding="utf-8") as f:
  json.dump(history, f, indent=2, ensure_ascii=False)

print("data.json 已更新完成！")
