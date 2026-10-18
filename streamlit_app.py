import streamlit as st

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
import streamlit as st
import sqlite3
import os
from datetime import datetime, date
import urllib.parse
import pandas as pd

# ---------------- CONFIGURATION & SETUP ----------------
st.set_page_config(
    page_title="HomeVault | Family Bill & Expiry Locker",
    page_icon="🛡️",
    layout="wide"
)

UPLOAD_DIR = "vault_uploads"
DB_FILE = "homevault.db"

# Create folder to store uploaded bill photos/PDFs safely
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Table for Bills, Warranties & Vehicle Docs
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            purchase_date TEXT,
            expiry_date TEXT NOT NULL,
            amount REAL,
            shop_or_reg_no TEXT,
            added_by TEXT,
            notes TEXT,
            file_path TEXT
        )
    ''')
    # Table for Shared Family Members
    c.execute('''
        CREATE TABLE IF NOT EXISTS family (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            relation TEXT,
            phone TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def seed_demo_data():
    """Inserts sample items if the database is completely empty so you can test right away."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM items")
    if c.fetchone()[0] == 0:
        sample_items = [
            ("Scooter Insurance & PUC", "Vehicle (RC/Insurance/PUC)", "2025-10-25", "2026-10-24", 1450, "KA-19-EE-4567", "Self", "Full comprehensive cover", ""),
            ("Living Room Smart TV 55\"", "Home Appliance Warranty", "2025-11-15", "2026-11-15", 42000, "Reliance Digital", "Brother", "Serial No: SN998823", ""),
            ("Home Fiber Wi-Fi Plan", "Utility & Recharge", "2026-09-20", "2026-10-20", 799, "Airtel Xstream", "Self", "Monthly 100 Mbps plan", ""),
            ("Kitchen Mixer Grinder", "Home Appliance Warranty", "2025-01-10", "2027-01-10", 3800, "Harsha Electronics", "Sister", "2 Year Motor Warranty", "")
        ]
        c.executemany('''
            INSERT INTO items (title, category, purchase_date, expiry_date, amount, shop_or_reg_no, added_by, notes, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_items)
        conn.commit()
    conn.close()

init_db()
seed_demo_data()

# ---------------- HELPER FUNCTIONS ----------------
def days_until_expiry(expiry_str):
    exp_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
    today = date.today()
    return (exp_date - today).days

def create_whatsapp_link(phone, message):
    clean_phone = ''.join(filter(str.isdigit, phone))
    if len(clean_phone) == 10:
        clean_phone = "91" + clean_phone
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_msg}"

# ---------------- SIDEBAR NAVIGATION ----------------
st.sidebar.title("🛡️ HomeVault")
st.sidebar.caption("Shared Family Bill, Warranty & Vehicle Locker")

menu = st.sidebar.radio(
    "Navigation",
    ["📊 Family Locker Dashboard", "➕ Snap & Add New Bill", "👨‍👩‍👧‍👦 Family Sharing & Referrals"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Free Tier:** Up to 10 Bills Free\n\n🔓 **HomeVault Pro (₹99/yr):** Unlimited Bills + 5 Family Members + Auto WhatsApp Alerts")

# ==============================================================================
# PAGE 1: DASHBOARD (TRACK EXPIRY & VIEW BILLS)
# ==============================================================================
if menu == "📊 Family Locker Dashboard":
    st.title("🛡️ HomeVault — Family Dashboard")
    st.write("All your household bills, appliance warranties, and vehicle documents in one safe place.")

    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM items", conn)
    conn.close()

    if df.empty:
        st.warning("Your vault is empty! Click **'➕ Snap & Add New Bill'** in the sidebar to add your first item.")
    else:
        # Calculate days left for each item
        df['days_left'] = df['expiry_date'].apply(days_until_expiry)
        df = df.sort_values(by='days_left', ascending=True)

        # Top Summary Metrics
        total_items = len(df)
        expiring_soon = len(df[(df['days_left'] >= 0) & (df['days_left'] <= 15)])
        expired = len(df[df['days_left'] < 0])
        total_value = df['amount'].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Total Saved Bills", f"{total_items} / 10 Free")
        col2.metric("⚠️ Expiring Soon (15 Days)", expiring_soon)
        col3.metric("🚨 Expired Items", expired)
        col4.metric("💰 Protected Value", f"₹{total_value:,.0f}")

        st.markdown("---")

        # Filter by Category
        categories = ["All Categories"] + list(df['category'].unique())
        selected_cat = st.selectbox("🔍 Filter by Category", categories)
        if selected_cat != "All Categories":
            df = df[df['category'] == selected_cat]

        # Display Each Item as a Clean Card
        for _, row in df.iterrows():
            days = row['days_left']
            if days < 0:
                badge = f"🚨 EXPIRED ({abs(days)} days ago)"
                border_color = "red"
            elif days <= 15:
                badge = f"⚠️ EXPIRING IN {days} DAYS"
                border_color = "orange"
            else:
                badge = f"✅ ACTIVE ({days} days left)"
                border_color = "green"

            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                
                with c1:
                    st.subheader(f"{row['title']}")
                    st.caption(f"**Category:** {row['category']}  |  **Added by:** {row['added_by']}")
                    st.write(f"🏪 **Shop / Reg No:** `{row['shop_or_reg_no']}`  |  💵 **Amount:** ₹{row['amount']:,.0f}")
                    if row['notes']:
                        st.caption(f"📝 *Note: {row['notes']}*")

                with c2:
                    st.markdown(f"**Status:** :{border_color}[**{badge}**]")
                    st.write(f"📅 **Purchase Date:** {row['purchase_date']}")
                    st.write(f"⏳ **Expiry / Due Date:** `{row['expiry_date']}`")

                with c3:
                    # WhatsApp Share / Claim Card Link
                    share_msg = (
                        f"*🛡️ HomeVault Official Record*\n"
                        f"-------------------------\n"
                        f"📌 *Item:* {row['title']}\n"
                        f"🏷️ *Shop/Reg No:* {row['shop_or_reg_no']}\n"
                        f"📅 *Purchase Date:* {row['purchase_date']}\n"
                        f"⏳ *Valid Till:* {row['expiry_date']} ({badge})\n"
                        f"💵 *Amount:* ₹{row['amount']:,.0f}\n"
                        f"-------------------------\n"
                        f"_Stored safely via HomeVault Family Locker_"
                    )
                    wa_url = f"https://wa.me/?text={urllib.parse.quote(share_msg)}"
                    st.link_button("📲 Share on WhatsApp", wa_url, use_container_width=True)

                    # View Attached Bill Image/PDF
                    if row['file_path'] and os.path.exists(row['file_path']):
                        with open(row['file_path'], "rb") as file_data:
                            st.download_button(
                                label="📄 Download Original Bill",
                                data=file_data,
                                file_name=os.path.basename(row['file_path']),
                                use_container_width=True,
                                key=f"dl_{row['id']}"
                            )
                    
                    # Delete Button
                    if st.button("🗑️ Delete", key=f"del_{row['id']}", use_container_width=True):
                        conn = sqlite3.connect(DB_FILE)
                        conn.execute("DELETE FROM items WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()

# ==============================================================================
# PAGE 2: ADD NEW BILL / WARRANTY / VEHICLE DOCUMENT
# ==============================================================================
elif menu == "➕ Snap & Add New Bill":
    st.title("➕ Add a Bill, Warranty or Vehicle Document")
    st.write("Take a photo of your paper bill before the ink fades, and set an automatic expiry countdown.")

    with st.form("add_item_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Item / Document Name *", placeholder="e.g., OnePlus 11 Phone, Scooter Insurance, Mixer")
            category = st.selectbox("Category *", [
                "Home Appliance Warranty",
                "Vehicle (RC/Insurance/PUC)",
                "Mobile & Electronics",
                "Utility & Recharge (Wi-Fi/Power)",
                "Medical / Health Insurance",
                "Other Household Receipt"
            ])
            shop_or_reg = st.text_input("Shop Name / Vehicle No / Serial No", placeholder="e.g., KA-19-AB-1234 or Croma")
            amount = st.number_input("Bill Amount (₹)", min_value=0.0, step=100.0)

        with col2:
            p_date = st.date_input("Purchase / Issue Date", value=date.today())
            e_date = st.date_input("Warranty Expiry / Renewal Due Date *", value=date.today())
            added_by = st.selectbox("Uploaded By (Family Member)", ["Self", "Father", "Mother", "Brother", "Sister", "Spouse"])
            uploaded_file = st.file_uploader("Upload Bill Photo or PDF (Optional)", type=["png", "jpg", "jpeg", "pdf"])

        notes = st.text_area("Extra Notes (Optional)", placeholder="e.g., 2 years motor warranty, kept original box in loft")
        submit = st.form_submit_button("✅ Save Safely to HomeVault", use_container_width=True)

        if submit:
            if not title.strip():
                st.error("Please enter an Item / Document Name.")
            else:
                saved_path = ""
                if uploaded_file is not None:
                    saved_path = os.path.join(UPLOAD_DIR, f"{int(datetime.now().timestamp())}_{uploaded_file.name}")
                    with open(saved_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                conn = sqlite3.connect(DB_FILE)
                conn.execute('''
                    INSERT INTO items (title, category, purchase_date, expiry_date, amount, shop_or_reg_no, added_by, notes, file_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title.strip(), category, str(p_date), str(e_date), amount, shop_or_reg.strip(), added_by, notes.strip(), saved_path))
                conn.commit()
                conn.close()
                st.success(f"🎉 '{title}' has been locked safely into your HomeVault!")

# ==============================================================================
# PAGE 3: FAMILY SHARING & VIRAL REFERRAL ENGINE
# ==============================================================================
elif menu == "👨‍👩‍👧‍👦 Family Sharing & Referrals":
    st.title("👨‍👩‍👧‍👦 Shared Family Locker (Up to 5 Members)")
    st.write("Add your family members so they can access vehicle papers and appliance warranties anytime without calling you in panic.")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Add Family Member to Vault")
        with st.form("add_family_form", clear_on_submit=True):
            f_name = st.text_input("Family Member Name *", placeholder="e.g., Sandeep")
            f_rel = st.selectbox("Relationship", ["Brother", "Sister", "Father", "Mother", "Spouse", "Roommate/Friend"])
            f_phone = st.text_input("WhatsApp Number (10 Digits) *", placeholder="e.g., 9845012345")
            add_fam_btn = st.form_submit_button("➕ Add & Generate Invite Link", use_container_width=True)

            if add_fam_btn:
                if f_name.strip() and len(f_phone.strip()) >= 10:
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute("INSERT INTO family (name, relation, phone) VALUES (?, ?, ?)",
                                 (f_name.strip(), f_rel, f_phone.strip()))
                    conn.commit()
                    conn.close()
                    st.success(f"Added {f_name} to your HomeVault!")
                else:
                    st.error("Please enter a valid name and 10-digit WhatsApp number.")

    with col_right:
        st.subheader("Current Family Members")
        conn = sqlite3.connect(DB_FILE)
        fam_df = pd.read_sql_query("SELECT * FROM family", conn)
        conn.close()

        if fam_df.empty:
            st.info("No family members added yet. Add your brother, sister, or parents on the left!")
        else:
            for _, f_row in fam_df.iterrows():
                with st.container(border=True):
                    fc1, fc2 = st.columns([2, 2])
                    fc1.write(f"👤 **{f_row['name']}** ({f_row['relation']})")
                    fc1.caption(f"📞 {f_row['phone']}")
                    
                    invite_text = (
                        f"Hey {f_row['name']}! I created our family's *HomeVault* digital locker. 🛡️\n\n"
                        f"All our home appliance bills, warranty cards, and vehicle insurance/PUC papers are stored here so we never lose them.\n\n"
                        f"Join our Family Locker here: https://homevault.app/join"
                    )
                    wa_invite_link = create_whatsapp_link(f_row['phone'], invite_text)
                    fc2.link_button("📲 Send WhatsApp Invite", wa_invite_link, use_container_width=True)

    st.markdown("---")
    st.subheader("🚀 Refer Friends & Unlock 5 Extra Free Bills!")
    referral_msg = (
        "Did you know thermal paper bills fade in 90 days? 🧾\n\n"
        "I'm using *HomeVault* to store all our home appliance warranties, mixer/TV bills, and scooter insurance in one shared family locker with auto-expiry alerts!\n\n"
        "Try it 100% Free for your home: https://homevault.app"
    )
    st.code(referral_msg, language="markdown")
    st.link_button("📢 Share HomeVault on WhatsApp Status / Groups", f"https://wa.me/?text={urllib.parse.quote(referral_msg)}")
