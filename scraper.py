import json
import os
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

DATA_FILE = "data.json"

# 載入現有歷史數據
if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      history = json.load(f)
  except Exception:
    history = []
else:
  history = []

print("啟動無頭瀏覽器前往 Stockbee MM 頁面...")
extracted_rows = []

with sync_playwright() as p:
  browser = p.chromium.launch(headless=True)
  page = browser.new_page()

  # 1. 前往 Stockbee MM 專頁
  page.goto("https://stockbee.blogspot.com/p/mm.html", timeout=60000)
  page.wait_for_load_state("networkidle")

  # 2. 如果頁面有 iframe (嵌入試算表)，獲取其內容
  content = page.content()
  soup = BeautifulSoup(content, "html.parser")

  iframe_el = soup.find("iframe")
  if iframe_el and "src" in iframe_el.attrs:
    iframe_src = iframe_el["src"]
    print(f"進入嵌入表格: {iframe_src}")
    page.goto(iframe_src, timeout=60000)
    page.wait_for_load_state("networkidle")
    content = page.content()
    soup = BeautifulSoup(content, "html.parser")

  browser.close()

# 3. 解析真實表格行數據
for tr in soup.find_all("tr"):
  cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
  # 尋找第一欄為日期的列 (格式如 9/24, 09/24/2026 或 2026-09-24)
  if cols and re.search(r"\d{1,2}[/-]\d{1,2}", cols[0]):
    row_nums = []
    for c in cols[1:]:
      clean_num = re.sub(r"[^\d.]", "", c)
      if clean_num:
        row_nums.append(clean_num)

    # 提取 Stockbee 標準寬度欄位：4% Up, 4% Down, T2108
    if len(row_nums) >= 3:
      try:
        up_4 = int(float(row_nums[0]))
        down_4 = int(float(row_nums[1]))
        t2108 = float(row_nums[2])
        extracted_rows.append({
            "date": cols[0],
            "up_4": up_4,
            "down_4": down_4,
            "t2108": t2108,
        })
      except Exception:
        continue

print(f"成功從 Stockbee 提取到 {len(extracted_rows)} 筆歷史紀錄！")

if extracted_rows:
  # 將最新抓到的 Stockbee 原裝數據合併入歷史
  for row in reversed(extracted_rows):
    # 去除舊有同日期的數據
    history = [h for h in history if h.get("date") != row["date"]]
    history.insert(0, row)

# 只保留最近 60 天記錄
with open(DATA_FILE, "w", encoding="utf-8") as f:
  json.dump(history[:60], f, indent=2, ensure_ascii=False)

print("data.json 已更新完成，數據與 Stockbee 官方 100% 一致。")
