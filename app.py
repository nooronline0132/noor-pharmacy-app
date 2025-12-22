import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Password
PASSWORD = "noor786" 

# Files Setup
FILE_NAME = "noor_ledger_final.csv"
CUST_FILE = "customer_details.csv"

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- LOGIN PAGE ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🔐 Noor Pharmacy Login</h2>", unsafe_allow_html=True)
    user_pass = st.text_input("Password Daalain", type="password")
    if st.button("Login"):
        if user_pass == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("Ghalat Password!")
    st.stop()

# --- MAIN APP ---
st.markdown("<style>.stApp{background-color:white;} h1,h2,h3,p,span,label{color:black !important;}</style>", unsafe_allow_html=True)

# Logout Button (Top Right)
if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.rerun()

def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

def load_customers(ledger_df):
    if os.path.exists(CUST_FILE): df = pd.read_csv(CUST_FILE)
    else: df = pd.DataFrame(columns=["Name", "Phone", "Address", "Image_Path"])
    l_names = ledger_df["Name"].unique().tolist()
    e_names = df["Name"].tolist()
    new_data = [{"Name": n, "Phone": "", "Address": "", "Image_Path": ""} for n in l_names if n not in e_names]
    if new_data: df = pd.concat([df, pd.DataFrame(new_data)], ignore_index=True)
    return df

def save_file(df, file): df.to_csv(file, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'custs' not in st.session_state: st.session_state.custs = load_customers(st.session_state.data)

st.markdown('<h2 style="text-align:center; color:#0D47A1;">🏥 NOOR PHARMACY MOBILE</h2>', unsafe_allow_html=True)

# Summary Cards
if not st.session_state.data.empty:
    summary = st.session_state.data.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
    receive = summary[summary > 0].sum()
    pay = abs(summary[summary < 0].sum())
else:
    receive = 0.0; pay = 0.0; summary = pd.Series()

m1, m2 = st.columns(2)
m1.metric("KUL VASOOLI", f"Rs {receive:,.0f}")
m2.metric("KUL ADAIGI", f"Rs {pay:,.0f}")

t1, t2 = st.tabs(["👤 CUSTOMERS", "➕ NEW ENTRY"])

with t1:
    search = st.text_input("🔍 Search Name")
    disp = st.session_state.custs
    if search: disp = disp[disp['Name'].str.contains(search, case=False)]
    
    for idx, r in disp.iterrows():
        with st.container():
            st.markdown(f'<div style="border:2px solid #0D47A1; padding:10px; border-radius:10px; margin-bottom:10px; color:black;"><b>NAME: {r["Name"]}</b>', unsafe_allow_html=True)
            bal = summary.get(r['Name'], 0) if not summary.empty else 0
            st.write(f"💰 **BALANCE: Rs {bal:,.0f}**")
            
            c1, c2 = st.columns(2)
            msg = f"Assalam o Alaikum {r['Name']}, Aapka balance Rs {bal} hai. Noor Pharmacy."
            wa_url = f"https://web.whatsapp.com/send?text={urllib.parse.quote(msg)}"
            c1.markdown(f'🟢 [**WhatsApp**]({wa_url})')
            
            ledger = st.session_state.data[st.session_state.data['Name'] == r['Name']]
            csv_data = ledger.to_csv(index=False).encode('utf-8')
            c2.download_button("📥 Report", data=csv_data, file_name=f"{r['Name']}.csv", key=f"dl_{idx}")
            st.markdown('</div>', unsafe_allow_html=True)

with t2:
    with st.form("mobile_entry", clear_on_submit=True):
        st.write("### 📝 Nayi Entry")
        u_name = st.text_input("Naam")
        u_note = st.text_input("Detail")
        u_amt = st.number_input("Raqam", min_value=0.0)
        u_type = st.radio("Type", ["Udhaar Diya", "Vasooli Hui"])
        if st.form_submit_button("✅ SAVE"):
            dr = u_amt if "Udhaar" in u_type else 0.0
            cr = u_amt if "Vasooli" in u_type else 0.0
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            if u_name not in st.session_state.custs['Name'].tolist():
                new_c = pd.DataFrame([{"Name": u_name, "Phone": "", "Address": "", "Image_Path": ""}])
                st.session_state.custs = pd.concat([st.session_state.custs, new_c], ignore_index=True)
                save_file(st.session_state.custs, CUST_FILE)
            save_file(st.session_state.data, FILE_NAME); st.rerun()
