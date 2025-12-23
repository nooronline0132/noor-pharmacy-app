import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Files & Logo
PASSWORD = "noor786"
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"

st.set_page_config(page_title="Noor Pharmacy", layout="centered")

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🔐 Noor Pharmacy</h2>", unsafe_allow_html=True)
    user_pass = st.text_input("PIN", type="password")
    if st.button("Enter"):
        if user_pass == PASSWORD: st.session_state.logged_in = True; st.rerun()
    st.stop()

# --- ADVANCED UI CSS (Mirroring Your Image) ---
st.markdown(f"""
<style>
    .stApp {{ background-color: #F7F9FC !important; }}
    .metric-container {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }}
    .metric-card {{ background: white; padding: 15px; border-radius: 15px; width: 48%; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; border: 1px solid #E1E8F0; }}
    .metric-label {{ color: #78909C; font-size: 14px; margin-bottom: 5px; }}
    .metric-value {{ font-size: 18px; font-weight: bold; }}
    .cust-card {{ background: white; padding: 12px 15px; border-bottom: 1px solid #EDF2F7; display: flex; justify-content: space-between; align-items: center; }}
    .cust-name {{ font-size: 16px; font-weight: 500; color: #2D3748; margin: 0; }}
    .cust-date {{ font-size: 12px; color: #A0AEC0; margin: 0; }}
    .cust-bal-green {{ color: #38A169; font-weight: bold; font-size: 16px; }}
    .cust-bal-red {{ color: #E53E3E; font-weight: bold; font-size: 16px; }}
    .action-bar {{ position: fixed; bottom: 20px; left: 0; right: 0; display: flex; justify-content: center; gap: 10px; padding: 0 20px; z-index: 100; }}
    .btn-take {{ background-color: #3182CE; color: white; padding: 12px 20px; border-radius: 30px; border: none; font-weight: bold; flex: 1; }}
    .btn-give {{ background-color: #ED8936; color: white; padding: 12px 20px; border-radius: 30px; border: none; font-weight: bold; flex: 1; }}
</style>
""", unsafe_allow_html=True)

# Data Functions
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

if 'data' not in st.session_state: st.session_state.data = load_data()

# --- HEADER ---
c1, c2 = st.columns([1, 5])
with c1: 
    if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=60)
with c2: st.markdown("<h3 style='margin-top:10px;'>Noor Pharmacy</h3>", unsafe_allow_html=True)

# --- TOP SUMMARY CARDS ---
if not st.session_state.data.empty:
    summary = st.session_state.data.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
    receive = summary[summary > 0].sum()
    pay = abs(summary[summary < 0].sum())
else: receive = 0; pay = 0; summary = pd.Series()

st.markdown(f"""
<div class="metric-container">
    <div class="metric-card">
        <div class="metric-label">To Receive</div>
        <div class="metric-value" style="color: #38A169;">Rs {receive:,.0f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">To Pay</div>
        <div class="metric-value" style="color: #E53E3E;">Rs {pay:,.0f}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- CUSTOMER LIST ---
search = st.text_input("🔍 Search Name or Phone Number", label_visibility="collapsed", placeholder="Search Name...")
names = st.session_state.data["Name"].unique()
if search: names = [n for n in names if search.lower() in n.lower()]

for name in names:
    bal = summary.get(name, 0)
    bal_style = "cust-bal-green" if bal >= 0 else "cust-bal-red"
    
    # Customer Row
    st.markdown(f"""
    <div class="cust-card">
        <div>
            <p class="cust-name">{name}</p>
            <p class="cust-date">Last updated: {datetime.now().strftime('%d Dec')}</p>
        </div>
        <div class="{bal_style}">Rs {abs(bal):,.0f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Hidden Actions (Click to Expand)
    with st.expander("Details & WhatsApp"):
        c1, c2 = st.columns(2)
        wa_url = f"https://web.whatsapp.com/send?text=Assalam o Alaikum {name}, Aapka balance Rs {bal} hai."
        c1.markdown(f'[🔔 WhatsApp]({wa_url})')
        if c2.button("🗑️ Delete", key=f"del_{name}"):
            st.session_state.data = st.session_state.data[st.session_state.data["Name"] != name]
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.rerun()

# --- FLOATING ACTION BUTTONS ---
st.markdown("""
<div class="action-bar">
    <button class="btn-take">↙️ Take Payment</button>
    <button class="btn-give">↗️ Give Credit</button>
</div>
""", unsafe_allow_html=True)

# Nayi Entry Form (Tabs as per Image)
st.markdown("---")
with st.expander("➕ Add New Transaction"):
    with st.form("quick_add", clear_on_submit=True):
        u_name = st.text_input("Customer Name")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Udhaar Diya", "Vasooli Hui"], horizontal=True)
        if st.form_submit_button("Save"):
            dr, cr = (u_amt, 0.0) if "Udhaar" in u_type else (0.0, u_amt)
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": "Quick Entry", "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.rerun()
