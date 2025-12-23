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

st.set_page_config(page_title="Noor Pharmacy", layout="wide", initial_sidebar_state="collapsed")

# --- FORCE WHITE MODE CSS ---
st.markdown("""
<style>
    /* Pure White Background for whole app */
    .stApp { background-color: #FFFFFF !important; color: #000000 !important; }
    
    /* Vyapar Style Header Boxes */
    .top-card { background: #F1F6F9; padding: 20px; border-radius: 12px; border: 1px solid #D1D9E0; text-align: center; }
    .val-rec { color: #2E7D32; font-size: 28px; font-weight: bold; }
    .val-pay { color: #D32F2F; font-size: 28px; font-weight: bold; }
    
    /* Force text to be black regardless of theme */
    h1, h2, h3, h4, h5, h6, p, label, span, div { color: #111111 !important; }
    
    /* Styling Buttons like Vyapar */
    .btn-credit { background-color: #FF9800 !important; color: white !important; border-radius: 20px !important; }
    .btn-payment { background-color: #2196F3 !important; color: white !important; border-radius: 20px !important; }
</style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🔐 Noor Pharmacy Login</h2>", unsafe_allow_html=True)
    if st.text_input("Security PIN", type="password") == PASSWORD:
        st.session_state.logged_in = True
        st.rerun()
    st.stop()

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

# --- HEADER SECTION ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=120)
    st.markdown("<h1 style='text-align:center;'>NOOR PHARMACY</h1>", unsafe_allow_html=True)

# --- TOP SUMMARY ---
if not df.empty:
    summary = df.groupby('Name').agg({'Debit': 'sum', 'Credit': 'sum'}).reset_index()
    summary['Bal'] = summary['Debit'] - summary['Credit']
    rec = summary[summary['Bal'] > 0]['Bal'].sum()
    pay = abs(summary[summary['Bal'] < 0]['Bal'].sum())
else:
    summary = pd.DataFrame(columns=['Name', 'Bal']); rec = 0; pay = 0

m1, m2 = st.columns(2)
m1.markdown(f'<div class="top-card"><small>TO RECEIVE (Vasooli)</small><br><span class="val-rec">Rs {rec:,.0f}</span></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="top-card"><small>TO PAY (Adaigi)</small><br><span class="val-pay">Rs {pay:,.0f}</span></div>', unsafe_allow_html=True)

st.markdown("---")

# --- MAIN LAYOUT ---
left, right = st.columns([2, 1])

with left:
    st.subheader("👤 Customers & Reports")
    search = st.text_input("🔍 Search Name (Naam Likhein)")
    
    names = summary['Name'].unique()
    if search: names = [n for n in names if search.lower() in str(n).lower()]
    
    for n in names:
        b_val = summary[summary['Name'] == n]['Bal'].values[0]
        with st.expander(f"👤 {n} (Rs {b_val:,.0f})"):
            # WhatsApp Link
            wa_msg = f"Noor Pharmacy: Account Balance for {n} is Rs {b_val}"
            st.link_button("🔔 Send WhatsApp Reminder", f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}")
            
            # Transactions Table
            st.write("Recent Activity:")
            cust_df = df[df['Name'] == n].iloc[::-1]
            st.table(cust_df[["Date", "Note", "Debit", "Credit"]])
            
            # Export CSV (Report)
            csv_data = cust_df.to_csv(index=False).encode('utf-8')
            st.download_button(f"📥 Download {n} Report", data=csv_data, file_name=f"{n}_Ledger.csv", key=f"dl_{n}")

with right:
    st.subheader("➕ New Entry")
    with st.form("entry_form", clear_on_submit=True):
        u_name = st.text_input("Customer Name")
        u_amt = st.number_input("Amount (Raqam)", min_value=0.0)
        u_type = st.radio("Type", ["Give Credit (Udhaar Diya)", "Take Payment (Vasooli)"])
        u_note = st.text_input("Note (Tafseel)")
        
        if st.form_submit_button("SAVE DATA"):
            dr = u_amt if "Give" in u_type else 0.0
            cr = u_amt if "Take" in u_type else 0.0
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.success("Saved Successfully!")
            st.rerun()

    # Clear/Logout Option
    st.write("---")
    if st.button("🚪 Logout System"):
        st.session_state.logged_in = False
        st.rerun()
