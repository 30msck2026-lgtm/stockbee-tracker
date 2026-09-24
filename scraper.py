import json
import os
import re
from bs4 import BeautifulSoup
import requests

URL = 'https://stockbee.blogspot.com/p/mm.html'
headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
}

print('正在抓取 Stockbee 頁面...')
response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

data_file = 'data.json'
if os.path.exists(data_file):
  with open(data_file, 'r', encoding='utf-8') as f:
    try:
      history = json.load(f)
    except Exception:
      history = []
else:
  history = []

tables = soup.find_all('table')
found = False

for table in tables:
  rows = table.find_all('tr')
  for row in rows:
    cols = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
    if len(cols) >= 4 and any(char.isdigit() for char in cols[0]):
      date_val = cols[0]
      nums = [re.sub(r'[^\d.]', '', c) for c in cols[1:4]]

      try:
        up_4 = int(float(nums[0])) if nums[0] else 0
        down_4 = int(float(nums[1])) if nums[1] else 0
        t2108 = float(nums[2]) if nums[2] else 0.0

        new_entry = {
            'date': date_val,
            'up_4': up_4,
            'down_4': down_4,
            't2108': t2108,
        }

        if not any(item.get('date') == date_val for item in history):
          history.insert(0, new_entry)
          print(f'成功抓取最新數據: {new_entry}')
        else:
          print('今日數據已存在，無需重複寫入。')

        found = True
        break
      except Exception:
        continue
  if found:
    break

if not history:
  history = [{
      'date': '未有數據',
      'up_4': 0,
      'down_4': 0,
      't2108': 0.0,
  }]

with open(data_file, 'w', encoding='utf-8') as f:
  json.dump(history[:60], f, indent=2, ensure_ascii=False)

print('已完成更新 data.json！')
