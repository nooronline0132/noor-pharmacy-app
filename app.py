import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# 1. Basic Settings
FILE_NAME = "noor_ledger_final.csv"
PASSWORD = "noor786"

st.set_page_config(page_title="Noor Pharmacy", layout="centered")

# 2. Simple CSS (Taaki crash na ho)
st.markdown("""
<style>
    .stApp { background-color: #F1F6F9 !important; }
    .metric-box { background: white; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .cust-card { background: white; padding: 10px; border-radius: 8px; margin-bottom: 5px; border-left: 5px solid #1E88E5; }
</style>
""", unsafe_allow_html=True)

# 3. Login System
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.header("🔐 Noor Pharmacy")
    p = st.text_input("Enter PIN", type="password")
    if st.button("Login"):
        if p == PASSWORD: 
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# 4. Data Loading (Safe Method)
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
if 'view' not in st.session_state: st.session_state.view = "main"
if 'sel_cust' not in st.session_state: st.session_state.sel_cust = None

# 5. Calculations
df = st.session_state.data
if not df.empty:
    summary = df.groupby('Name').agg({'Debit':'sum', 'Credit':'sum'}).reset_index()
    summary['Bal'] = summary['Debit'] - summary['Credit']
    rec = summary[summary['Bal'] > 0]['Bal'].sum()
    pay = abs(summary[summary['Bal'] < 0]['Bal'].sum())
else:
    summary = pd.DataFrame(columns=['Name', 'Bal'])
    rec = 0; pay = 0

# --- MAIN SCREEN ---
if st.session_state.view == "main":
    st.title("🏥 Noor Pharmacy")
    
    # Top Metrics (Vyapar Style)
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="metric-box"><small>To Receive</small><br><b style="color:green; font-size:20px;">Rs {rec:,.0f}</b></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-box"><small>To Pay</small><br><b style="color:red; font-size:20px;">Rs {pay:,.0f}</b></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["👤 Customers", "📑 All Transactions"])
    
    with tab1:
        search = st.text_input("🔍 Search Name")
        names = summary['Name'].unique()
        if search: names = [n for n in names if search.lower() in str(n).lower()]
        
        for n in names:
            b = summary[summary['Name']==n]['Bal'].values[0]
            col_n, col_b = st.columns([3, 1])
            if col_n.button(f"👤 {n}", key=f"btn_{n}", use_container_width=True):
                st.session_state.sel_cust = n
                st.session_state.view = "detail"
                st.rerun()
            col_b.markdown(f"**{b:,.0f}**")

    with tab2:
        st.write("Recent Activity:")
        for _, row in df.iloc[::-1].head(15).iterrows():
            st.markdown(f'<div class="cust-card">{row["Name"]} - Rs {row["Debit"]+row["Credit"]} <br><small>{row["Date"]}</small></div>', unsafe_allow_html=True)

# --- DETAIL VIEW ---
elif st.session_state.view == "detail":
    name = st.session_state.sel_cust
    if st.button("← Back"): 
        st.session_state.view = "main"
        st.rerun()
    
    st.subheader(f"Customer: {name}")
    c_bal = summary[summary['Name']==name]['Bal'].values[0]
    st.markdown(f'<div class="metric-box" style="width:100%"><h2>Rs {c_bal:,.0f}</h2></div>', unsafe_allow_html=True)
    
    # History
    st.write("---")
    h = df[df['Name'] == name].iloc[::-1]
    for idx, row in h.iterrows():
        t = "↗️ Credit" if row['Debit'] > 0 else "↙️ Payment"
        st.write(f"**{row['Date']}** | {t}: Rs {row['Debit']+row['Credit']}")
        if st.button("🗑️ Del", key=f"d_{idx}"):
            st.session_state.data = df.drop(idx)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.rerun()

# --- ENTRY FORM ---
with st.sidebar:
    st.header("➕ New Entry")
    with st.form("f", clear_on_submit=True):
        u_name = st.text_input("Name", value=st.session_state.sel_cust if st.session_state.sel_cust else "")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Give Credit", "Take Payment"])
        if st.form_submit_button("SAVE"):
            dr, cr = (u_amt, 0.0) if "Credit" in u_type else (0.0, u_amt)
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": "Entry", "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.rerun()
