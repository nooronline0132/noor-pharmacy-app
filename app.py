import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Files
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"

st.set_page_config(page_title="Noor Pharmacy", layout="centered")

# --- LOGIN & STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'view' not in st.session_state: st.session_state.view = "list" # views: list, detail, entry
if 'selected_cust' not in st.session_state: st.session_state.selected_cust = None
if 'entry_type' not in st.session_state: st.session_state.entry_type = None

# --- CSS (Professional Look) ---
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC !important; }
    .header { display: flex; align-items: center; padding: 10px; background: white; border-bottom: 1px solid #E2E8F0; margin-bottom: 10px; }
    .m-card { background: white; border-radius: 10px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }
    .cust-row { background: white; padding: 15px; border-bottom: 1px solid #F1F5F9; display: flex; justify-content: space-between; cursor: pointer; }
    .fab-container { position: fixed; bottom: 20px; left: 0; right: 0; display: flex; justify-content: center; gap: 15px; padding: 0 20px; z-index: 999; }
    .btn-blue { background-color: #2196F3; color: white; padding: 12px; border-radius: 25px; border: none; width: 45%; font-weight: bold; }
    .btn-orange { background-color: #FF9800; color: white; padding: 12px; border-radius: 25px; border: none; width: 45%; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

if 'data' not in st.session_state: st.session_state.data = load_data()

# --- NAVIGATION LOGIC ---
def go_to_list(): 
    st.session_state.view = "list"
    st.rerun()

def go_to_detail(name):
    st.session_state.selected_cust = name
    st.session_state.view = "detail"
    st.rerun()

def go_to_entry(etype):
    st.session_state.entry_type = etype
    st.session_state.view = "entry"
    st.rerun()

# --- WINDOW 1: CUSTOMER LIST ---
if st.session_state.view == "list":
    # Header & Metrics
    st.markdown("### Noor Pharmacy")
    summary = st.session_state.data.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
    
    m1, m2 = st.columns(2)
    m1.markdown(f'<div class="m-card"><small>To Receive</small><br><b style="color:green; font-size:18px;">Rs {summary[summary > 0].sum():,.0f}</b></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="m-card"><small>To Pay</small><br><b style="color:red; font-size:18px;">Rs {abs(summary[summary < 0].sum()):,.0f}</b></div>', unsafe_allow_html=True)

    search = st.text_input("🔍 Search Name...", placeholder="Waseem, Arshad...")
    names = st.session_state.data["Name"].unique()
    if search: names = [n for n in names if search.lower() in n.lower()]
    
    st.write("---")
    for n in names:
        bal = summary.get(n, 0)
        col_n, col_b = st.columns([3, 1])
        if col_n.button(f"👤 {n}", key=f"btn_{n}", use_container_width=True):
            go_to_detail(n)
        col_b.markdown(f"**{bal:,.0f}**")

# --- WINDOW 2: CUSTOMER DETAIL (LEDGER) ---
elif st.session_state.view == "detail":
    name = st.session_state.selected_cust
    if st.button("← Back to List"): go_to_list()
    
    st.markdown(f"## {name}")
    cust_bal = st.session_state.data[st.session_state.data['Name'] == name].apply(lambda x: x['Debit'] - x['Credit'], axis=1).sum()
    st.markdown(f'<div class="m-card"><small>Total Balance</small><h2>Rs {cust_bal:,.0f}</h2></div>', unsafe_allow_html=True)
    
    st.write("### Transaction History")
    history = st.session_state.data[st.session_state.data['Name'] == name].iloc[::-1]
    for _, row in history.iterrows():
        t_label = "↗️ Credit" if row['Debit'] > 0 else "↙️ Payment"
        t_amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
        st.markdown(f"**{row['Date']}** | {t_label}: **Rs {t_amt:,.0f}**")
        st.caption(f"Note: {row['Note']}")
        st.write("---")

# --- WINDOW 3: ENTRY WINDOW ---
elif st.session_state.view == "entry":
    etype = st.session_state.entry_type
    st.markdown(f"### ← {etype}")
    with st.form("entry_form"):
        u_name = st.text_input("Customer Name", value=st.session_state.selected_cust if st.session_state.selected_cust else "")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_note = st.text_input("Note (Optional)")
        if st.form_submit_button("SAVE TRANSACTION"):
            dr, cr = (u_amt, 0.0) if "Credit" in etype else (0.0, u_amt)
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            go_to_list()

# --- FLOATING BUTTONS (On List & Detail) ---
if st.session_state.view != "entry":
    st.markdown("""<div style="height:80px;"></div>""", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("↙️ Take Payment", key="main_take"): go_to_entry("Take Payment")
    if c2.button("↗️ Give Credit", key="main_give"): go_to_entry("Give Credit")
