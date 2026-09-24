import json
import os
import re
from playwright.sync_api import sync_playwright

print('正在連線 Stockbee 讀取頁面結構...')

with sync_playwright() as p:
  browser = p.chromium.launch(headless=True)
  page = browser.new_page()
  page.goto('https://stockbee.blogspot.com/p/mm.html', timeout=60000)
  page.wait_for_load_state('networkidle')

  # 1. 抓取頁面所有文字
  text_content = page.inner_text('body')

  # 2. 抓取頁面所有 iframe 原始連結 (印出黎睇下到底藏在哪)
  iframes = page.locator('iframe').all()
  iframe_srcs = [
      ifr.get_attribute('src') for ifr in iframes if ifr.get_attribute('src')
  ]

  browser.close()

print('=== 【偵測到的所有 IFRAME 網址】 ===')
for src in iframe_srcs:
  print(src)

print('\n=== 【頁面主體文字預覽 (前 800 字)】 ===')
print(text_content[:800])
