import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Password & Files
PASSWORD = "noor786"
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"

st.set_page_config(page_title="Noor Pharmacy", layout="centered")

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🔐 Noor Pharmacy Login</h2>", unsafe_allow_html=True)
    user_pass = st.text_input("Password", type="password")
    if st.button("Login"):
        if user_pass == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("Ghalat Password!")
    st.stop()

# --- PREMIUM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, label { color: #1A237E !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .card { background: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 5px solid #0D47A1; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px; color: black !important; }
    .stMetric { background: #E3F2FD; padding: 15px; border-radius: 12px; text-align: center; }
    [data-testid="stMetricValue"] { color: #0D47A1 !important; font-size: 24px !important; font-weight: bold !important; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #0D47A1; color: white; border: none; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# Data Loader
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

def save_file(df, file): df.to_csv(file, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()

# --- HEADER WITH LOGO ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=80)
with col_r:
    st.markdown('<h1 style="margin-top:10px;">NOOR PHARMACY</h1>', unsafe_allow_html=True)

# --- METRICS ---
if not st.session_state.data.empty:
    summary = st.session_state.data.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
    receive = summary[summary > 0].sum()
    pay = abs(summary[summary < 0].sum())
else:
    receive = 0.0; pay = 0.0; summary = pd.Series()

m1, m2 = st.columns(2)
with m1: st.metric("KUL VASOOLI", f"Rs {receive:,.0f}")
with m2: st.metric("KUL ADAIGI", f"Rs {pay:,.0f}")

t1, t2 = st.tabs(["👤 CUSTOMERS", "➕ NEW ENTRY"])

with t1:
    search = st.text_input("🔍 Search Customer Name")
    names = st.session_state.data["Name"].unique()
    if search: names = [n for n in names if search.lower() in n.lower()]
    
    for name in names:
        bal = summary.get(name, 0)
        st.markdown(f'<div class="card"><b>{name}</b><br><span style="color:#D32F2F;">Balance: Rs {bal:,.0f}</span></div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        wa_msg = f"Assalam o Alaikum {name}, Noor Pharmacy se aapka balance Rs {bal} hai."
        wa_url = f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}"
        c1.markdown(f'🟢 [**WhatsApp**]({wa_url})')
        
        cust_df = st.session_state.data[st.session_state.data['Name'] == name]
        c2.download_button("📥 Report", data=cust_df.to_csv(index=False), file_name=f"{name}.csv", key=f"dl_{name}")
        
        with st.expander("📝 View / Edit History"):
            for idx, row in cust_df.iterrows():
                st.write(f"{row['Date']} | {row['Note']} | Rs {row['Debit'] if row['Debit']>0 else row['Credit']}")
                if st.button("❌ Delete", key=f"del_{idx}"):
                    st.session_state.data = st.session_state.data.drop(idx)
                    save_file(st.session_state.data, FILE_NAME); st.rerun()

with t2:
    with st.form("premium_entry", clear_on_submit=True):
        st.write("### Nayi Entry Karein")
        u_name = st.text_input("Naam")
        u_note = st.text_input("Detail")
        u_amt = st.number_input("Raqam", min_value=0.0)
        u_type = st.radio("Qisam", ["Udhaar Diya", "Vasooli Hui"])
        if st.form_submit_button("SAVE RECORD"):
            dr, cr = (u_amt, 0.0) if "Udhaar" in u_type else (0.0, u_amt)
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            save_file(st.session_state.data, FILE_NAME); st.rerun()
