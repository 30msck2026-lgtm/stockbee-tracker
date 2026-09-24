from playwright.sync_api import sync_playwright

SHEET_URL = "https://docs.google.com/spreadsheet/pub?key=0Am_cU8NLIU20dEhiQnVEN3Nnc3B1S3J6eGhKZFowN3c&output=html&widget=true"

print("載入試算表並讀取內容...")
with sync_playwright() as p:
  browser = p.chromium.launch(headless=True)
  page = browser.new_page()
  page.goto(SHEET_URL, timeout=60000)
  page.wait_for_load_state("networkidle")
  page.wait_for_timeout(3000)

  text = page.inner_text("body")
  browser.close()

print("=== 試算表目前顯示的所有內容 ===")
for i, line in enumerate(text.split("\n")):
  if line.strip():
    print(f"第 {i+1} 行: {line.strip()}")
