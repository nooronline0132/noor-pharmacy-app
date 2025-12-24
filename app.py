import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# --- CONFIGURATION ---
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"

st.set_page_config(page_title="Noor Pharmacy", layout="centered")

# --- VERSION 40 SPECIAL CSS ---
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA !important; }
    .main-header { background-color: white; padding: 10px; border-radius: 0 0 20px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); text-align: center; }
    .card { background-color: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 10px; border: 1px solid #f0f0f0; }
    .metric-title { font-size: 14px; color: #666; font-weight: bold; }
    .metric-value { font-size: 22px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- DATA FUNCTIONS ---
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- HEADER & LOGO ---
if os.path.exists(LOGO_FILE):
    st.image(LOGO_FILE, width=100)
st.markdown("<h2 style='text-align:center; color:#0D47A1;'>Noor Pharmacy</h2>", unsafe_allow_html=True)

# --- CALCULATIONS ---
df = st.session_state.data
summary = df.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
to_receive = summary[summary > 0].sum()
to_pay = abs(summary[summary < 0].sum())

# --- TOP DASHBOARD ---
c1, c2 = st.columns(2)
with c1:
    st.markdown(f'<div class="card"><span class="metric-title">To Receive</span><br><span class="metric-value" style="color:#2E7D32;">Rs {to_receive:,.0f}</span></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="card"><span class="metric-title">To Pay</span><br><span class="metric-value" style="color:#C62828;">Rs {to_pay:,.0f}</span></div>', unsafe_allow_html=True)

# --- MAIN TABS ---
tab1, tab2 = st.tabs(["👤 Customers", "➕ Quick Entry"])

with tab1:
    search = st.text_input("🔍 Search Name")
    names = df["Name"].unique()
    if search:
        names = [n for n in names if search.lower() in n.lower()]
    
    for name in names:
        bal = summary.get(name, 0)
        with st.expander(f"👤 {name} (Rs {bal:,.0f})"):
            st.write(f"**Current Balance: Rs {bal:,.0f}**")
            
            # WhatsApp Reminder
            wa_msg = f"Noor Pharmacy: Aapka balance Rs {bal} hai."
            st.link_button("🔔 Send Reminder", f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}")
            
            # History
            cust_df = df[df["Name"] == name].iloc[::-1]
            st.dataframe(cust_df[["Date", "Note", "Debit", "Credit"]], hide_index=True)
            
            if st.button(f"Delete Records for {name}", key=f"del_{name}"):
                st.session_state.data = df[df["Name"] != name]
                st.session_state.data.to_csv(FILE_NAME, index=False)
                st.rerun()

with tab2:
    with st.form("entry_form", clear_on_submit=True):
        u_name = st.text_input("Customer Name")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Give Credit (Udhaar)", "Take Payment (Vasooli)"])
        u_note = st.text_input("Note")
        
        if st.form_submit_button("Save"):
            dr, cr = (u_amt, 0.0) if "Give" in u_type else (0.0, u_amt)
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.success("Entry Saved!")
            st.rerun()
