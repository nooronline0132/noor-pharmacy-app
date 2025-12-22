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

# Mobile Friendly CSS
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    .main-title { font-size: 24px !important; text-align: center; color: #0D47A1; font-weight: bold; margin-bottom: 10px; }
    .card { background: white; padding: 12px; border-radius: 12px; border: 1px solid #ddd; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'custs' not in st.session_state: st.session_state.custs = load_customers(st.session_state.data)

st.markdown('<div class="main-title">🏥 NOOR PHARMACY MOBILE</div>', unsafe_allow_html=True)

# --- TOP SUMMARY (With Error Fix) ---
# Agar data khali ho to 0 dikhaye
if not st.session_state.data.empty:
    summary = st.session_state.data.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
    receive = summary[summary > 0].sum()
    pay = abs(summary[summary < 0].sum())
else:
    receive = 0.0
    pay = 0.0

m1, m2 = st.columns(2)
m1.metric("KUL VASOOLI", f"Rs {receive:,.0f}")
m2.metric("KUL ADAIGI", f"Rs {pay:,.0f}")

t1, t2 = st.tabs(["👤 CUSTOMERS", "➕ NEW ENTRY"])

with t1:
    search = st.text_input("🔍 Search Name...")
    # Add Default Customer if none exists
    if st.session_state.custs.empty:
        st.info("Abhi koi customer nahi hai. 'NEW ENTRY' mein ja kar pehli entry karein.")
    
    disp = st.session_state.custs
    if search: disp = disp[disp['Name'].str.contains(search, case=False)]
    
    for idx, r in disp.iterrows():
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 3])
            
            with c1:
                img = r['Image_Path'] if r['Image_Path'] and os.path.exists(str(r['Image_Path'])) else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                st.image(img, width=70)
            
            with c2:
                bal = summary.get(r['Name'], 0) if not st.session_state.data.empty else 0
                st.subheader(r['Name'])
                st.write(f"**Bal: Rs {bal:,.0f}**")
            
            # Actions
            col_a, col_b = st.columns(2)
            msg = f"Assalam o Alaikum {r['Name']}, Aapka balance Rs {bal} hai. Shukriya."
            wa_url = f"https://web.whatsapp.com/send?text={urllib.parse.quote(msg)}"
            col_a.markdown(f'🔔 [**Reminder**]({wa_url})')
            
            cust_ledger = st.session_state.data[st.session_state.data['Name'] == r['Name']]
            csv_data = cust_ledger.to_csv(index=False).encode('utf-8')
            col_b.download_button("📥 Report", data=csv_data, file_name=f"{r['Name']}.csv", mime='text/csv', key=f"dl_{idx}")

            with st.expander("🛠️ Options & History"):
                if st.button(f"🗑️ Delete Account", key=f"fdel_{idx}"):
                    st.session_state.custs = st.session_state.custs.drop(idx)
                    st.session_state.data = st.session_state.data[st.session_state.data['Name'] != r['Name']]
                    save_file(st.session_state.custs, CUST_FILE); save_file(st.session_state.data, FILE_NAME)
                    st.rerun()
                
                for h_idx, h_row in cust_ledger.iterrows():
                    st.markdown("---")
                    amt = h_row['Debit'] if h_row['Debit'] > 0 else h_row['Credit']
                    st.caption(f"{h_row['Date']} | {h_row['Note']} | Rs {amt}")
                    if st.button("❌ Del", key=f"db_{h_idx}"):
                        st.session_state.data = st.session_state.data.drop(h_idx)
                        save_file(st.session_state.data, FILE_NAME); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

with t2:
    with st.form("mobile_entry", clear_on_submit=True):
        st.write("### Nayi Entry")
        # Direct Text Input if no customers yet
        if st.session_state.custs.empty:
            u_name = st.text_input("Naya Customer Naam")
        else:
            u_name = st.selectbox("Customer Select Karein", st.session_state.custs['Name'].tolist())
            u_name_extra = st.text_input("Ya Naya Naam Likhein (Optional)")
            if u_name_extra: u_name = u_name_extra
            
        u_note = st.text_input("Details")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Udhaar Diya", "Vasooli Hui"])
        
        if st.form_submit_button("SAVE RECORD"):
            dr = u_amt if "Udhaar" in u_type else 0.0
            cr = u_amt if "Vasooli" in u_type else 0.0
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            # Update customer list too
            if u_name not in st.session_state.custs['Name'].tolist():
                new_c = pd.DataFrame([{"Name": u_name, "Phone": "", "Address": "", "Image_Path": ""}])
                st.session_state.custs = pd.concat([st.session_state.custs, new_c], ignore_index=True)
                save_file(st.session_state.custs, CUST_FILE)
            
            save_file(st.session_state.data, FILE_NAME); st.rerun()
