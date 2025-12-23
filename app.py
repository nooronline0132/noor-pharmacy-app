import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Setup
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"

st.set_page_config(page_title="Noor Pharmacy", layout="centered")

# --- CUSTOM CSS (Mirroring Vyapar App) ---
st.markdown("""
<style>
    .stApp { background-color: #F1F6F9 !important; }
    .main-header { background: #FFFFFF; padding: 15px; border-bottom: 2px solid #E0E0E0; margin-bottom: 10px; }
    .summary-card { background: white; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #1E88E5; }
    .txn-card { background: white; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #E0E0E0; }
    .fab-bar { position: fixed; bottom: 0; left: 0; right: 0; background: white; padding: 15px; display: flex; justify-content: space-around; z-index: 1000; border-top: 1px solid #DDD; }
    .btn-take { background: #2196F3; color: white; border-radius: 25px; padding: 10px 20px; font-weight: bold; border:none; width: 45%; }
    .btn-give { background: #FF9800; color: white; border-radius: 25px; padding: 10px 20px; font-weight: bold; border:none; width: 45%; }
    .stTabs [data-baseweb="tab-list"] { gap: 50px; justify-content: center; }
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

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'view' not in st.session_state: st.session_state.view = "main"
if 'selected_cust' not in st.session_state: st.session_state.selected_cust = None

# --- HEADER ---
col1, col2 = st.columns([1, 4])
with col1:
    if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=60)
with col2:
    st.markdown("<h2 style='margin:0; color:#0D47A1;'>Noor Pharmacy</h2>", unsafe_allow_html=True)

# --- MAIN SCREEN ---
if st.session_state.view == "main":
    summary = st.session_state.data.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
    
    # Top Metrics
    m1, m2 = st.columns(2)
    m1.markdown(f'<div class="summary-card"><small>To Receive</small><br><b style="color:#2E7D32; font-size:18px;">Rs {summary[summary > 0].sum():,.0f}</b></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="summary-card" style="border-top-color:#E53935;"><small>To Pay</small><br><b style="color:#E53935; font-size:18px;">Rs {abs(summary[summary < 0].sum()):,.0f}</b></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["👤 Customers", "📑 All Transactions"])

    with tab1:
        search = st.text_input("🔍 Search Name...", placeholder="Name or Phone...")
        names = st.session_state.data["Name"].unique()
        if search: names = [n for n in names if search.lower() in n.lower()]
        
        for n in names:
            bal = summary.get(n, 0)
            with st.container():
                c_name, c_bal = st.columns([3, 1])
                if c_name.button(f"👤 {n}", key=f"cust_{n}", use_container_width=True):
                    st.session_state.selected_cust = n
                    st.session_state.view = "detail"
                    st.rerun()
                c_bal.markdown(f"<p style='margin-top:10px; font-weight:bold; color:{'#2E7D32' if bal>=0 else '#E53935'};'>{abs(bal):,.0f}</p>", unsafe_allow_html=True)

    with tab2:
        st.write("Recent Entries:")
        for _, row in st.session_state.data.iloc[::-1].head(15).iterrows():
            st.markdown(f'<div class="txn-card"><span>{row["Name"]}<br><small>{row["Date"]}</small></span><b>Rs {row["Debit"]+row["Credit"]:,.0f}</b></div>', unsafe_allow_html=True)

# --- CUSTOMER DETAIL VIEW ---
elif st.session_state.view == "detail":
    name = st.session_state.selected_cust
    if st.button("← Back"): 
        st.session_state.view = "main"
        st.rerun()
    
    st.markdown(f"### {name}")
    cust_df = st.session_state.data[st.session_state.data['Name'] == name]
    bal = cust_df['Debit'].sum() - cust_df['Credit'].sum()
    
    st.markdown(f'<div class="summary-card" style="width:100%"><small>Total Balance</small><h2>Rs {bal:,.0f}</h2></div>', unsafe_allow_html=True)
    
    # Action Row
    ac1, ac2 = st.columns(2)
    wa_msg = f"Noor Pharmacy: Aapka balance Rs {bal} hai."
    ac1.link_button("🔔 Remind", f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}")
    ac2.button("📄 Generate PDF")

    st.write("---")
    for _, row in cust_df.iloc[::-1].iterrows():
        icon = "↗️" if row['Debit'] > 0 else "↙️"
        color = "#FF9800" if row['Debit'] > 0 else "#2196F3"
        st.markdown(f"""
        <div class="txn-card">
            <div><span style="color:{color}; font-weight:bold;">{icon} {'Credit' if row['Debit']>0 else 'Payment'}</span><br><small>{row['Date']}</small></div>
            <div style="text-align:right;"><b>Rs {row['Debit'] if row['Debit']>0 else row['Credit']:,.0f}</b><br><small>{row['Note']}</small></div>
        </div>
        """, unsafe_allow_html=True)

# --- ENTRY FORM ---
with st.sidebar:
    st.markdown("### ➕ New Entry")
    with st.form("entry", clear_on_submit=True):
        u_name = st.text_input("Customer Name", value=st.session_state.selected_cust if st.session_state.selected_cust else "")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Give Credit (Udhaar)", "Take Payment (Vasooli)"])
        u_note = st.text_input("Note")
        if st.form_submit_button("Save"):
            dr, cr = (u_amt, 0.0) if "Credit" in u_type else (0.0, u_amt)
            new_r = {"Date": datetime.now().strftime("%d %b %I:%M %p"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False); st.rerun()
