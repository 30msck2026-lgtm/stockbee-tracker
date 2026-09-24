import json
import os
import re
from bs4 import BeautifulSoup
import requests

DATA_FILE = "data.json"

if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      history = json.load(f)
  except Exception:
    history = []
else:
  history = []

# Stockbee 官方公開的文章 RSS Feed (包含最新幾日的完整發文內容)
FEED_URL = "https://stockbee.blogspot.com/feeds/posts/default?alt=json"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
}

print(f"正在讀取 Stockbee 官方最新文章 Feed: {FEED_URL}")
resp = requests.get(FEED_URL, headers=headers, timeout=20)
feed_data = resp.json()

entries = feed_data.get("feed", {}).get("entry", [])
print(f"成功取得最新 {len(entries)} 篇文章，開始搜尋 Market Monitor 數據...")

found = False
for entry in entries:
  title = entry.get("title", {}).get("$t", "")
  content = entry.get("content", {}).get("$t", "")

  # 解析文章內文的純文字
  soup = BeautifulSoup(content, "html.parser")
  text = soup.get_text("\n")

  # 尋找是否包含 MM / 4% up / T2108 等關鍵數據
  t2108_match = re.search(r"T2108[:\s]+([\d\.]+)", text, re.I)
  up_match = re.search(r"4%\s*(?:up|\+)[^\d]*(\d+)", text, re.I)
  down_match = re.search(r"4%\s*(?:down|\-)[^\d]*(\d+)", text, re.I)

  # 日期從文章發布時間提取
  pub_date = entry.get("published", {}).get("$t", "")[:10]

  if t2108_match and up_match and down_match:
    t2108_val = float(t2108_match.group(1))
    up_val = int(up_match.group(1))
    down_val = int(down_match.group(1))

    new_record = {
        "date": pub_date,
        "up_4": up_val,
        "down_4": down_val,
        "t2108": t2108_val,
    }
    print(f"成功在文章「{title}」中提取到官方數據: {new_record}")

    # 去重並排在最前面
    history = [h for h in history if h.get("date") != pub_date]
    history.insert(0, new_record)
    found = True
    break

if not found:
  print(
      "最新文章中未找到文字形式的 MM 數字，先保留現有歷史數據以避免覆蓋。"
  )

with open(DATA_FILE, "w", encoding="utf-8") as f:
  json.dump(history[:60], f, indent=2, ensure_ascii=False)

print("data.json 已更新完成！")
