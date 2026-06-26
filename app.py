import streamlit as st
import pandas as pd
import pdfplumber
import plotly.express as px
import re
import os
from datetime import datetime, date

DATA_FILE = "CFS_KAYITLARI.xlsx"

USERS = {
    "admin": {"password": "1234", "role": "Admin"},
    "cfs": {"password": "1234", "role": "CFS Personeli"},
    "viewer": {"password": "1234", "role": "Viewer"},
}

COLUMNS = [
    "Kayıt Tarihi", "Container No", "DO No", "BL No", "Acente", "Consignee",
    "Vessel", "Voyage", "Size/Type", "Seal No", "EXP Date", "CFS Durumu",
    "Açım Tarihi", "Cargo Type", "Quantity", "Hasar Durumu", "Delivery Tarihi",
    "Truck No", "Driver Name", "Released By", "Kayıt Yapan", "Not"
]

st.set_page_config(
    page_title="ALPORT CFS SYSTEM",
    page_icon="⚓",
    layout="wide"
)

st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #001B3A 0%, #003B73 100%);
}
[data-testid="stSidebar"] * {
    color: white !important;
}
.block-container {
    padding-top: 1.5rem;
}
.main-title {
    background: linear-gradient(90deg, #001B3A, #005B96);
    padding: 22px;
    border-radius: 18px;
    color: white;
    margin-bottom: 20px;
}
.card {
    padding: 22px;
    border-radius: 18px;
    color: white;
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    min-height: 130px;
}
.blue {background: linear-gradient(135deg, #005BEA, #00C6FB);}
.orange {background: linear-gradient(135deg, #F7971E, #FFD200);}
.green {background: linear-gradient(135deg, #11998E, #38EF7D);}
.purple {background: linear-gradient(135deg, #7F00FF, #E100FF);}
.red {background: linear-gradient(135deg, #FF416C, #FF4B2B);}
.card-title {font-size: 15px; font-weight: 700;}
.card-value {font-size: 38px; font-weight: 800; margin-top: 12px;}
.card-sub {font-size: 13px; opacity: 0.9;}
.status-bekliyor {background:#fff3cd;color:#856404;padding:5px 10px;border-radius:8px;}
.status-acildi {background:#d4edda;color:#155724;padding:5px 10px;border-radius:8px;}
.status-delivery {background:#d7c8ff;color:#3b168c;padding:5px 10px;border-radius:8px;}
.status-iptal {background:#f8d7da;color:#721c24;padding:5px 10px;border-radius:8px;}
</style>
""", unsafe_allow_html=True)


def create_file():
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=COLUMNS).to_excel(DATA_FILE, index=False)


def read_data():
    create_file()
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


def find_first(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_do(text):
    data = {k: "" for k in [
        "Container No", "DO No", "BL No", "Acente", "Consignee",
        "Vessel", "Voyage", "Size/Type", "Seal No", "EXP Date"
    ]}

    cont = re.search(r"\b[A-Z]{4}\d{7}\b", text)
    if cont:
        data["Container No"] = cont.group(0)

    data["DO No"] = find_first(r"DELIVERY ORDER NO\s*[:\-]?\s*([A-Z0-9]+)", text)
    data["BL No"] = find_first(r"B/L\s*-\s*NO\s*[:\-]?\s*([A-Z0-9]+)", text)
    data["Voyage"] = find_first(r"VOYAGE\s*[:\-]?\s*([A-Z0-9]+)", text)

    vessel = find_first(r"VESSEL\s*[:\-]?\s*([A-Z0-9\s]+)", text)
    if vessel:
        data["Vessel"] = vessel.split("\n")[0].strip()

    size = re.search(r"\b(20GP|20DC|20DV|40GP|40HC|40HQ|45HC|45GP)\b", text, re.IGNORECASE)
    if size:
        data["Size/Type"] = size.group(1).upper()

    seal = re.search(r"SEAL\s*([A-Z0-9]{5,15})", text, re.IGNORECASE)
    if seal:
        data["Seal No"] = seal.group(1)

    exp = re.search(r"EXP DATE\s*.*?(\d{2}-[A-Z]{3}-\d{2,4})", text, re.IGNORECASE | re.DOTALL)
    if exp:
        data["EXP Date"] = exp.group(1).upper()
    else:
        dates = re.findall(r"\b\d{2}-[A-Z]{3}-\d{2,4}\b", text, re.IGNORECASE)
        if dates:
            data["EXP Date"] = dates[-1].upper()

    if "CMA CGM" in text.upper():
        data["Acente"] = "CMA CGM"
    elif "MSC" in text.upper():
        data["Acente"] = "MSC"
    elif "MAERSK" in text.upper():
        data["Acente"] = "MAERSK"

    lines = [x.strip() for x in text.split("\n") if x.strip()]
    for line in lines[:15]:
        u = line.upper()
        if not any(x in u for x in ["DELIVERY", "PAGE", "VESSEL", "VOYAGE", "CMA", "MSC", "B/L"]):
            if len(line) > 3:
                data["Consignee"] = line
                break

    return data


def login():
    st.markdown("""
    <div class="main-title">
        <h1>⚓ ALPORT CFS SYSTEM</h1>
        <p>Delivery Order & Container Tracking Platform</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.subheader("🔐 Kullanıcı Girişi")
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = USERS[username]["role"]
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı.")


def logout():
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **{st.session_state.username}**")
    st.sidebar.write(f"🔐 {st.session_state.role}")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.clear()
        st.rerun()


def card(col, title, value, sub, css):
    col.markdown(f"""
    <div class="card {css}">
        <div class="card-title">{title}</div>
        <div class="card-value">{value}</div>
        <div class="card-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def parse_exp_date(x):
    try:
        return pd.to_datetime(x, errors="coerce", dayfirst=True)
    except Exception:
        return pd.NaT


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

create_file()

st.sidebar.markdown("## ⚓ ALPORT")
st.sidebar.markdown("### CFS SYSTEM")
st.sidebar.markdown("---")

role = st.session_state.role

if role == "Admin":
    menus = ["Dashboard", "Delivery Order Kaydı", "Kayıt Ara", "Tüm Kayıtlar", "Excel İndir"]
elif role == "CFS Personeli":
    menus = ["Dashboard", "Delivery Order Kaydı", "Kayıt Ara", "Tüm Kayıtlar"]
else:
    menus = ["Dashboard", "Kayıt Ara", "Tüm Kayıtlar"]

menu = st.sidebar.radio("Menü", menus)
logout()

st.markdown("""
<div class="main-title">
    <h1>⚓ ALPORT CFS AUTOMATION SYSTEM</h1>
    <p>Banjul Terminal | Delivery Order & CFS Operation Tracking</p>
</div>
""", unsafe_allow_html=True)

df = read_data()

if menu == "Dashboard":
    total = len(df)
    waiting = len(df[df["CFS Durumu"] == "Bekliyor"])
    opened = len(df[df["CFS Durumu"] == "CFS Açıldı"])
    delivered = len(df[df["CFS Durumu"] == "Delivery Yapıldı"])
    cancelled = len(df[df["CFS Durumu"] == "İptal"])

    c1, c2, c3, c4, c5 = st.columns(5)
    card(c1, "📦 TOPLAM KAYIT", total, "Tüm zamanlar", "blue")
    card(c2, "⏳ BEKLEYEN", waiting, "İşlem bekleyen", "orange")
    card(c3, "✅ CFS AÇILDI", opened, "CFS işlemi açıldı", "green")
    card(c4, "🚛 DELIVERY", delivered, "Teslim edildi", "purple")
    card(c5, "⚠️ İPTAL", cancelled, "İptal kayıt", "red")

    st.markdown("---")

    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.subheader("📊 Durum Dağılımı")
        status_df = df["CFS Durumu"].value_counts().reset_index()
        status_df.columns = ["Durum", "Adet"]
        if not status_df.empty:
            fig = px.pie(status_df, names="Durum", values="Adet", hole=0.45)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("⏰ Yaklaşan EXP Date")
        temp = df.copy()
        temp["EXP Parsed"] = temp["EXP Date"].apply(parse_exp_date)
        today = pd.Timestamp(date.today())
        temp["Kalan Gün"] = (temp["EXP Parsed"] - today).dt.days
        soon = temp[(temp["Kalan Gün"] >= 0) & (temp["Kalan Gün"] <= 7)]
        soon = soon.sort_values("Kalan Gün")
        if soon.empty:
            st.success("7 gün içinde yaklaşan EXP Date yok.")
        else:
            st.dataframe(
                soon[["Container No", "DO No", "EXP Date", "Kalan Gün", "CFS Durumu"]],
                use_container_width=True
            )

    st.subheader("🕘 Son Kayıtlar")
    st.dataframe(df.tail(10), use_container_width=True)

elif menu == "Delivery Order Kaydı":
    st.subheader("📄 Delivery Order PDF Yükle")

    parsed = {k: "" for k in [
        "Container No", "DO No", "BL No", "Acente", "Consignee",
        "Vessel", "Voyage", "Size/Type", "Seal No", "EXP Date"
    ]}

    uploaded_pdf = st.file_uploader("Delivery Order PDF seç", type=["pdf"])

    if uploaded_pdf is not None:
        try:
            text = extract_pdf_text(uploaded_pdf)
            parsed = parse_do(text)
            st.success("PDF başarıyla okundu. Bilgileri kontrol edip kaydedin.")
        except Exception as e:
            st.error(f"PDF okunamadı: {e}")

    col1, col2 = st.columns(2)

    with col1:
        container_no = st.text_input("Container No", parsed["Container No"])
        do_no = st.text_input("Delivery Order No", parsed["DO No"])
        bl_no = st.text_input("B/L No", parsed["BL No"])
        acente = st.text_input("Acente", parsed["Acente"])
        consignee = st.text_input("Consignee", parsed["Consignee"])

    with col2:
        vessel = st.text_input("Vessel", parsed["Vessel"])
        voyage = st.text_input("Voyage", parsed["Voyage"])
        size_type = st.text_input("Size / Type", parsed["Size/Type"])
        seal_no = st.text_input("Seal No", parsed["Seal No"])
        exp_date = st.text_input("EXP Date", parsed["EXP Date"])

    st.markdown("### CFS Operasyon Bilgileri")

    c3, c4 = st.columns(2)

    with c3:
        cfs_durumu = st.selectbox("CFS Durumu", ["Bekliyor", "CFS Açıldı", "Delivery Yapıldı", "İptal"])
        acim_tarihi = st.text_input("Açım Tarihi")
        cargo_type = st.text_input("Cargo Type")
        quantity = st.text_input("Quantity")

    with c4:
        hasar = st.selectbox("Hasar Durumu", ["Yok", "Var"])
        delivery_tarihi = st.text_input("Delivery Tarihi")
        truck_no = st.text_input("Truck No")
        driver_name = st.text_input("Driver Name")
        released_by = st.text_input("Released By")

    note = st.text_area("Not")

    if st.button("💾 Kaydet", use_container_width=True):
        if not container_no.strip():
            st.error("Container No boş olamaz.")
        else:
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
                "Kayıt Yapan": st.session_state.username,
                "Not": note.strip()
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Kayıt başarıyla kaydedildi.")

elif menu == "Kayıt Ara":
    st.subheader("🔎 Kayıt Ara")
    search = st.text_input("Container / DO / BL / Vessel / Consignee ara")

    if search:
        result = df[
            df["Container No"].astype(str).str.contains(search, case=False, na=False) |
            df["DO No"].astype(str).str.contains(search, case=False, na=False) |
            df["BL No"].astype(str).str.contains(search, case=False, na=False) |
            df["Vessel"].astype(str).str.contains(search, case=False, na=False) |
            df["Consignee"].astype(str).str.contains(search, case=False, na=False)
        ]
        st.dataframe(result, use_container_width=True)
    else:
        st.info("Arama yapmak için bilgi girin.")

elif menu == "Tüm Kayıtlar":
    st.subheader("📋 Tüm CFS Kayıtları")
    st.dataframe(df, use_container_width=True)

elif menu == "Excel İndir":
    st.subheader("⬇️ Excel İndir")
    st.dataframe(df, use_container_width=True)

    with open(DATA_FILE, "rb") as file:
        st.download_button(
            label="Excel Dosyasını İndir",
            data=file,
            file_name="CFS_KAYITLARI.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
