import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# --- SETTINGS ---
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"
PASSWORD = "noor786"

st.set_page_config(page_title="Noor Pharmacy", layout="wide")

# --- CUSTOM CSS (Version 40 Style) ---
st.markdown("""
<style>
    .stApp { background-color: #F0F2F6 !important; }
    .header-box { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom: 25px; border-top: 5px solid #0D47A1; }
    .card { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; border: 1px solid #E0E0E0; }
    .metric-title { color: #5F6368; font-size: 14px; font-weight: bold; }
    .metric-value { font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<div class='header-box'><h2>🔐 Noor Pharmacy Login</h2></div>", unsafe_allow_html=True)
    if st.text_input("PIN", type="password") == PASSWORD:
        st.session_state.logged_in = True
        st.rerun()
    st.stop()

# --- DATA ---
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

if 'data' not in st.session_state: st.session_state.data = load_data()

# --- CALCULATIONS ---
df = st.session_state.data
if not df.empty:
    summary = df.groupby('Name').agg({'Debit': 'sum', 'Credit': 'sum'}).reset_index()
    summary['Balance'] = summary['Debit'] - summary['Credit']
    to_receive = summary[summary['Balance'] > 0]['Balance'].sum()
    to_pay = abs(summary[summary['Balance'] < 0]['Balance'].sum())
else:
    summary = pd.DataFrame(columns=['Name', 'Balance'])
    to_receive = 0; to_pay = 0

# --- HEADER & LOGO ---
with st.container():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=150)
        st.markdown(f"<h1 style='text-align:center; color:#0D47A1;'>NOOR PHARMACY</h1>", unsafe_allow_html=True)

# --- DASHBOARD ---
st.markdown("---")
m1, m2 = st.columns(2)
with m1:
    st.markdown(f'<div class="header-box"><span class="metric-title">KUL VASOOLI</span><br><span class="metric-value" style="color:green;">Rs {to_receive:,.0f}</span></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="header-box" style="border-top-color:red;"><span class="metric-title">KUL ADAIGI</span><br><span class="metric-value" style="color:red;">Rs {to_pay:,.0f}</span></div>', unsafe_allow_html=True)

# --- MAIN LAYOUT ---
col_list, col_entry = st.columns([2, 1])

with col_list:
    st.subheader("👤 Customer Ledger")
    search = st.text_input("🔍 Search Name...")
    
    display_names = summary['Name'].unique()
    if search: display_names = [n for n in display_names if search.lower() in str(n).lower()]
    
    for name in display_names:
        bal = summary[summary['Name'] == name]['Balance'].values[0]
        color = "green" if bal >= 0 else "red"
        
        with st.expander(f"👤 {name} (Balance: Rs {bal:,.0f})"):
            st.markdown(f"**Total Balance: <span style='color:{color};'>Rs {bal:,.0f}</span>**", unsafe_allow_html=True)
            wa_msg = f"Noor Pharmacy: Aapka balance Rs {bal} hai."
            st.link_button("🔔 Send WhatsApp", f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}")
            
            # Show Transactions
            cust_df = df[df['Name'] == name].iloc[::-1]
            st.table(cust_df[["Date", "Note", "Debit", "Credit"]])
            
            if st.button(f"Delete Customer {name}", key=f"del_{name}"):
                st.session_state.data = df[df['Name'] != name]
                st.session_state.data.to_csv(FILE_NAME, index=False)
                st.rerun()

with col_entry:
    st.subheader("➕ Nayi Entry")
    with st.form("main_form", clear_on_submit=True):
        u_name = st.text_input("Customer Name")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Udhaar Diya (Debit)", "Vasooli Hui (Credit)"])
        u_note = st.text_input("Note")
        if st.form_submit_button("SAVE ENTRY"):
            dr, cr = (u_amt, 0.0) if "Debit" in u_type else (0.0, u_amt)
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.success("Saved!")
            st.rerun()
