import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Files
FILE_NAME = "noor_ledger_final.csv"
PASSWORD = "noor786"

st.set_page_config(page_title="Noor Pharmacy", layout="centered")

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🔐 Login</h2>", unsafe_allow_html=True)
    if st.text_input("PIN", type="password") == PASSWORD:
        st.session_state.logged_in = True
        st.rerun()
    st.stop()

# --- ADVANCED CSS (Professional App Look) ---
st.markdown("""
<style>
    .stApp { background-color: #F0F4F8 !important; }
    /* Metric Cards */
    .m-card { background: white; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }
    .m-val { font-size: 20px; font-weight: bold; }
    /* Transaction List */
    .txn-row { background: white; padding: 10px 15px; border-bottom: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center; }
    .txn-type { font-weight: 500; color: #4A5568; margin: 0; }
    .txn-date { font-size: 11px; color: #A0AEC0; margin: 0; }
    .txn-amt { font-weight: bold; font-size: 16px; color: #2D3748; }
    /* Floating Action Buttons */
    .fab-container { position: fixed; bottom: 20px; left: 0; right: 0; display: flex; justify-content: space-around; padding: 0 20px; z-index: 1000; }
    .btn-blue { background-color: #1E88E5; color: white; padding: 12px 25px; border-radius: 30px; border: none; font-weight: bold; width: 45%; }
    .btn-orange { background-color: #FB8C00; color: white; padding: 12px 25px; border-radius: 30px; border: none; font-weight: bold; width: 45%; }
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

# --- TOP METRICS ---
summary = st.session_state.data.groupby('Name').apply(lambda x: x['Debit'].sum() - x['Credit'].sum(), include_groups=False)
receive = summary[summary > 0].sum()
pay = abs(summary[summary < 0].sum())

c1, c2 = st.columns(2)
c1.markdown(f'<div class="m-card"><span style="color:#78909C;">To Receive</span><br><span class="m-val" style="color:#2E7D32;">Rs {receive:,.0f}</span></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="m-card"><span style="color:#78909C;">To Pay</span><br><span class="m-val" style="color:#C62828;">Rs {pay:,.0f}</span></div>', unsafe_allow_html=True)

# --- CUSTOMER SELECTOR ---
st.write("")
selected_cust = st.selectbox("👤 Select Customer", ["All Customers"] + list(st.session_state.data["Name"].unique()))

if selected_cust == "All Customers":
    search = st.text_input("🔍 Search Name", placeholder="Type name...")
    names = st.session_state.data["Name"].unique()
    if search: names = [n for n in names if search.lower() in n.lower()]
    for n in names:
        bal = summary.get(n, 0)
        st.markdown(f'<div class="txn-row"><div><p class="txn-type">{n}</p></div><div class="txn-amt">Rs {bal:,.0f}</div></div>', unsafe_allow_html=True)
else:
    # --- CUSTOMER DETAIL VIEW (As per Screenshot) ---
    cust_bal = summary.get(selected_cust, 0)
    st.markdown(f"""
    <div style="background:white; padding:20px; border-radius:15px; margin-bottom:10px; text-align:center;">
        <p style="color:#78909C; margin:0;">To Receive</p>
        <h2 style="color:#1E88E5; margin:0;">Rs {cust_bal:,.0f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Action Icons
    ic1, ic2 = st.columns(2)
    wa_msg = f"Noor Pharmacy: Your balance is Rs {cust_bal}."
    ic1.link_button("📩 Remind WhatsApp", f"https://web.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}")
    ic2.button("📊 Send PDF (Coming Soon)")

    # Transaction History
    st.write("### History")
    cust_df = st.session_state.data[st.session_state.data['Name'] == selected_cust].iloc[::-1] # Newest first
    for _, row in cust_df.iterrows():
        t_type = "Credit" if row['Debit'] > 0 else "Payment"
        t_amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
        st.markdown(f"""
        <div class="txn-row">
            <div><p class="txn-type">↗️ {t_type}</p><p class="txn-date">{row['Date']}</p></div>
            <div class="txn-amt">Rs {t_amt:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

# --- FLOATING BUTTONS ---
st.markdown("""
<div class="fab-container">
    <button class="btn-blue">↙️ Take Payment</button>
    <button class="btn-orange">↗️ Give Credit</button>
</div>
""", unsafe_allow_html=True)

# Entry Form
with st.expander("📝 Manual Entry Form"):
    with st.form("entry_form", clear_on_submit=True):
        u_name = st.text_input("Name", value="" if selected_cust=="All Customers" else selected_cust)
        u_amt = st.number_input("Amount", min_value=0.0)
        u_type = st.radio("Type", ["Give Credit", "Take Payment"], horizontal=True)
        if st.form_submit_button("Save Transaction"):
            dr, cr = (u_amt, 0.0) if u_type == "Give Credit" else (0.0, u_amt)
            new_r = {"Date": datetime.now().strftime("%d/%m/%Y"), "Name": u_name, "Note": "Manual", "Debit": dr, "Credit": cr}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False); st.rerun()
