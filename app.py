import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Setup
FILE_NAME = "noor_ledger_final.csv"
LOGO_FILE = "Noor Pharmacy logo.jpg"

st.set_page_config(page_title="Noor Pharmacy", layout="centered")

# --- LOGIN ---
PASSWORD = "noor786"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🔐 Noor Pharmacy Login</h2>", unsafe_allow_html=True)
    if st.text_input("PIN", type="password") == PASSWORD:
        st.session_state.logged_in = True
        st.rerun()
    st.stop()

# --- CSS (Professional & Clear) ---
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC !important; }
    .main-title { color: #1E3A8A; text-align: center; font-weight: bold; margin-bottom: 20px; }
    .m-card { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; border-bottom: 4px solid #3B82F6; }
    .cust-row { background: white; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #E2E8F0; }
    .txn-card { background: white; padding: 10px; border-radius: 8px; margin-bottom: 5px; border-left: 5px solid #3B82F6; }
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
if 'view' not in st.session_state: st.session_state.view = "main"
if 'sel_cust' not in st.session_state: st.session_state.sel_cust = None

# Header
st.markdown('<h2 class="main-title">🏥 NOOR PHARMACY</h2>', unsafe_allow_html=True)

# --- CALCULATIONS (Fixed Error Here) ---
data = st.session_state.data
if not data.empty:
    # Safely group and calculate balance
    cust_totals = data.groupby('Name').agg({'Debit': 'sum', 'Credit': 'sum'}).reset_index()
    cust_totals['Balance'] = cust_totals['Debit'] - cust_totals['Credit']
    to_receive = cust_totals[cust_totals['Balance'] > 0]['Balance'].sum()
    to_pay = abs(cust_totals[cust_totals['Balance'] < 0]['Balance'].sum())
else:
    cust_totals = pd.DataFrame(columns=['Name', 'Debit', 'Credit', 'Balance'])
    to_receive = 0.0
    to_pay = 0.0

# --- MAIN SCREEN ---
if st.session_state.view == "main":
    # Metrics
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="m-card"><small>To Receive</small><br><b style="color:green; font-size:20px;">Rs {to_receive:,.0f}</b></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="m-card" style="border-bottom-color:red;"><small>To Pay</small><br><b style="color:red; font-size:20px;">Rs {to_pay:,.0f}</b></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["👤 Customers", "📑 History"])
    
    with tab1:
        search = st.text_input("🔍 Search Customer")
        display_df = cust_totals
        if search: display_df = display_df[display_df['Name'].str.contains(search, case=False)]
        
        for _, row in display_df.iterrows():
            col_a, col_b = st.columns([3, 1])
            if col_a.button(f"👤 {row['Name']}", key=f"btn_{row['Name']}", use_container_width=True):
                st.session_state.sel_cust = row['Name']
                st.session_state.view = "detail"
                st.rerun()
            col_b.markdown(f"**{row['Balance']:,.0f}**")

    with tab2:
        st.write("Recent Entries:")
        for _, row in data.iloc[::-1].head(10).iterrows():
            st.markdown(f'<div class="cust-row"><span>{row["Name"]}<br><small>{row["Date"]}</small></span><b>Rs {row["Debit"]+row["Credit"]:,.0f}</b></div>', unsafe_allow_html=True)

# --- DETAIL VIEW ---
elif st.session_state.view == "detail":
    name = st.session_state.sel_cust
    if st.button("← Wapis Jayein"): 
        st.session_state.view = "main"
        st.rerun()
    
    cust_bal = cust_totals[cust_totals['Name'] == name]['Balance'].values[0]
    st.markdown(f'<div class="m-card" style="width:100%;"><h3>{name}</h3><small>Balance</small><h2>Rs {cust_bal:,.0f}</h2></div>', unsafe_allow_html=True)
    
    # WhatsApp Reminder
    wa_msg = f"Assalam o Alaikum {name}, Noor Pharmacy se aapka balance Rs {cust_bal} hai."
    st.link_button("🔔 WhatsApp Reminder", f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}")
    
    st.write("---")
    hist = data[data['Name'] == name].iloc[::-1]
    for idx, row in hist.iterrows():
        t_label = "↗️ Credit (Diya)" if row['Debit'] > 0 else "↙️ Payment (Mila)"
        st.markdown(f"**{row['Date']}**")
        st.markdown(f"{t_label}: **Rs {row['Debit'] if row['Debit']>0 else row['Credit']:,.0f}**")
        if st.button("🗑️ Delete", key=f"del_{idx}"):
            st.session_state.data = data.drop(idx)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.rerun()
        st.write("---")

# --- ENTRY SIDEBAR ---
with st.sidebar:
    st.image(LOGO_FILE) if os.path.exists(LOGO_FILE) else st.write("Noor Pharmacy")
    st.header("➕ Nayi Entry")
    with st.form("entry_form", clear_on_submit=True):
        u_name = st.text_input("Customer Naam", value=st.session_state.sel_cust if st.session_state.sel_cust else "")
        u_amt = st.number_input("Raqam", min_value=0.0)
        u_type = st.radio("Type", ["Udhaar Diya", "Vasooli Hui"])
        u_note = st.text_input("Note")
        if st.form_submit_button("SAVE"):
            dr, cr = (u_amt, 0.0) if "Udhaar" in u_type else (0.0, u_amt)
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False); st.rerun()
