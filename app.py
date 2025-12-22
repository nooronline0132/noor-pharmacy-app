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
    .mobile-btn { width: 100%; border-radius: 8px; padding: 10px; margin-top: 5px; text-align: center; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
</style>
""", unsafe_allow_html=True)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'custs' not in st.session_state: st.session_state.custs = load_customers(st.session_state.data)

st.markdown('<div class="main-title">🏥 NOOR PHARMACY MOBILE</div>', unsafe_allow_html=True)

# Top Summary Cards (Optimized for Mobile)
summary = st.session_state.data.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
m1, m2 = st.columns(2)
m1.metric("KUL VASOOLI", f"Rs {summary[summary > 0].sum():,.0f}")
m2.metric("KUL ADAIGI", f"Rs {abs(summary[summary < 0].sum()):,.0f}")

t1, t2 = st.tabs(["👤 CUSTOMERS", "➕ NEW ENTRY"])

with t1:
    search = st.text_input("🔍 Search Name...")
    disp = st.session_state.custs
    if search: disp = disp[disp['Name'].str.contains(search, case=False)]
    
    for idx, r in disp.iterrows():
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 3])
            
            with c1: # Profile Photo
                img = r['Image_Path'] if r['Image_Path'] and os.path.exists(str(r['Image_Path'])) else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                st.image(img, width=70)
            
            with c2: # Name & Balance
                bal = summary.get(r['Name'], 0)
                st.subheader(r['Name'])
                st.write(f"**Bal: Rs {bal:,.0f}**")
            
            # Action Row (Reminders & Downloads)
            col_a, col_b = st.columns(2)
            msg = f"Assalam o Alaikum {r['Name']}, Aapka balance Rs {bal} hai. Shukriya."
            wa_url = f"https://web.whatsapp.com/send?text={urllib.parse.quote(msg)}"
            col_a.markdown(f'🔔 [**Reminder**]({wa_url})')
            
            cust_ledger = st.session_state.data[st.session_state.data['Name'] == r['Name']]
            csv_data = cust_ledger.to_csv(index=False).encode('utf-8')
            col_b.download_button("📥 Report", data=csv_data, file_name=f"{r['Name']}.csv", mime='text/csv', key=f"dl_{idx}")

            with st.expander("🛠️ History & Edit"):
                # Full Delete Button
                if st.button(f"🗑️ Delete Account", key=f"fdel_{idx}"):
                    st.session_state.custs = st.session_state.custs.drop(idx)
                    st.session_state.data = st.session_state.data[st.session_state.data['Name'] != r['Name']]
                    save_file(st.session_state.custs, CUST_FILE); save_file(st.session_state.data, FILE_NAME)
                    st.rerun()
                
                # History List
                for h_idx, h_row in cust_ledger.iterrows():
                    st.markdown("---")
                    amt = h_row['Debit'] if h_row['Debit'] > 0 else h_row['Credit']
                    st.caption(f"{h_row['Date']} | {h_row['Note']} | Rs {amt}")
                    
                    e1, e2 = st.columns(2)
                    if e1.button("✏️ Edit", key=f"eb_{h_idx}"): st.session_state.active_edit = h_idx
                    if e2.button("❌ Del", key=f"db_{h_idx}"):
                        st.session_state.data = st.session_state.data.drop(h_idx)
                        save_file(st.session_state.data, FILE_NAME); st.rerun()

                    if st.session_state.get('active_edit') == h_idx:
                        with st.form(f"ef_{h_idx}"):
                            enote = st.text_input("Detail", h_row['Note'])
                            eamt = st.number_input("Amount", value=float(amt))
                            if st.form_submit_button("Update"):
                                if h_row['Debit'] > 0: st.session_state.data.at[h_idx, 'Debit'] = eamt
                                else: st.session_state.data.at[h_idx, 'Credit'] = eamt
                                st.session_state.data.at[h_idx, 'Note'] = enote
                                save_file(st.session_state.data, FILE_NAME); del st.session_state.active_edit; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

with t2:
    with st.form("mobile_entry", clear_on_submit=True):
        st.write("### Nayi Entry")
        u_name = st.selectbox("Customer", st.session_state.custs['Name'].tolist())
        u_note = st.text_input("Details")
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Udhaar Diya", "Vasooli Hui"])
        if st.form_submit_button("SAVE RECORD"):
            dr = u_amt if "Udhaar" in u_type else 0.0
            cr = u_amt if "Vasooli" in u_type else 0.0
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": u_note, "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            save_file(st.session_state.data, FILE_NAME); st.rerun()
