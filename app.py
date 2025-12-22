import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Password & Files
PASSWORD = "noor786"
FILE_NAME = "noor_ledger_final.csv"
CUST_FILE = "customer_details.csv"

st.set_page_config(page_title="Noor Pharmacy", layout="wide")

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🔐 Noor Pharmacy Login</h2>", unsafe_allow_html=True)
    user_pass = st.text_input("Password", type="password")
    if st.button("Login"):
        if user_pass == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("Ghalat Password!")
    st.stop()

# --- CSS for Visibility ---
st.markdown("""
<style>
    .stApp { background-color: white !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: black !important; font-weight: 500; }
    .card { background: #f0f2f6; padding: 15px; border-radius: 12px; border: 2px solid #0D47A1; margin-bottom: 10px; color: black !important; }
    [data-testid="stMetricValue"] { color: #0D47A1 !important; font-weight: bold !important; font-size: 28px !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; }
</style>
""", unsafe_allow_html=True)

# Data Functions
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
        df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
        return df
    return pd.DataFrame(columns=["Date", "Name", "Note", "Debit", "Credit"])

def save_file(df, file): df.to_csv(file, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()

st.markdown('<h2 style="text-align:center; color:#0D47A1;">🏥 NOOR PHARMACY</h2>', unsafe_allow_html=True)

# --- Summary Metrics ---
if not st.session_state.data.empty:
    summary = st.session_state.data.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
    receive = summary[summary > 0].sum()
    pay = abs(summary[summary < 0].sum())
else:
    receive = 0.0; pay = 0.0; summary = pd.Series()

col1, col2 = st.columns(2)
col1.metric("KUL VASOOLI", f"Rs {receive:,.0f}")
col2.metric("KUL ADAIGI", f"Rs {pay:,.0f}")

t1, t2 = st.tabs(["👤 CUSTOMERS", "➕ NEW ENTRY"])

with t1:
    search = st.text_input("🔍 Search Customer")
    unique_names = st.session_state.data["Name"].unique()
    if search: unique_names = [n for n in unique_names if search.lower() in n.lower()]
    
    for name in unique_names:
        with st.container():
            bal = summary.get(name, 0)
            st.markdown(f'<div class="card"><b>{name}</b><br>Balance: Rs {bal:,.0f}</div>', unsafe_allow_html=True)
            
            # Action Buttons
            c1, c2 = st.columns(2)
            msg = f"Assalam o Alaikum {name}, Noor Pharmacy se aapka balance Rs {bal} hai."
            wa_url = f"https://web.whatsapp.com/send?text={urllib.parse.quote(msg)}"
            c1.markdown(f'🟢 [**WhatsApp**]({wa_url})')
            
            cust_data = st.session_state.data[st.session_state.data['Name'] == name]
            csv_data = cust_data.to_csv(index=False).encode('utf-8')
            c2.download_button("📥 Report", data=csv_data, file_name=f"{name}.csv", key=f"dl_{name}")

            # History with Edit/Delete (Raat Wala Style)
            with st.expander("📝 History / Edit / Delete"):
                for idx, row in cust_data.iterrows():
                    amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
                    st.write(f"📅 {row['Date']} | {row['Note']} | **Rs {amt}**")
                    
                    e1, e2 = st.columns(2)
                    if e1.button("✏️ Edit", key=f"ed_{idx}"): st.session_state.active_edit = idx
                    if e2.button("❌ Del", key=f"de_{idx}"):
                        st.session_state.data = st.session_state.data.drop(idx)
                        save_file(st.session_state.data, FILE_NAME); st.rerun()
                    
                    if st.session_state.get('active_edit') == idx:
                        with st.form(f"f_{idx}"):
                            new_note = st.text_input("Update Note", row['Note'])
                            new_amt = st.number_input("Update Amount", value=float(amt))
                            if st.form_submit_button("Update"):
                                if row['Debit'] > 0: st.session_state.data.at[idx, 'Debit'] = new_amt
                                else: st.session_state.data.at[idx, 'Credit'] = new_amt
                                st.session_state.data.at[idx, 'Note'] = new_note
                                save_file(st.session_state.data, FILE_NAME); del st.session_state.active_edit; st.rerun()

with t2:
    with st.form("new_entry_form", clear_on_submit=True):
        st.write("### Nayi Entry")
        u_name = st.text_input("Customer Naam")
        u_note = st.text_input("Detail")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Udhaar Diya", "Vasooli Hui"])
        if st.form_submit_button("Save Record"):
            dr = u_amt if "Udhaar" in u_type else 0.0
            cr = u_amt if "Vasooli" in u_type else 0.0
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            save_file(st.session_state.data, FILE_NAME); st.rerun()
