import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# --- SETTINGS ---
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"

st.set_page_config(page_title="Noor Pharmacy", layout="centered")

# --- VERSION 40 CLEAN CSS ---
st.markdown("""
<style>
    /* White Background and Dark Text */
    .stApp { background-color: #FFFFFF !important; }
    h2, h3, p, span, label { color: #1A202C !important; font-family: sans-serif !important; }
    
    /* Vyapar Style Summary Cards */
    .summary-card { background: #F7FAFC; padding: 15px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; margin-bottom: 10px; }
    .rec-val { color: #2F855A; font-size: 24px; font-weight: bold; }
    .pay-val { color: #C53030; font-size: 24px; font-weight: bold; }
    
    /* Force Buttons to be Visible */
    .stButton>button { border-radius: 10px !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

if 'data' not in st.session_state: st.session_state.data = load_data()
df = st.session_state.data

# --- LOGO & TITLE ---
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=120)
st.markdown("<h2 style='margin-top:0;'>Noor Pharmacy</h2>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- TOP STATS ---
if not df.empty:
    summary = df.groupby('Name').agg({'Debit': 'sum', 'Credit': 'sum'}).reset_index()
    summary['Bal'] = summary['Debit'] - summary['Credit']
    t_rec = summary[summary['Bal'] > 0]['Bal'].sum()
    t_pay = abs(summary[summary['Bal'] < 0]['Bal'].sum())
else:
    t_rec = 0; t_pay = 0

c1, c2 = st.columns(2)
c1.markdown(f'<div class="summary-card"><small>To Receive</small><br><span class="rec-val">Rs {t_rec:,.0f}</span></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="summary-card"><small>To Pay</small><br><span class="pay-val">Rs {t_pay:,.0f}</span></div>', unsafe_allow_html=True)

# --- TABS ---
t1, t2 = st.tabs(["👤 Customers", "➕ Nayi Entry"])

with t1:
    search = st.text_input("🔍 Search Name")
    unique_names = df["Name"].unique()
    if search: unique_names = [n for n in unique_names if search.lower() in n.lower()]
    
    for n in unique_names:
        b = summary[summary['Name'] == n]['Bal'].values[0]
        with st.expander(f"👤 {n} (Rs {b:,.0f})"):
            # WhatsApp Option
            wa_msg = f"Noor Pharmacy: Account Balance for {n} is Rs {b}"
            st.link_button("🔔 Send WhatsApp", f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}")
            
            # Transactions
            st.dataframe(df[df["Name"] == n].iloc[::-1][["Date", "Note", "Debit", "Credit"]], hide_index=True)
            
            if st.button(f"Delete Records of {n}", key=f"del_{n}"):
                st.session_state.data = df[df["Name"] != n]
                st.session_state.data.to_csv(FILE_NAME, index=False)
                st.rerun()

with t2:
    with st.form("entry_form", clear_on_submit=True):
        u_name = st.text_input("Customer Name")
        u_amt = st.number_input("Amount (Raqam)", min_value=0.0)
        u_type = st.radio("Type", ["Give Credit (Udhaar Diya)", "Take Payment (Vasooli)"])
        u_note = st.text_input("Note (Details)")
        
        if st.form_submit_button("SAVE DATA"):
            dr = u_amt if "Give" in u_type else 0.0
            cr = u_amt if "Take" in u_type else 0.0
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.success("Saved!")
            st.rerun()
