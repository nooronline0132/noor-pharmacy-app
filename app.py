import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Files Setup
FILE_NAME = "noor_ledger_final.csv"
CUST_FILE = "customer_details.csv"
IMG_DIR = "customer_images"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

def load_customers(ledger_df):
    df = pd.read_csv(CUST_FILE) if os.path.exists(CUST_FILE) else pd.DataFrame(columns=["Name", "Phone", "Address", "Image_Path"])
    l_names = ledger_df["Name"].unique().tolist()
    e_names = df["Name"].tolist()
    new_data = [{"Name": n, "Phone": "", "Address": "", "Image_Path": ""} for n in l_names if n not in e_names]
    if new_data: df = pd.concat([df, pd.DataFrame(new_data)], ignore_index=True)
    return df

def save_file(df, file): df.to_csv(file, index=False)

st.set_page_config(page_title="Noor Mobile", layout="wide")

# --- VISIBILITY FIX: Strong Black Text & White Background ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #000000 !important; }
    .main-title { font-size: 24px !important; text-align: center; color: #0D47A1 !important; font-weight: bold; padding: 10px; }
    .card { background: #f9f9f9; padding: 15px; border-radius: 12px; border: 2px solid #0D47A1; margin-bottom: 10px; color: black !important; }
    [data-testid="stMetricValue"] { color: #0D47A1 !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div { color: black !important; background-color: white !important; border: 1px solid #0D47A1 !important; }
</style>
""", unsafe_allow_html=True)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'custs' not in st.session_state: st.session_state.custs = load_customers(st.session_state.data)

st.markdown('<div class="main-title">🏥 NOOR PHARMACY MOBILE</div>', unsafe_allow_html=True)

# Top Summary
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
    search = st.text_input("🔍 Search Name (Yahan Likhein)")
    if st.session_state.custs.empty:
        st.warning("⚠️ Abhi koi record nahi hai. Niche 'NEW ENTRY' par click kar ke pehla banda add karein.")
    
    disp = st.session_state.custs
    if search: disp = disp[disp['Name'].str.contains(search, case=False)]
    
    for idx, r in disp.iterrows():
        with st.container():
            st.markdown(f'<div class="card"><b>NAME: {r["Name"]}</b>', unsafe_allow_html=True)
            bal = summary.get(r['Name'], 0)
            st.write(f"💰 **BALANCE: Rs {bal:,.0f}**")
            
            c1, c2 = st.columns(2)
            msg = f"Assalam o Alaikum {r['Name']}, Aapka balance Rs {bal} hai."
            wa_url = f"https://web.whatsapp.com/send?text={urllib.parse.quote(msg)}"
            c1.markdown(f'🟢 [**WhatsApp**]({wa_url})')
            
            cust_ledger = st.session_state.data[st.session_state.data['Name'] == r['Name']]
            csv_data = cust_ledger.to_csv(index=False).encode('utf-8')
            c2.download_button("📥 Report", data=csv_data, file_name=f"{r['Name']}.csv", key=f"dl_{idx}")
            st.markdown('</div>', unsafe_allow_html=True)

with t2:
    st.markdown("### 📝 Nayi Entry Karein")
    with st.form("mobile_entry", clear_on_submit=True):
        if st.session_state.custs.empty:
            u_name = st.text_input("Customer ka Naam Likhein")
        else:
            u_name = st.selectbox("Purana Customer Chunien", st.session_state.custs['Name'].tolist())
            u_name_new = st.text_input("Ya Bilkul Naya Naam Likhein")
            if u_name_new: u_name = u_name_new
            
        u_note = st.text_input("Detail (Maslan: Panadol Tablet)")
        u_amt = st.number_input("Raqam (Amount)", min_value=0.0, step=10.0)
        u_type = st.radio("Entry ki Qisam", ["Udhaar Diya", "Vasooli Hui"])
        
        if st.form_submit_button("✅ SAVE RECORD"):
            dr = u_amt if "Udhaar" in u_type else 0.0
            cr = u_amt if "Vasooli" in u_type else 0.0
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            if u_name not in st.session_state.custs['Name'].tolist():
                new_c = pd.DataFrame([{"Name": u_name, "Phone": "", "Address": "", "Image_Path": ""}])
                st.session_state.custs = pd.concat([st.session_state.custs, new_c], ignore_index=True)
                save_file(st.session_state.custs, CUST_FILE)
            save_file(st.session_state.data, FILE_NAME); st.rerun()
