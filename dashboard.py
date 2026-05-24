import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

# --- Page Setup ---
st.set_page_config(page_title="MADE by asif khan monitor ", layout="wide")

if 'table_data' not in st.session_state:
    st.session_state.table_data = []

# --- Custom CSS ---
st.markdown("""
<style>
.stApp { background-color: #e8f5e9; }
.header-container { display: flex; align-items: center; background: bleu; padding: 15px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.table-header { display: grid; grid-template-columns: 0.5fr 1.5fr 1.5fr 1fr 1fr 1fr 1.5fr 0.8fr; background: #343a40; color: white; text-align: center; padding: 15px; border-radius: 10px 10px 0 0; font-weight: bold; font-size: 13px; }
.data-row { display: grid; grid-template-columns: 0.5fr 1.5fr 1.5fr 1fr 1fr 1fr 1.5fr 0.8fr; background: bleu; color: black; text-align: center; padding: 12px; border-bottom: 1px solid #eee; align-items: center; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="header-container">
    <div style="font-size: 50px; margin-right: 15px;">👤</div>
    <div style="flex-grow: 1;">
        <h2 style="margin:0; color: #222;">ASIF KHAN'S Dashboard</h2>
        <p style="margin:0; color: #666; font-size: 14px;">Made by ASIF KHAN</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 1. Scraper Settings ---
with st.container():
    st.write("⚙️ **Scraper Settings:**")
    s_col = st.columns(6)
    p_wait = s_col[0].number_input("Page Wait", value=2.0)
    pop_wait = s_col[1].number_input("Popup Wait", value=1.5)
    c_wait = s_col[2].number_input("Click Wait", value=0.5)
    l_apply = s_col[3].number_input("Loc. Apply", value=2.0)
    p_ignore = s_col[4].number_input("Price Ignore", value=0.5)
    if s_col[5].button("💾 Save Settings"):
        st.success("Settings Saved!")

# --- 2. Action Controls ---
r2 = st.columns([2, 1, 1, 1, 1.5])
url_input = r2[0].text_input("", placeholder="Paste Amazon URL here...", label_visibility="collapsed")
r2[1].button("🔵 Add Product")
uploaded_file = r2[2].file_uploader("Upload CSV", type=['csv'], label_visibility="collapsed")
r2[3].button("📂 Upload CSV")

# Export Logic
if st.session_state.table_data:
    df_export = pd.DataFrame(st.session_state.table_data)
    csv = df_export.to_csv(index=False).encode('utf-8')
    r2[4].download_button(label="📊 Export CSV", data=csv, file_name='limited_stock.csv', mime='text/csv')
else:
    r2[4].button("📊 Export CSV (Empty)", disabled=True)

# --- 3. Execution Controls ---
st.divider()
r3 = st.columns(5)
start_num = r3[0].number_input("Start #", value=1, min_value=1)
end_num_val = r3[1].text_input("End #", value="Last")
update_btn = r3[2].button("🗳️ Update All / Range", type="primary")

# --- Table Display ---
st.markdown("""<div class="table-header"><div>#</div><div>ASIN</div><div>SOURCE</div><div>SHEET PRICE</div><div>LIVE PRICE</div><div>DELIVERY</div><div>STOCK STATUS</div><div>ACTION</div></div>""", unsafe_allow_html=True)
table_area = st.empty()

def update_display():
    with table_area.container():
        for row in st.session_state.table_data:
            st.markdown(f"""
            <div class="data-row">
                <div>{row['id']}</div><div>{row['asin']}</div><div>Amazon</div>
                <div style="color:blue;">${row['sheet']}</div>
                <div style="color:red; font-weight:bold;">${row['live']}</div>
                <div>Free ✅</div>
                <div style="color:green; font-weight:bold;">{row['stock']}</div>
                <div><button style="width:100%; height:22px; font-size:10px;">Edit</button></div>
            </div>""", unsafe_allow_html=True)

update_display()

# --- Scraper Engine ---
if update_btn and uploaded_file:
    df = pd.read_csv(uploaded_file)
    real_end = len(df) if end_num_val.lower() == "last" else int(end_num_val)
    
    # Linux setup bina crash options ke
    options = Options()
    options.add_argument("--headless")  # Cloud par baghair window ke chalanay ke liye lazmi hai
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Streamlit Linux Server Driver setup
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        for i in range(start_num-1, real_end):
            try:
                _ = driver.window_handles
            except:
                st.error("⚠️ Browser window band ho gayi hai!")
                break

            row_data = df.iloc[i]
            link = str(row_data.iloc[2]) if len(row_data) > 2 else ""
            sheet_p = str(row_data.iloc[4]) if len(row_data) > 4 else "0.0"

            if "http" in link:
                try:
                    driver.get(link)
                    time.sleep(p_wait)
                    
                    p_text = driver.find_element(By.CSS_SELECTOR, "span.a-price span.a-offscreen").get_attribute("textContent")
                    live_p = re.sub(r'[^\d.]', '', p_text)
                    stock_text = driver.find_element(By.ID, "availability").text.strip()
                    asin = link.split("/dp/")[1].split("/")[0] if "/dp/" in link else "N/A"

                    st.session_state.table_data.append({
                        "id": i+1, "asin": asin, "sheet": sheet_p, 
                        "live": live_p, "stock": stock_text
                    })
                    update_display()
                except:
                    continue
    finally:
        driver.quit()
        st.success("Scraping mukamal asif khan!")
