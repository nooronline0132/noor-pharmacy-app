import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION & THEME ---
st.set_page_config(page_title="Noor Pharmacy POS", layout="wide")

# Windows XP Styling
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF !important; }
    /* XP Royal Blue Header */
    .header { background-color: #0D47A1; padding: 15px; border-radius: 5px; text-align: center; color: white; margin-bottom: 20px; border-bottom: 4px solid #FBC02D; }
    /* XP Green Buttons */
    .stButton>button { background-color: #2E7D32 !important; color: white !important; border-radius: 8px !important; font-weight: bold; border: 2px solid #1B5E20; }
    /* Cards Style */
    .bill-card { background-color: #F0F4F8; padding: 20px; border-radius: 10px; border-left: 5px solid #0D47A1; }
    .total-box { font-size: 32px; font-weight: bold; color: #0D47A1; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_files():
    prod_df = pd.read_csv("Products.xlsx - Products.csv")
    acc_df = pd.read_csv("AccountCodes.xlsx - AccountCodes.csv")
    return prod_df, acc_df

try:
    prods, accounts = load_files()
except:
    st.error("Please ensure Products and AccountCodes CSV files are in the same folder.")
    st.stop()

# --- HEADER ---
st.markdown("<div class='header'><h1>NOOR PHARMACY - SALE POINT</h1></div>", unsafe_allow_html=True)

# --- SALE INTERFACE ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🛒 Item Selection")
    
    # Customer Selection from AccountCodes
    cust_list = accounts['Name'].tolist()
    customer = st.selectbox("Select Customer / Account", ["Walk-in Customer"] + cust_list)
    
    # Product Search/Scan from Products
    prod_list = prods['ProductName'].tolist()
    selected_item = st.selectbox("Search Product or Scan Barcode", [""] + prod_list)
    
    if selected_item != "":
        # Fetching price from Product file
        item_details = prods[prods['ProductName'] == selected_item].iloc[0]
        price = item_details['RetailPrice']
        packing = item_details['Packing']
        
        c1, c2, c3 = st.columns(3)
        qty = c1.number_input("Quantity", min_value=1, value=1)
        disc = c2.number_input("Discount %", min_value=0, max_value=100, value=0)
        
        item_total = (price * qty) * (1 - disc/100)
        c3.markdown(f"**Price:** Rs {price}<br>**Total:** Rs {item_total:,.2f}", unsafe_allow_html=True)
        
        if st.button("➕ Add to Bill"):
            if 'cart' not in st.session_state: st.session_state.cart = []
            st.session_state.cart.append({
                "Item": selected_item,
                "Price": price,
                "Qty": qty,
                "Total": item_total
            })
            st.rerun()

with col2:
    st.markdown("<div class='bill-card'>", unsafe_allow_html=True)
    st.subheader("📑 Current Bill")
    
    if 'cart' in st.session_state and len(st.session_state.cart) > 0:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.table(cart_df)
        
        grand_total = cart_df['Total'].sum()
        st.markdown(f"<div class='total-box'>Net Total: Rs {grand_total:,.2f}</div>", unsafe_allow_html=True)
        
        if st.button("✅ FINALIZE & PRINT"):
            st.success(f"Bill Generated for {customer}!")
            # Future WhatsApp Logic will go here
            st.session_state.cart = []
            st.rerun()
            
        if st.button("❌ Clear Bill"):
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("No items added yet.")
    st.markdown("</div>", unsafe_allow_html=True)
