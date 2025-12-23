import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# --- BASIC SETTINGS ---
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"
PASSWORD = "noor786"

st.set_page_config(page_title="Noor Pharmacy", layout="wide")

# --- CLEAN CSS (White Background Fix) ---
st.markdown("""
<style>
    /* Sab se pehle background ko bilkul safaid aur saaf kar diya */
    .stApp { background-color: #FFFFFF !important; color: #000000 !important; }
    
    /* Metrics Boxes (Kul Vasooli / Kul Adaigi) */
    .metric-container { background: #F8F9FA; padding: 20px; border-radius: 15px; border: 1px solid #E0E0E0; text-align: center; }
    .rec-text { color: #2E7D32; font-size: 28px; font-weight: bold; }
    .pay-text { color: #D32F2F; font-size: 28px; font-weight: bold; }
    
    /* Input fields ko dark mode se bachane ke liye */
    input, select, textarea { background-color: #FFFFFF !important; color: #000000 !important; border: 1px solid #CCCCCC !important; }
    
    /* Buttons */
    .stButton>button { border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🔐 Noor Pharmacy Login</h2>", unsafe_allow_html=True)
    pw = st.text_input("Enter PIN", type="password")
    if st.button("Login"):
        if pw == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- DATA HANDLING ---
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

if 'data' not in st.session_state: st.session_state.data = load_data()

# --- HEADER WITH LOGO ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if os.path.exists(LOGO_FILE): 
        st.image(LOGO_FILE, width=150)
    st.markdown("<h1 style='text-align:center; color:#0D47A1;'>NOOR PHARMACY</h1>", unsafe_allow_html=True)

# --- CALCULATIONS ---
df = st.session_state.data
if not df.empty:
    summary = df.groupby('Name').agg({'Debit': 'sum', 'Credit': 'sum'}).reset_index()
    summary['Balance'] = summary['Debit'] - summary['Credit']
    total_rec = summary[summary['Balance'] > 0]['Balance'].sum()
    total_pay = abs(summary[summary['Balance'] < 0]['Balance'].sum())
else:
    summary = pd.DataFrame(columns=['Name', 'Balance'])
    total_rec = 0; total_pay = 0

# --- DASHBOARD METRICS ---
m1, m2 = st.columns(2)
m1.markdown(f'<div class="metric-container"><small>KUL VASOOLI (To Receive)</small><br><span class="rec-text">Rs {total_rec:,.0f}</span></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-container"><small>KUL ADAIGI (To Pay)</small><br><span class="pay-text">Rs {total_pay:,.0f}</span></div>', unsafe_allow_html=True)

st.divider()

# --- MAIN SCREEN (2 COLUMNS) ---
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("👤 Customer Records")
    search = st.text_input("🔍 Search Name (Naam Likhein)")
    
    unique_names = summary['Name'].unique()
    if search:
        unique_names = [n for n in unique_names if search.lower() in str(n).lower()]
    
    for name in unique_names:
        b = summary[summary['Name'] == name]['Balance'].values[0]
        color = "#2E7D32" if b >= 0 else "#D32F2F"
        
        with st.expander(f"👤 {name} (Balance: Rs {b:,.0f})"):
            st.markdown(f"**Customer: {name} | Current Balance: <span style='color:{color}; font-size:20px;'>Rs {b:,.0f}</span>**", unsafe_allow_html=True)
            
            # WhatsApp & PDF Action
            wa_msg = f"Assalam o Alaikum {name}, Noor Pharmacy se aapka balance Rs {b} hai."
            st.link_button("🔔 WhatsApp Reminder", f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}")
            
            # Show Detailed Table
            cust_entries = df[df['Name'] == name].iloc[::-1]
            st.dataframe(cust_entries[["Date", "Note", "Debit", "Credit"]], use_container_width=True, hide_index=True)
            
            if st.button(f"Delete Records for {name}", key=f"del_{name}"):
                st.session_state.data = df[df['Name'] != name]
                st.session_state.data.to_csv(FILE_NAME, index=False)
                st.rerun()

with right_col:
    st.subheader("➕ Nayi Entry")
    with st.form("entry_form", clear_on_submit=True):
        u_name = st.text_input("Customer Ka Naam")
        u_amt = st.number_input("Amount (Raqam)", min_value=0.0)
        u_type = st.radio("Entry Type", ["Udhaar Diya (Debit)", "Vasooli Hui (Credit)"])
        u_note = st.text_input("Note (Tafseel)")
        
        if st.form_submit_button("SAVE DATA"):
            dr = u_amt if "Debit" in u_type else 0.0
            cr = u_amt if "Credit" in u_type else 0.0
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.success("Entry Saved!")
            st.rerun()
