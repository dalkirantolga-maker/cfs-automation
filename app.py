import streamlit as st
import pandas as pd
import pdfplumber
import re
import os
from datetime import datetime

DATA_FILE = "CFS_KAYITLARI.xlsx"

USERS = {
    "admin": {"password": "1234", "role": "Admin"},
    "cfs": {"password": "1234", "role": "CFS Personeli"},
    "viewer": {"password": "1234", "role": "Viewer"}
}

COLUMNS = [
    "Kayıt Tarihi",
    "Container No",
    "DO No",
    "BL No",
    "Acente",
    "Consignee",
    "Vessel",
    "Voyage",
    "Size/Type",
    "Seal No",
    "EXP Date",
    "CFS Durumu",
    "Açım Tarihi",
    "Cargo Type",
    "Quantity",
    "Hasar Durumu",
    "Delivery Tarihi",
    "Truck No",
    "Driver Name",
    "Released By",
    "Kayıt Yapan Kullanıcı",
    "Not"
]

def create_file_if_not_exists():
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=COLUMNS).to_excel(DATA_FILE, index=False)

def read_data():
    create_file_if_not_exists()
    df = pd.read_excel(DATA_FILE)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df[COLUMNS]

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

def extract_pdf_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += "\n" + (page.extract_text() or "")
    return text

def parse_delivery_order(text):
    data = {
        "Container No": "",
        "DO No": "",
        "BL No": "",
        "Acente": "",
        "Consignee": "",
        "Vessel": "",
        "Voyage": "",
        "Size/Type": "",
        "Seal No": "",
        "EXP Date": ""
    }

    container_match = re.search(r"\b[A-Z]{4}\d{7}\b", text)
    if container_match:
        data["Container No"] = container_match.group(0)

    do_match = re.search(r"DELIVERY ORDER NO\s*[:\-]?\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if do_match:
        data["DO No"] = do_match.group(1)

    bl_match = re.search(r"B/L\s*-\s*NO\s*[:\-]?\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if bl_match:
        data["BL No"] = bl_match.group(1)

    vessel_match = re.search(
        r"\b(CONTSHIP\s+[A-Z]+|HORIZON|JONATHAN\s+P|MARTI\s+SPIRIT|MATILDE\s+A)\b",
        text,
        re.IGNORECASE
    )
    if vessel_match:
        data["Vessel"] = vessel_match.group(1).upper()

    voyage_match = re.search(r"\b[0-9A-Z]{4,12}\b", text)
    if voyage_match:
        data["Voyage"] = voyage_match.group(0)

    size_match = re.search(r"\b(20GP|20DC|20DV|40GP|40HC|40HQ|45HC)\b", text, re.IGNORECASE)
    if size_match:
        data["Size/Type"] = size_match.group(1).upper()

    seal_match = re.search(r"\b[A-Z0-9]{7,10}\b", text)
    if seal_match:
        data["Seal No"] = seal_match.group(0)

    exp_match = re.search(
        r"EXP DATE\s*.*?(\d{2}-[A-Z]{3}-\d{2,4})",
        text,
        re.IGNORECASE | re.DOTALL
    )
    if exp_match:
        data["EXP Date"] = exp_match.group(1).upper()
    else:
        dates = re.findall(r"\b\d{2}-[A-Z]{3}-\d{2,4}\b", text, re.IGNORECASE)
        if dates:
            data["EXP Date"] = dates[0].upper()

    if "CMA CGM" in text.upper():
        data["Acente"] = "CMA CGM"

    return data

def login_screen():
    st.markdown("# ⚓ ALPORT CFS SYSTEM")
    st.markdown("### Kullanıcı Girişi")

    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")

    if st.button("Giriş Yap"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = USERS[username]["role"]
            st.success("Giriş başarılı.")
            st.rerun()
        else:
            st.error("Kullanıcı adı veya şifre hatalı.")

def logout_button():
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 Kullanıcı: **{st.session_state['username']}**")
    st.sidebar.write(f"🔐 Yetki: **{st.session_state['role']}**")

    if st.sidebar.button("Çıkış Yap"):
        st.session_state.clear()
        st.rerun()

st.set_page_config(
    page_title="ALPORT CFS System",
    page_icon="⚓",
    layout="wide"
)
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #001f3f 0%, #003366 100%);
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.main {
    background-color: #f5f7fb;
}

h1, h2, h3 {
    color: #001f3f;
    font-family: Arial, sans-serif;
}

.metric-card {
    padding: 25px;
    border-radius: 18px;
    color: white;
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    margin-bottom: 15px;
}

.blue-card {
    background: linear-gradient(135deg, #005bea, #00c6fb);
}

.orange-card {
    background: linear-gradient(135deg, #f7971e, #ffd200);
}

.green-card {
    background: linear-gradient(135deg, #11998e, #38ef7d);
}

.purple-card {
    background: linear-gradient(135deg, #7f00ff, #e100ff);
}

.red-card {
    background: linear-gradient(135deg, #ff416c, #ff4b2b);
}

.metric-title {
    font-size: 15px;
    font-weight: bold;
}

.metric-value {
    font-size: 34px;
    font-weight: bold;
    margin-top: 10px;
}

.metric-sub {
    font-size: 13px;
    opacity: 0.9;
}

.block-container {
    padding-top: 25px;
}

.stButton > button {
    border-radius: 10px;
    background: #005bea;
    color: white;
    border: none;
    padding: 10px 20px;
    font-weight: bold;
}

.stButton > button:hover {
    background: #003f9e;
    color: white;
}
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

create_file_if_not_exists()

st.markdown("""
# ⚓ ALPORT CFS SYSTEM
### Delivery Order & Konteyner Takip Paneli
""")

role = st.session_state["role"]
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=180)

st.sidebar.markdown("## ⚓ ALPORT CFS")
st.sidebar.markdown("### Automation System")
st.sidebar.markdown("---")
st.sidebar.title("Menü")

if role == "Admin":
    menu_options = [
        "Dashboard",
        "Delivery Order Kaydı",
        "Kayıt Ara",
        "Tüm Kayıtlar",
        "Excel İndir"
    ]
elif role == "CFS Personeli":
    menu_options = [
        "Dashboard",
        "Delivery Order Kaydı",
        "Kayıt Ara",
        "Tüm Kayıtlar"
    ]
else:
    menu_options = [
        "Dashboard",
        "Kayıt Ara",
        "Tüm Kayıtlar"
    ]

menu = st.sidebar.radio("Sayfa Seç", menu_options)
logout_button()

if menu == "Dashboard":
    df = read_data()

    st.subheader("📊 Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    total = len(df)
    waiting = len(df[df["CFS Durumu"] == "Bekliyor"]) if not df.empty else 0
    opened = len(df[df["CFS Durumu"] == "CFS Açıldı"]) if not df.empty else 0
    delivered = len(df[df["CFS Durumu"] == "Delivery Yapıldı"]) if not df.empty else 0

 col1.markdown(f"""
<div class="metric-card blue-card">
    <div class="metric-title">📦 TOPLAM KAYIT</div>
    <div class="metric-value">{total}</div>
    <div class="metric-sub">Tüm kayıtlar</div>
</div>
""", unsafe_allow_html=True)

col2.markdown(f"""
<div class="metric-card orange-card">
    <div class="metric-title">⏳ BEKLEYEN</div>
    <div class="metric-value">{waiting}</div>
    <div class="metric-sub">Bekleyen konteyner</div>
</div>
""", unsafe_allow_html=True)

col3.markdown(f"""
<div class="metric-card green-card">
    <div class="metric-title">✅ CFS AÇILDI</div>
    <div class="metric-value">{opened}</div>
    <div class="metric-sub">CFS işlemi açıldı</div>
</div>
""", unsafe_allow_html=True)

col4.markdown(f"""
<div class="metric-card purple-card">
    <div class="metric-title">🚛 DELIVERY YAPILDI</div>
    <div class="metric-value">{delivered}</div>
    <div class="metric-sub">Teslim edildi</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Son Kayıtlar")
    st.dataframe(df.tail(10), use_container_width=True)

elif menu == "Delivery Order Kaydı":
    st.subheader("📄 Delivery Order PDF Yükle")

    uploaded_pdf = st.file_uploader("PDF dosyası seç", type=["pdf"])

    parsed = {
        "Container No": "",
        "DO No": "",
        "BL No": "",
        "Acente": "",
        "Consignee": "",
        "Vessel": "",
        "Voyage": "",
        "Size/Type": "",
        "Seal No": "",
        "EXP Date": ""
    }

    if uploaded_pdf is not None:
        try:
            text = extract_pdf_text(uploaded_pdf)
            parsed = parse_delivery_order(text)
            st.success("PDF okundu. Bilgileri kontrol edip kaydedebilirsiniz.")
        except Exception as e:
            st.error(f"PDF okunamadı: {e}")

    st.markdown("### Konteyner / DO Bilgileri")

    col1, col2 = st.columns(2)

    with col1:
        container_no = st.text_input("Container No", value=parsed["Container No"])
        do_no = st.text_input("Delivery Order No", value=parsed["DO No"])
        bl_no = st.text_input("B/L No", value=parsed["BL No"])
        acente = st.text_input("Acente", value=parsed["Acente"])
        consignee = st.text_input("Consignee", value=parsed["Consignee"])

    with col2:
        vessel = st.text_input("Vessel", value=parsed["Vessel"])
        voyage = st.text_input("Voyage", value=parsed["Voyage"])
        size_type = st.text_input("Size / Type", value=parsed["Size/Type"])
        seal_no = st.text_input("Seal No", value=parsed["Seal No"])
        exp_date = st.text_input("EXP Date", value=parsed["EXP Date"])

    st.markdown("### CFS Operasyon Bilgileri")

    col3, col4 = st.columns(2)

    with col3:
        cfs_durumu = st.selectbox(
            "CFS Durumu",
            ["Bekliyor", "CFS Açıldı", "Delivery Yapıldı", "İptal"]
        )
        acim_tarihi = st.text_input("Açım Tarihi", placeholder="Örn: 26-06-2026")
        cargo_type = st.text_input("Cargo Type")
        quantity = st.text_input("Quantity")

    with col4:
        hasar = st.selectbox("Hasar Durumu", ["Yok", "Var"])
        delivery_tarihi = st.text_input("Delivery Tarihi", placeholder="Örn: 26-06-2026")
        truck_no = st.text_input("Truck No")
        driver_name = st.text_input("Driver Name")
        released_by = st.text_input("Released By")

    note = st.text_area("Not")

    if st.button("💾 Kaydet"):
        if container_no.strip() == "":
            st.error("Container No boş olamaz.")
        else:
            df = read_data()

            new_row = {
                "Kayıt Tarihi": datetime.now().strftime("%d-%m-%Y %H:%M"),
                "Container No": container_no.upper().strip(),
                "DO No": do_no.strip(),
                "BL No": bl_no.strip(),
                "Acente": acente.strip(),
                "Consignee": consignee.strip(),
                "Vessel": vessel.strip(),
                "Voyage": voyage.strip(),
                "Size/Type": size_type.strip(),
                "Seal No": seal_no.strip(),
                "EXP Date": exp_date.strip(),
                "CFS Durumu": cfs_durumu,
                "Açım Tarihi": acim_tarihi.strip(),
                "Cargo Type": cargo_type.strip(),
                "Quantity": quantity.strip(),
                "Hasar Durumu": hasar,
                "Delivery Tarihi": delivery_tarihi.strip(),
                "Truck No": truck_no.strip(),
                "Driver Name": driver_name.strip(),
                "Released By": released_by.strip(),
                "Kayıt Yapan Kullanıcı": st.session_state["username"],
                "Not": note.strip()
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Kayıt başarıyla kaydedildi.")

elif menu == "Kayıt Ara":
    st.subheader("🔎 Kayıt Ara")

    search = st.text_input("Container No / DO No / BL No / Vessel ile ara")

    df = read_data()

    if search:
        result = df[
            df["Container No"].astype(str).str.contains(search, case=False, na=False) |
            df["DO No"].astype(str).str.contains(search, case=False, na=False) |
            df["BL No"].astype(str).str.contains(search, case=False, na=False) |
            df["Vessel"].astype(str).str.contains(search, case=False, na=False)
        ]

        if result.empty:
            st.warning("Kayıt bulunamadı.")
        else:
            st.dataframe(result, use_container_width=True)
    else:
        st.info("Arama yapmak için bilgi girin.")

elif menu == "Tüm Kayıtlar":
    st.subheader("📋 Tüm CFS Kayıtları")
    df = read_data()
    st.dataframe(df, use_container_width=True)

elif menu == "Excel İndir":
    st.subheader("⬇️ Excel İndir")

    df = read_data()
    st.dataframe(df, use_container_width=True)

    with open(DATA_FILE, "rb") as file:
        st.download_button(
            label="Excel Dosyasını İndir",
            data=file,
            file_name="CFS_KAYITLARI.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
