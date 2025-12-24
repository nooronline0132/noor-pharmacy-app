import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# --- BASIC CONFIG ---
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"

st.set_page_config(page_title="Noor Pharmacy Ledger", layout="centered")

# --- FORCE WHITE MODE CSS ---
st.markdown("""
<style>
    /* Sab kuch safaid aur saaf karne ke liye */
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #000000 !important; font-family: 'Arial', sans-serif !important; }
    
    /* Summary Cards (Version 40 Style) */
    .card { background: #F8F9FA; padding: 15px; border-radius: 12px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 10px; }
    .val-rec { color: #28A745; font-size: 24px; font-weight: bold; }
    .val-pay { color: #DC3545; font-size: 24px; font-weight: bold; }
    
    /* Input Fields Fix */
    input { background-color: #FFFFFF !important; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
def load_data():
    if os.path.exists(FILE_NAME):
        try:
            df = pd.read_csv(FILE_NAME)
            df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
            df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
            return df
        except:
            return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

if 'data' not in st.session_state: st.session_state.data = load_data()
df = st.session_state.data

# --- LOGO & CENTERED TITLE ---
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
if os.path.exists(LOGO_FILE): 
    st.image(LOGO_FILE, width=120)
st.markdown("<h2 style='margin:0;'>Noor Pharmacy</h2><p>Ledger / Udhar Book</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- TOP SUMMARY ---
if not df.empty:
    summary = df.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
    t_rec = summary[summary > 0].sum()
    t_pay = abs(summary[summary < 0].sum())
else:
    t_rec = 0; t_pay = 0

c1, c2 = st.columns(2)
c1.markdown(f'<div class="card"><small>To Receive</small><br><span class="val-rec">Rs {t_rec:,.0f}</span></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card"><small>To Pay</small><br><span class="val-pay">Rs {t_pay:,.0f}</span></div>', unsafe_allow_html=True)

# --- MAIN TABS ---
tab1, tab2 = st.tabs(["👤 Customers List", "➕ Add New Entry"])

with tab1:
    search = st.text_input("🔍 Search Customer")
    names = df["Name"].unique()
    if search:
        names = [n for n in names if search.lower() in str(n).lower()]
    
    for n in names:
        bal = df[df['Name']==n]['Debit'].sum() - df[df['Name']==n]['Credit'].sum()
        with st.expander(f"👤 {n} (Balance: {bal:,.0f})"):
            # WhatsApp Reminder
            wa_msg = f"Noor Pharmacy: Aapka balance Rs {bal} hai."
            st.link_button("🔔 WhatsApp Reminder", f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}")
            
            # History Table
            st.write("Transaction History:")
            st.table(df[df["Name"] == n].iloc[::-1][["Date", "Note", "Debit", "Credit"]])
            
            if st.button(f"Delete Account {n}", key=f"del_{n}"):
                st.session_state.data = df[df["Name"] != n]
                st.session_state.data.to_csv(FILE_NAME, index=False)
                st.rerun()

with tab2:
    st.markdown("### Nayi Entry Karein")
    with st.form("entry_form", clear_on_submit=True):
        u_name = st.text_input("Customer Name")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Udhaar Diya (Debit)", "Vasooli Hui (Credit)"])
        u_note = st.text_input("Note/Details")
        
        if st.form_submit_button("SAVE RECORD"):
            dr = u_amt if "Udhaar" in u_type else 0.0
            cr = u_amt if "Vasooli" in u_type else 0.0
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.success("Entry Saved!")
            st.rerun()
