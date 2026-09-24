import json
import os
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

DATA_FILE = 'data.json'

if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
      history = json.load(f)
  except Exception:
    history = []
else:
  history = []

print('啟動無頭瀏覽器前往 Stockbee MM 頁面...')
extracted_rows = []

with sync_playwright() as p:
  browser = p.chromium.launch(headless=True)
  page = browser.new_page()

  # 前往 Stockbee MM 專頁
  page.goto('https://stockbee.blogspot.com/p/mm.html', timeout=60000)
  page.wait_for_load_state('networkidle')

  content = page.content()
  soup = BeautifulSoup(content, 'html.parser')

  # 遍歷所有 iframe，只抓取真正的 Google Sheets / 試算表表格，避開 recaptcha
  target_src = None
  for ifr in soup.find_all('iframe'):
    src = ifr.get('src', '')
    if 'google.com/spreadsheets' in src or 'docs.google.com' in src:
      target_src = src
      break

  if target_src:
    print(f'成功鎖定真實數據表格: {target_src}')
    page.goto(target_src, timeout=60000)
    page.wait_for_load_state('networkidle')
    # 等待表格行載入完成
    page.wait_for_selector('tr', timeout=20000)
    content = page.content()
    soup = BeautifulSoup(content, 'html.parser')
  else:
    print('未找到外部 iframe，直接解析主頁面表格內容...')

  browser.close()

# 解析表格資料列
for tr in soup.find_all('tr'):
  cols = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
  # 尋找第一欄包含日期的列 (如 9/24, 2026-09-24)
  if cols and re.search(r'\d{1,2}[/-]\d{1,2}', cols[0]):
    row_nums = []
    for c in cols[1:]:
      clean_num = re.sub(r'[^\d.]', '', c)
      if clean_num:
        row_nums.append(clean_num)

    if len(row_nums) >= 3:
      try:
        up_4 = int(float(row_nums[0]))
        down_4 = int(float(row_nums[1]))
        t2108 = float(row_nums[2])
        extracted_rows.append({
            'date': cols[0],
            'up_4': up_4,
            'down_4': down_4,
            't2108': t2108,
        })
      except Exception:
        continue

print(f'成功從 Stockbee 提取到 {len(extracted_rows)} 筆歷史紀錄！')

if extracted_rows:
  for row in reversed(extracted_rows):
    history = [h for h in history if h.get('date') != row['date']]
    history.insert(0, row)

# 保留最近 60 筆寫入
with open(DATA_FILE, 'w', encoding='utf-8') as f:
  json.dump(history[:60], f, indent=2, ensure_ascii=False)

print('data.json 已更新完成！')
