import json
import os
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SHEET_URL = 'https://docs.google.com/spreadsheet/pub?key=0Am_cU8NLIU20dEhiQnVEN3Nnc3B1S3J6eGhKZFowN3c&output=html&widget=true'
DATA_FILE = 'data.json'

if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
      history = json.load(f)
  except Exception:
    history = []
else:
  history = []

print(f'啟動瀏覽器載入 Google 試算表: {SHEET_URL}')
extracted = []

with sync_playwright() as p:
  browser = p.chromium.launch(headless=True)
  page = browser.new_page()

  page.goto(SHEET_URL, timeout=60000)
  # 等待真實表格列渲染完成
  page.wait_for_selector('table tr', timeout=30000)

  html_content = page.content()
  browser.close()

soup = BeautifulSoup(html_content, 'html.parser')
rows = soup.find_all('tr')
print(f'試算表渲染成功，共載入 {len(rows)} 列，開始提取數據...')

for row in rows:
  cols = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
  if not cols:
    continue

  # 尋找第一格為日期格式 (如 9/24, 09/24/2026, 2026-09-24)
  if re.search(r'\d{1,2}[/-]\d{1,2}', cols[0]):
    nums = []
    for c in cols[1:]:
      cleaned = re.sub(r'[^\d.]', '', c)
      if cleaned:
        nums.append(cleaned)

    if len(nums) >= 3:
      try:
        up_4 = int(float(nums[0]))
        down_4 = int(float(nums[1]))
        t2108 = float(nums[2])
        extracted.append({
            'date': cols[0],
            'up_4': up_4,
            'down_4': down_4,
            't2108': t2108,
        })
      except Exception:
        continue

print(f'成功提取到 {len(extracted)} 筆 Stockbee 歷史數據！')

if extracted:
  print(f'最新一筆數據: {extracted[0]}')
  history = extracted[:60]

with open(DATA_FILE, 'w', encoding='utf-8') as f:
  json.dump(history, f, indent=2, ensure_ascii=False)

print('data.json 已更新完成！')
