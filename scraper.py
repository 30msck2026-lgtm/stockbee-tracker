import json
import os
import re
from bs4 import BeautifulSoup
import requests

# Stockbee MM 頁面
URL = "https://stockbee.blogspot.com/p/mm.html"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

print("正在分析 Stockbee 頁面結構...")
resp = requests.get(URL, headers=headers)
soup = BeautifulSoup(resp.text, "html.parser")

# 尋找內嵌的試算表網址 (iframe)
iframe = soup.find("iframe")
target_url = iframe["src"] if iframe and "src" in iframe.attrs else URL

print(f"抓取數據來源: {target_url}")
data_resp = requests.get(target_url, headers=headers)
data_soup = BeautifulSoup(data_resp.text, "html.parser")

data_file = "data.json"
if os.path.exists(data_file):
  with open(data_file, "r", encoding="utf-8") as f:
    try:
      history = json.load(f)
    except Exception:
      history = []
else:
  history = []

rows = data_soup.find_all("tr")
extracted = []

for row in rows:
  cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
  # 尋找包含日期格式（例如 1/24/2025 或 2025-01-24）的列
  if cols and re.search(r"\d{1,2}/\d{1,2}|\d{4}-\d{2}", cols[0]):
    try:
      date_str = cols[0]
      # 提取整列的所有數字
      nums = [re.sub(r"[^\d.]", "", c) for c in cols if c]
      nums = [n for n in nums if n]

      if len(nums) >= 3:
        # Stockbee 表格常見順序：4% Up, 4% Down, T2108
        up_4 = int(float(nums[0]))
        down_4 = int(float(nums[1]))
        t2108 = float(nums[2])

        entry = {
            "date": date_str,
            "up_4": up_4,
            "down_4": down_4,
            "t2108": t2108,
        }
        extracted.append(entry)
    except Exception:
      continue

if extracted:
  # 將最新抓到的數據合併並去除重複日期
  for item in extracted:
    if not any(h.get("date") == item["date"] for h in history):
      history.append(item)

  # 按日期由新至舊排序（若已有排序好的列表）
  # 確保不為空
  print(f"成功取得最新數據: {extracted[0]}")
else:
  print("未能從表格提取，保留歷史紀錄。")

if history and history[0].get("date") == "未有數據":
  history.pop(0)

# 保留最近 60 日寫入
with open(data_file, "w", encoding="utf-8") as f:
  json.dump(history[:60], f, indent=2, ensure_ascii=False)

print("完成更新 data.json！")
