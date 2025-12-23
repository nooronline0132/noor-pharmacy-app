import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
import base64

# --- SETTINGS ---
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"
PASSWORD = "noor786"

# Page Configuration for Desktop
st.set_page_config(page_title="Noor Pharmacy Ledger Book", layout="wide")

# --- ADVANCED CLEAN CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        font-family: 'Roboto', sans-serif;
    }
    
    .stApp { color: #2C3E50 !important; }

    /* Centered Header & Logo */
    .header-container { text-align: center; padding: 20px; }
    .main-title { color: #0D47A1; font-size: 36px; font-weight: bold; margin-bottom: 5px; }
    .sub-title { color: #546E7A; font-size: 18px; margin-bottom: 20px; }

    /* Summary Cards */
    .card-box { 
        background: #F8F9FA; 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid #E0E0E0; 
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .text-rec { color: #2E7D32; font-size: 26px; font-weight: bold; }
    .text-pay { color: #D32F2F; font-size: 26px; font-weight: bold; }

    /* Buttons Fix */
    .stButton>button {
        border-radius: 8px;
        transition: 0.3s;
    }
    
    /* Make everything visible in Light Mode */
    p, span, label, h1, h2, h3 { color: #1B2631 !important; }
    
    /* Table Styling */
    .styled-table { width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 0.9em; min-width: 400px; }
</style>
""", unsafe_allow_html=True)

# --- FUNCTIONS ---
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

if 'data' not in st.session_state: st.session_state.data = load_data()

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<div class='header-container'><h1>🔐 Secure Login</h1></div>", unsafe_allow_html=True)
    if st.text_input("Enter PIN", type="password") == PASSWORD:
        st.session_state.logged_in = True
        st.rerun()
    st.stop()

# --- HEADER (Centered Logo & Title) ---
st.markdown("<div class='header-container'>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=150)
    st.markdown("<div class='main-title'>NOOR PHARMACY</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Udhar Book / Ledger System</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- CALCULATIONS ---
df = st.session_state.data
if not df.empty:
    summary = df.groupby('Name').agg({'Debit': 'sum', 'Credit': 'sum'}).reset_index()
    summary['Bal'] = summary['Debit'] - summary['Credit']
    t_rec = summary[summary['Bal'] > 0]['Bal'].sum()
    t_pay = abs(summary[summary['Bal'] < 0]['Bal'].sum())
else:
    summary = pd.DataFrame(columns=['Name', 'Bal']); t_rec = 0; t_pay = 0

# --- METRICS ---
m1, m2 = st.columns(2)
m1.markdown(f'<div class="card-box"><small>TOTAL TO RECEIVE</small><br><span class="text-rec">Rs {t_rec:,.0f}</span></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="card-box"><small>TOTAL TO PAY</small><br><span class="text-pay">Rs {t_pay:,.0f}</span></div>', unsafe_allow_html=True)

st.divider()

# --- MAIN APP LAYOUT ---
col_list, col_entry = st.columns([2, 1])

with col_list:
    st.subheader("📋 Customer Ledger Records")
    search = st.text_input("🔍 Search Customer Name", placeholder="Start typing...")
    
    unique_names = summary['Name'].unique()
    if search:
        unique_names = [n for n in unique_names if search.lower() in str(n).lower()]
    
    for name in unique_names:
        b = summary[summary['Name'] == name]['Bal'].values[0]
        color = "#2E7D32" if b >= 0 else "#D32F2F"
        
        with st.expander(f"👤 {name} (Balance: Rs {b:,.0f})"):
            # Customer Header Detail
            st.markdown(f"### Customer: {name}")
            st.markdown(f"**Current Balance:** <span style='color:{color}; font-size:22px;'>Rs {b:,.0f}</span>", unsafe_allow_html=True)
            
            # Action Buttons Row
            b1, b2, b3 = st.columns(3)
            wa_msg = f"Noor Pharmacy: Account Balance for {name} is Rs {b:,.0f}"
            b1.link_button("🔔 WhatsApp", f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}")
            
            # Data View & Edit/Delete Section
            cust_df = df[df['Name'] == name].iloc[::-1]
            st.write("---")
            st.markdown("**Transaction History & Edit Options:**")
            
            for idx, row in cust_df.iterrows():
                with st.container():
                    r1, r2, r3, r4 = st.columns([2, 2, 1, 1])
                    r1.write(f"{row['Date']}")
                    r2.write(f"{'↙️ Mila' if row['Credit']>0 else '↗️ Diya'}: Rs {row['Credit']+row['Debit']}")
                    
                    if r3.button("📝 Edit", key=f"edit_{idx}"):
                        st.info(f"Edit feature: Please update the form on the right for {name}.")
                    
                    if r4.button("🗑️ Del", key=f"del_{idx}"):
                        st.session_state.data = df.drop(idx)
                        st.session_state.data.to_csv(FILE_NAME, index=False)
                        st.rerun()
            st.write("---")

with col_entry:
    st.subheader("➕ Nayi Entry / Edit")
    with st.form("ledger_form", clear_on_submit=True):
        u_name = st.text_input("Customer Name")
        u_amt = st.number_input("Amount (Rs)", min_value=0.0)
        u_type = st.radio("Entry Type", ["↗️ Give Credit (Udhar Diya)", "↙️ Take Payment (Vasooli)"])
        u_note = st.text_input("Note / Bill Number")
        
        if st.form_submit_button("SAVE TRANSACTION"):
            dr = u_amt if "Give" in u_type else 0.0
            cr = u_amt if "Take" in u_type else 0.0
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.success(f"Entry for {u_name} saved!")
            st.rerun()

    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()
