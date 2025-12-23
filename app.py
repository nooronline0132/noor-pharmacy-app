import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Files
FILE_NAME = "noor_ledger_final.csv"

st.set_page_config(page_title="Noor Pharmacy", layout="centered")

# --- LOGIN & STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'view' not in st.session_state: st.session_state.view = "list"
if 'selected_cust' not in st.session_state: st.session_state.selected_cust = None

# --- NEW PROFESSIONAL CSS ---
st.markdown("""
<style>
    .stApp { background-color: #EBF2F7 !important; } /* Light Blue-Grey Background */
    [data-testid="stHeader"] { background: #EBF2F7 !important; }
    
    /* Header Style */
    .app-header { background: white; padding: 15px; border-radius: 0 0 20px 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px; }
    
    /* Metric Cards */
    .m-container { display: flex; justify-content: space-between; margin-bottom: 20px; gap: 10px; }
    .m-card { background: white; padding: 15px; border-radius: 15px; width: 48%; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }
    
    /* Customer Card */
    .cust-btn { background: white !important; border: none !important; border-radius: 10px !important; padding: 15px !important; margin-bottom: 10px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.03) !important; color: black !important; text-align: left !important; width: 100%; border-bottom: 1px solid #eee !important; }
    
    /* FAB Buttons */
    .fab-fixed { position: fixed; bottom: 0; left: 0; width: 100%; background: white; padding: 15px; display: flex; justify-content: space-around; box-shadow: 0 -5px 15px rgba(0,0,0,0.05); z-index: 999; }
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

# --- WINDOW 1: LIST VIEW ---
if st.session_state.view == "list":
    st.markdown('<div class="app-header"><h3>Noor Pharmacy</h3></div>', unsafe_allow_html=True)
    
    # Metrics
    summary = st.session_state.data.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
    m1, m2 = st.columns(2)
    with m1: st.markdown(f'<div class="m-card"><small style="color:grey;">To Receive</small><br><b style="color:#2E7D32; font-size:20px;">Rs {summary[summary > 0].sum():,.0f}</b></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="m-card"><small style="color:grey;">To Pay</small><br><b style="color:#C62828; font-size:20px;">Rs {abs(summary[summary < 0].sum()):,.0f}</b></div>', unsafe_allow_html=True)

    st.write("")
    search = st.text_input("🔍 Search Name", placeholder="Customer ka naam likhein...")
    
    st.markdown("#### Customers")
    names = st.session_state.data["Name"].unique()
    if search: names = [n for n in names if search.lower() in n.lower()]
    
    for n in names:
        bal = summary.get(n, 0)
        # Using a container to make it look like a list item
        with st.container():
            c1, c2 = st.columns([3, 1])
            if c1.button(f"👤 {n}", key=f"sel_{n}"):
                st.session_state.selected_cust = n
                st.session_state.view = "detail"
                st.rerun()
            c2.markdown(f"<p style='margin-top:10px; font-weight:bold; color:{'green' if bal>=0 else 'red'};'>{abs(bal):,.0f}</p>", unsafe_allow_html=True)

# --- WINDOW 2: DETAIL VIEW ---
elif st.session_state.view == "detail":
    name = st.session_state.selected_cust
    st.markdown(f'<div class="app-header"><h3 style="display:inline;">{name}</h3></div>', unsafe_allow_html=True)
    if st.button("← Back"): 
        st.session_state.view = "list"
        st.rerun()
    
    cust_df = st.session_state.data[st.session_state.data['Name'] == name]
    bal = cust_df['Debit'].sum() - cust_df['Credit'].sum()
    
    st.markdown(f'<div class="m-card" style="width:100%"><small>Current Balance</small><h2>Rs {bal:,.0f}</h2></div>', unsafe_allow_html=True)
    
    st.write("---")
    for _, row in cust_df.iloc[::-1].iterrows():
        t_type = "↗️ Credit" if row['Debit'] > 0 else "↙️ Payment"
        st.markdown(f"**{row['Date']}**")
        st.markdown(f"{t_label} : **Rs {row['Debit'] if row['Debit']>0 else row['Credit']:,.0f}**")
        st.caption(f"Note: {row['Note']}")
        st.write("---")

# --- FLOATING ENTRY FORM ---
with st.sidebar:
    st.markdown("### ➕ Quick Entry")
    with st.form("quick_form", clear_on_submit=True):
        u_name = st.text_input("Customer", value=st.session_state.selected_cust if st.session_state.selected_cust else "")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Give Credit", "Take Payment"])
        if st.form_submit_button("Save"):
            dr, cr = (u_amt, 0.0) if u_type == "Give Credit" else (0.0, u_amt)
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": "Added", "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.success("Saved!")
            st.rerun()
