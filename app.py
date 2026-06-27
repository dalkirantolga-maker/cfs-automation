import streamlit as st
import pandas as pd
import pdfplumber
import plotly.express as px
import re
import os
from datetime import datetime, date

DATA_FILE = "CFS_KAYITLARI.xlsx"
PDF_FOLDER = "DO_PDF_ARCHIVE"
os.makedirs(PDF_FOLDER, exist_ok=True)

USERS = {
    "admin": {"password": "1234", "role": "Admin"},
    "cfs": {"password": "1234", "role": "CFS Personeli"},
    "viewer": {"password": "1234", "role": "Viewer"},
}

COLUMNS = [
    "Kayıt Tarihi", "Container No", "DO No", "BL No", "Acente", "Consignee",
    "Vessel", "Voyage", "Size/Type", "Seal No", "EXP Date", "CFS Durumu",
    "Açım Tarihi", "Cargo Type", "Quantity", "Hasar Durumu", "Delivery Tarihi",
    "Truck No", "Driver Name", "Released By", "Kayıt Yapan", "PDF Dosya Yolu", "Not"
]

st.set_page_config(page_title="ALPORT CFS SYSTEM", page_icon="⚓", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] {background: linear-gradient(180deg,#001B3A,#003B73);}
[data-testid="stSidebar"] * {color:white!important;}
.block-container {padding-top:1.2rem;}
.header {background:linear-gradient(90deg,#001B3A,#005B96);padding:22px;border-radius:18px;color:white;margin-bottom:20px;}
.card {padding:20px;border-radius:18px;color:white;box-shadow:0 8px 22px rgba(0,0,0,.15);}
.blue{background:linear-gradient(135deg,#005BEA,#00C6FB);}
.orange{background:linear-gradient(135deg,#F7971E,#FFD200);}
.green{background:linear-gradient(135deg,#11998E,#38EF7D);}
.purple{background:linear-gradient(135deg,#7F00FF,#E100FF);}
.red{background:linear-gradient(135deg,#FF416C,#FF4B2B);}
.card-title{font-size:14px;font-weight:700;}
.card-value{font-size:36px;font-weight:800;margin-top:10px;}
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
    data = {k: "" for k in ["Container No","DO No","BL No","Acente","Consignee","Vessel","Voyage","Size/Type","Seal No","EXP Date"]}

    cont = re.search(r"\b[A-Z]{4}\d{7}\b", text)
    if cont: data["Container No"] = cont.group(0)

    data["DO No"] = find_first(r"DELIVERY ORDER NO\s*[:\-]?\s*([A-Z0-9]+)", text)
    data["BL No"] = find_first(r"B/L\s*-\s*NO\s*[:\-]?\s*([A-Z0-9]+)", text)
    data["Voyage"] = find_first(r"VOYAGE\s*[:\-]?\s*([A-Z0-9]+)", text)

    size = re.search(r"\b(20GP|20DC|20DV|40GP|40HC|40HQ|45HC|45GP)\b", text, re.IGNORECASE)
    if size: data["Size/Type"] = size.group(1).upper()

    seal = re.search(r"SEAL\s*([A-Z0-9]{5,15})", text, re.IGNORECASE)
    if seal: data["Seal No"] = seal.group(1)

    exp = re.search(r"EXP DATE\s*.*?(\d{2}-[A-Z]{3}-\d{2,4})", text, re.IGNORECASE | re.DOTALL)
    if exp: data["EXP Date"] = exp.group(1).upper()

    if "CMA CGM" in text.upper(): data["Acente"] = "CMA CGM"
    elif "MSC" in text.upper(): data["Acente"] = "MSC"
    elif "MAERSK" in text.upper(): data["Acente"] = "MAERSK"

    return data

def login():
    st.markdown('<div class="header"><h1>⚓ ALPORT CFS SYSTEM</h1><p>Delivery Order & Container Tracking Platform</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.2,1])
    with c2:
        st.subheader("🔐 Kullanıcı Girişi")
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            if u in USERS and USERS[u]["password"] == p:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.role = USERS[u]["role"]
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı.")

def card(col, title, value, css):
    col.markdown(f'<div class="card {css}"><div class="card-title">{title}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

create_file()
df = read_data()
role = st.session_state.role

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=190)

st.sidebar.markdown("## ⚓ ALPORT")
st.sidebar.markdown("### CFS SYSTEM")
st.sidebar.markdown("---")

if role == "Admin":
    menus = ["Dashboard","Delivery Order Kaydı","Kayıt Düzenle / Sil","Kayıt Ara","Tüm Kayıtlar","Excel İndir"]
elif role == "CFS Personeli":
    menus = ["Dashboard","Delivery Order Kaydı","Kayıt Düzenle / Sil","Kayıt Ara","Tüm Kayıtlar"]
else:
    menus = ["Dashboard","Kayıt Ara","Tüm Kayıtlar"]

menu = st.sidebar.radio("Menü", menus)

st.sidebar.markdown("---")
st.sidebar.write(f"👤 {st.session_state.username}")
st.sidebar.write(f"🔐 {role}")
if st.sidebar.button("Çıkış Yap"):
    st.session_state.clear()
    st.rerun()

st.markdown('<div class="header"><h1>⚓ ALPORT CFS AUTOMATION SYSTEM</h1><p>Banjul Terminal | Delivery Order & CFS Operation Tracking</p></div>', unsafe_allow_html=True)

if menu == "Dashboard":
    total = len(df)
    waiting = len(df[df["CFS Durumu"] == "Bekliyor"])
    opened = len(df[df["CFS Durumu"] == "CFS Açıldı"])
    delivered = len(df[df["CFS Durumu"] == "Delivery Yapıldı"])
    cancelled = len(df[df["CFS Durumu"] == "İptal"])

    c1,c2,c3,c4,c5 = st.columns(5)
    card(c1,"📦 TOPLAM",total,"blue")
    card(c2,"⏳ BEKLEYEN",waiting,"orange")
    card(c3,"✅ CFS AÇILDI",opened,"green")
    card(c4,"🚛 DELIVERY",delivered,"purple")
    card(c5,"⚠️ İPTAL",cancelled,"red")

    st.markdown("---")
    c1,c2 = st.columns(2)

    with c1:
        st.subheader("📊 Durum Dağılımı")
        status_df = df["CFS Durumu"].value_counts().reset_index()
        status_df.columns = ["Durum","Adet"]
        if not status_df.empty:
            st.plotly_chart(px.pie(status_df, names="Durum", values="Adet", hole=0.45), use_container_width=True)

    with c2:
        st.subheader("🕘 Son Kayıtlar")
        st.dataframe(df.tail(10), use_container_width=True)

elif menu == "Delivery Order Kaydı":
    st.subheader("📄 Delivery Order PDF Yükle")

    parsed = {k:"" for k in ["Container No","DO No","BL No","Acente","Consignee","Vessel","Voyage","Size/Type","Seal No","EXP Date"]}
    uploaded_pdf = st.file_uploader("Delivery Order PDF seç", type=["pdf"])
pdf_saved_path = ""

if uploaded_pdf is not None:
    try:
        text = extract_pdf_text(uploaded_pdf)
        parsed = parse_do(text)

        temp_container = parsed["Container No"] if parsed["Container No"] else "UNKNOWN"
        safe_name = f"{temp_container}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_saved_path = os.path.join(PDF_FOLDER, safe_name)

        with open(pdf_saved_path, "wb") as f:
            f.write(uploaded_pdf.getbuffer())

        st.success("PDF okundu ve arşive kaydedildi.")
        st.info(f"PDF Dosya Yolu: {pdf_saved_path}")

    except Exception as e:
        st.error(f"PDF okunamadı: {e}")
    c1,c2 = st.columns(2)
    with c1:
        container_no = st.text_input("Container No", parsed["Container No"])
        do_no = st.text_input("Delivery Order No", parsed["DO No"])
        bl_no = st.text_input("B/L No", parsed["BL No"])
        acente = st.text_input("Acente", parsed["Acente"])
        consignee = st.text_input("Consignee", parsed["Consignee"])
    with c2:
        vessel = st.text_input("Vessel", parsed["Vessel"])
        voyage = st.text_input("Voyage", parsed["Voyage"])
        size_type = st.text_input("Size / Type", parsed["Size/Type"])
        seal_no = st.text_input("Seal No", parsed["Seal No"])
        exp_date = st.text_input("EXP Date", parsed["EXP Date"])

    st.markdown("### CFS Operasyon Bilgileri")
    c3,c4 = st.columns(2)
    with c3:
        cfs_durumu = st.selectbox("CFS Durumu", ["Bekliyor","CFS Açıldı","Delivery Yapıldı","İptal"])
        acim_tarihi = st.text_input("Açım Tarihi")
        cargo_type = st.text_input("Cargo Type")
        quantity = st.text_input("Quantity")
    with c4:
        hasar = st.selectbox("Hasar Durumu", ["Yok","Var"])
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
"PDF Dosya Yolu": pdf_saved_path,
"Not": note.strip()
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Kayıt başarıyla kaydedildi.")

elif menu == "Kayıt Düzenle / Sil":
    st.subheader("✏️ Kayıt Düzenle / Sil")

    search_edit = st.text_input("Container No / DO No / BL No girin")

    if search_edit:
        result = df[
            df["Container No"].astype(str).str.contains(search_edit, case=False, na=False) |
            df["DO No"].astype(str).str.contains(search_edit, case=False, na=False) |
            df["BL No"].astype(str).str.contains(search_edit, case=False, na=False)
        ]

        if result.empty:
            st.warning("Kayıt bulunamadı.")
        else:
            st.dataframe(result, use_container_width=True)
            selected_index = st.selectbox("Düzenlenecek kaydı seç", result.index.tolist())
            row = df.loc[selected_index]

            c1,c2 = st.columns(2)
            with c1:
                edit_container = st.text_input("Container No", row["Container No"])
                edit_do = st.text_input("DO No", row["DO No"])
                edit_bl = st.text_input("BL No", row["BL No"])
                edit_acente = st.text_input("Acente", row["Acente"])
                edit_consignee = st.text_input("Consignee", row["Consignee"])
                edit_vessel = st.text_input("Vessel", row["Vessel"])
            with c2:
                edit_voyage = st.text_input("Voyage", row["Voyage"])
                edit_size = st.text_input("Size/Type", row["Size/Type"])
                edit_seal = st.text_input("Seal No", row["Seal No"])
                edit_exp = st.text_input("EXP Date", row["EXP Date"])
                statuses = ["Bekliyor","CFS Açıldı","Delivery Yapıldı","İptal"]
                damages = ["Yok","Var"]
                edit_status = st.selectbox("CFS Durumu", statuses, index=statuses.index(row["CFS Durumu"]) if row["CFS Durumu"] in statuses else 0)
                edit_damage = st.selectbox("Hasar Durumu", damages, index=damages.index(row["Hasar Durumu"]) if row["Hasar Durumu"] in damages else 0)

            edit_note = st.text_area("Not", row["Not"])

            csave, cdel = st.columns(2)
            with csave:
                if st.button("💾 Değişiklikleri Kaydet", use_container_width=True):
                    df.loc[selected_index, "Container No"] = edit_container.upper().strip()
                    df.loc[selected_index, "DO No"] = edit_do.strip()
                    df.loc[selected_index, "BL No"] = edit_bl.strip()
                    df.loc[selected_index, "Acente"] = edit_acente.strip()
                    df.loc[selected_index, "Consignee"] = edit_consignee.strip()
                    df.loc[selected_index, "Vessel"] = edit_vessel.strip()
                    df.loc[selected_index, "Voyage"] = edit_voyage.strip()
                    df.loc[selected_index, "Size/Type"] = edit_size.strip()
                    df.loc[selected_index, "Seal No"] = edit_seal.strip()
                    df.loc[selected_index, "EXP Date"] = edit_exp.strip()
                    df.loc[selected_index, "CFS Durumu"] = edit_status
                    df.loc[selected_index, "Hasar Durumu"] = edit_damage
                    df.loc[selected_index, "Not"] = edit_note.strip()
                    save_data(df)
                    st.success("Kayıt güncellendi.")

            with cdel:
                if role == "Admin":
                    if st.button("🗑️ Kaydı Sil", use_container_width=True):
                        df = df.drop(index=selected_index).reset_index(drop=True)
                        save_data(df)
                        st.success("Kayıt silindi.")
                else:
                    st.info("Silme yetkisi sadece Admin kullanıcısındadır.")
    else:
        st.info("Düzenleme için arama yapın.")

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
            "Excel Dosyasını İndir",
            data=file,
            file_name="CFS_KAYITLARI.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
