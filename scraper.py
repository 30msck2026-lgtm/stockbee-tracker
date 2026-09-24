import json
import os
import re
from bs4 import BeautifulSoup
import requests

# Stockbee 公開發布的試算表完整 HTML 頁面
PUB_URL = "https://docs.google.com/spreadsheet/pub?key=0Am_cU8NLIU20dEhiQnVEN3Nnc3B1S3J6eGhKZFowN3c&output=html&gid=0"
DATA_FILE = "data.json"

print(f"正在讀取 Stockbee 試算表公開發布內容: {PUB_URL}")

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
}
resp = requests.get(PUB_URL, headers=headers, timeout=20)
resp.encoding = "utf-8"

# 讀取既有歷史數據
if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      history = json.load(f)
  except Exception:
    history = []
else:
  history = []

soup = BeautifulSoup(resp.text, "html.parser")
rows = soup.find_all("tr")
extracted = []

print(f"成功加載頁面，共找到 {len(rows)} 列，開始提取數據...")

for row in rows:
  cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
  if not cols:
    continue

  # 尋找第一格包含日期特徵的資料列 (如 9/24, 09/24/2026, 2026-09-24)
  if re.search(r"\d{1,2}[/-]\d{1,2}", cols[0]):
    # 提取該列的所有數值
    nums = []
    for c in cols[1:]:
      clean_num = re.sub(r"[^\d.]", "", c)
      if clean_num:
        nums.append(clean_num)

    if len(nums) >= 3:
      try:
        up_4 = int(float(nums[0]))
        down_4 = int(float(nums[1]))
        t2108 = float(nums[2])

        extracted.append({
            "date": cols[0],
            "up_4": up_4,
            "down_4": down_4,
            "t2108": t2108,
        })
      except Exception:
        continue

print(f"成功解析出 {len(extracted)} 筆 Stockbee 歷史數據！")

if extracted:
  print(f"最新一筆數據: {extracted[0]}")
  history = extracted[:60]  # 保留最新 60 筆

with open(DATA_FILE, "w", encoding="utf-8") as f:
  json.dump(history, f, indent=2, ensure_ascii=False)

print("data.json 已更新完成！")
