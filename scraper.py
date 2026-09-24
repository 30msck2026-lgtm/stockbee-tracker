import io
import json
import os
import re
from bs4 import BeautifulSoup
import requests

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
}
DATA_FILE = 'data.json'

# 讀取現有歷史
if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
      history = json.load(f)
  except Exception:
    history = []
else:
  history = []

# Stockbee MM 主頁解析
BLOG_URL = 'https://stockbee.blogspot.com/p/mm.html'
found_entries = []

try:
  res = requests.get(BLOG_URL, headers=HEADERS, timeout=15)
  soup = BeautifulSoup(res.text, 'html.parser')

  # 尋找頁面中的表格或嵌入來源
  for row in soup.find_all('tr'):
    cols = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
    # 尋找符合日期特徵的資料列 (如 9/23, 2026-09-23)
    if cols and re.search(r'\d{1,2}/\d{1,2}|\d{4}[-/]\d{2}', cols[0]):
      nums = [re.sub(r'[^\d.]', '', c) for c in cols[1:] if c]
      nums = [n for n in nums if n]
      if len(nums) >= 3:
        try:
          found_entries.append({
              'date': cols[0],
              'up_4': int(float(nums[0])),
              'down_4': int(float(nums[1])),
              't2108': float(nums[2]),
          })
        except Exception:
          continue
except Exception as e:
  print(f'解析出錯: {e}')

# 若成功抓到資料，合併去重
if found_entries:
  for entry in found_entries:
    if not any(h.get('date') == entry['date'] for h in history):
      history.insert(0, entry)
  print(f'成功獲取最新數據: {found_entries[0]}')
else:
  print('頁面未更新或格式未變更，保留現有歷史數據。')

# 儲存最近 60 筆
with open(DATA_FILE, 'w', encoding='utf-8') as f:
  json.dump(history[:60], f, indent=2, ensure_ascii=False)
