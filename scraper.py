import csv
import io
import json
import os
import re
import requests

# Stockbee 官方永久發布的 Google 試算表 CSV 導出網址
CSV_URL = (
    "https://docs.google.com/spreadsheet/pub?key=0Am_cU8NLIU20dEhiQnVEN3Nnc3B1S3J6eGhKZFowN3c&output=csv"
)
DATA_FILE = "data.json"

print(f"正在直接下載 Stockbee 官方試算表數據: {CSV_URL}")

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
}
resp = requests.get(CSV_URL, headers=headers, timeout=20)
resp.encoding = "utf-8"

# 讀取現有歷史紀錄
if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      history = json.load(f)
  except Exception:
    history = []
else:
  history = []

reader = list(csv.reader(io.StringIO(resp.text)))
extracted = []

print(f"下載成功，總共取得 {len(reader)} 行數據，開始解析欄位...")

for row in reader:
  # 尋找包含日期格式的第一欄 (例如 9/24/2026 或 2026-09-24)
  if row and re.search(r"\d{1,2}[/-]\d{1,2}", row[0]):
    # 提取後續所有包含數值的儲存格
    nums = []
    for cell in row[1:]:
      cleaned = re.sub(r"[^\d.]", "", cell.strip())
      if cleaned:
        nums.append(cleaned)

    # 提取 Stockbee 標準寬度：4% Up, 4% Down, T2108
    if len(nums) >= 3:
      try:
        up_4 = int(float(nums[0]))
        down_4 = int(float(nums[1]))
        t2108 = float(nums[2])

        extracted.append({
            "date": row[0].strip(),
            "up_4": up_4,
            "down_4": down_4,
            "t2108": t2108,
        })
      except Exception:
        continue

print(f"成功解析出 {len(extracted)} 筆 Stockbee 歷史數據！")

if extracted:
  print(f"最新一筆數據: {extracted[0]}")
  history = extracted[:60]  # 保留最新的 60 天真實記錄

with open(DATA_FILE, "w", encoding="utf-8") as f:
  json.dump(history, f, indent=2, ensure_ascii=False)

print("data.json 已更新成功！")
