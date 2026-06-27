import os
import re
from datetime import datetime, date
from io import BytesIO

import pandas as pd
import pdfplumber
import plotly.express as px
import streamlit as st

APP_NAME = "ALPORT CFS AUTOMATION SYSTEM"
DATA_FILE = "CFS_KAYITLARI.xlsx"
PDF_FOLDER = "storage/do_pdfs"
UPLOAD_FOLDER = "storage/uploads"
LOGO_PATH = "assets/logo.png"

USERS = {
    "admin": {"password": "1234", "role": "Admin"},
    "cfs": {"password": "1234", "role": "CFS Personeli"},
    "viewer": {"password": "1234", "role": "Viewer"},
}

COLUMNS = [
    "Kayıt ID",
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
    "CFS Lokasyon",
    "Açım Tarihi",
    "Cargo Type",
    "Quantity",
    "Hasar Durumu",
    "Delivery Tarihi",
    "Truck No",
    "Driver Name",
    "Released By",
    "Kayıt Yapan",
    "Son Güncelleyen",
    "Son Güncelleme",
    "PDF Dosya Yolu",
    "Not",
]

STATUS_LIST = ["Bekliyor", "CFS Açıldı", "Delivery Yapıldı", "İptal"]
DAMAGE_LIST = ["Yok", "Var"]

st.set_page_config(page_title=APP_NAME, page_icon="⚓", layout="wide")

st.markdown(
    """
<style>
[data-testid="stSidebar"] {background: linear-gradient(180deg,#001B3A,#003B73);} 
[data-testid="stSidebar"] * {color:white!important;}
.block-container {padding-top:1.1rem; padding-bottom:2rem;}
.header {background:linear-gradient(90deg,#001B3A,#005B96);padding:22px;border-radius:18px;color:white;margin-bottom:20px;}
.header h1 {margin:0;font-size:30px;}
.header p {margin:5px 0 0 0;opacity:.9;}
.login-box {background:#ffffff; padding:25px; border-radius:18px; box-shadow:0 6px 22px rgba(0,0,0,.10);}
.card {padding:20px;border-radius:18px;color:white;box-shadow:0 8px 22px rgba(0,0,0,.15);min-height:120px;}
.blue{background:linear-gradient(135deg,#005BEA,#00C6FB);} 
.orange{background:linear-gradient(135deg,#F7971E,#FFD200);} 
.green{background:linear-gradient(135deg,#11998E,#38EF7D);} 
.purple{background:linear-gradient(135deg,#7F00FF,#E100FF);} 
.red{background:linear-gradient(135deg,#FF416C,#FF4B2B);} 
.dark{background:linear-gradient(135deg,#001B3A,#005B96);} 
.card-title{font-size:14px;font-weight:700;letter-spacing:.3px;}
.card-value{font-size:36px;font-weight:800;margin-top:10px;}
.card-sub{font-size:12px;opacity:.9;margin-top:5px;}
.small-note{font-size:12px;color:#5b6472;}
.footer {text-align:center; color:#6c757d; font-size:12px; margin-top:30px;}
.stButton > button {border-radius:10px; font-weight:700;}
</style>
""",
    unsafe_allow_html=True,
)


def ensure_storage() -> None:
    os.makedirs(PDF_FOLDER, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs("assets", exist_ok=True)


def create_file() -> None:
    ensure_storage()
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=COLUMNS).to_excel(DATA_FILE, index=False)


def read_data() -> pd.DataFrame:
    create_file()
    try:
        df = pd.read_excel(DATA_FILE)
    except Exception:
        df = pd.DataFrame(columns=COLUMNS)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[COLUMNS]


def save_data(df: pd.DataFrame) -> None:
    df = df.copy()
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df[COLUMNS].to_excel(DATA_FILE, index=False)


def next_record_id(df: pd.DataFrame) -> str:
    if df.empty or "Kayıt ID" not in df.columns:
        return "CFS-000001"
    nums = []
    for val in df["Kayıt ID"].astype(str):
        m = re.search(r"(\d+)$", val)
        if m:
            nums.append(int(m.group(1)))
    return f"CFS-{(max(nums) + 1 if nums else 1):06d}"


def extract_pdf_text(uploaded_file) -> str:
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += "\n" + (page.extract_text() or "")
    return text


def find_first(pattern: str, text: str) -> str:
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_do(text: str) -> dict:
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

    upper = text.upper()
    if "CMA CGM" in upper:
        data["Acente"] = "CMA CGM"
    elif "MSC" in upper:
        data["Acente"] = "MSC"
    elif "MAERSK" in upper:
        data["Acente"] = "MAERSK"

    lines = [x.strip() for x in text.split("\n") if x.strip()]
    for line in lines[:20]:
        u = line.upper()
        if not any(x in u for x in ["DELIVERY", "PAGE", "VESSEL", "VOYAGE", "CMA", "MSC", "MAERSK", "B/L", "CONTAINER"]):
            if len(line) > 3:
                data["Consignee"] = line
                break
    return data


def save_uploaded_pdf(uploaded_file, container_no: str) -> str:
    ensure_storage()
    safe_container = re.sub(r"[^A-Z0-9_-]", "", (container_no or "UNKNOWN").upper()) or "UNKNOWN"
    safe_name = f"{safe_container}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join(PDF_FOLDER, safe_name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


def parse_exp_date(value):
    if pd.isna(value) or str(value).strip() == "":
        return pd.NaT
    return pd.to_datetime(str(value), errors="coerce", dayfirst=True)


def status_badge(status: str) -> str:
    colors = {
        "Bekliyor": "#fff3cd",
        "CFS Açıldı": "#d4edda",
        "Delivery Yapıldı": "#d7c8ff",
        "İptal": "#f8d7da",
    }
    text_colors = {
        "Bekliyor": "#856404",
        "CFS Açıldı": "#155724",
        "Delivery Yapıldı": "#3b168c",
        "İptal": "#721c24",
    }
    bg = colors.get(status, "#e9ecef")
    fg = text_colors.get(status, "#212529")
    return f'<span style="background:{bg};color:{fg};padding:5px 10px;border-radius:8px;font-weight:700;">{status}</span>'


def render_header() -> None:
    st.markdown(
        f'<div class="header"><h1>⚓ {APP_NAME}</h1><p>Banjul Terminal | Delivery Order & CFS Operation Tracking</p></div>',
        unsafe_allow_html=True,
    )


def render_sidebar(role: str) -> str:
    if os.path.exists(LOGO_PATH):
        st.sidebar.image(LOGO_PATH, width=190)
    st.sidebar.markdown("## ⚓ ALPORT")
    st.sidebar.markdown("### CFS SYSTEM")
    st.sidebar.markdown("---")
    if role == "Admin":
        menus = ["Dashboard", "Delivery Order Kaydı", "Kayıt Düzenle / Sil", "Kayıt Ara", "Tüm Kayıtlar", "Raporlar", "Excel İndir"]
    elif role == "CFS Personeli":
        menus = ["Dashboard", "Delivery Order Kaydı", "Kayıt Düzenle / Sil", "Kayıt Ara", "Tüm Kayıtlar", "Raporlar"]
    else:
        menus = ["Dashboard", "Kayıt Ara", "Tüm Kayıtlar", "Raporlar"]
    menu = st.sidebar.radio("Menü", menus)
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **{st.session_state.username}**")
    st.sidebar.write(f"🔐 {role}")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.clear()
        st.rerun()
    return menu


def login_screen() -> None:
    st.markdown(
        '<div class="header"><h1>⚓ ALPORT CFS SYSTEM</h1><p>Delivery Order & Container Tracking Platform</p></div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)


def metric_card(col, title: str, value, sub: str, css: str) -> None:
    col.markdown(
        f'<div class="card {css}"><div class="card-title">{title}</div><div class="card-value">{value}</div><div class="card-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def page_dashboard(df: pd.DataFrame) -> None:
    st.subheader("📊 Dashboard")
    total = len(df)
    waiting = len(df[df["CFS Durumu"] == "Bekliyor"])
    opened = len(df[df["CFS Durumu"] == "CFS Açıldı"])
    delivered = len(df[df["CFS Durumu"] == "Delivery Yapıldı"])
    cancelled = len(df[df["CFS Durumu"] == "İptal"])

    c1, c2, c3, c4, c5 = st.columns(5)
    metric_card(c1, "📦 TOPLAM", total, "Tüm kayıtlar", "blue")
    metric_card(c2, "⏳ BEKLEYEN", waiting, "İşlem bekleyen", "orange")
    metric_card(c3, "✅ CFS AÇILDI", opened, "CFS işlemi açıldı", "green")
    metric_card(c4, "🚛 DELIVERY", delivered, "Teslim edilen", "purple")
    metric_card(c5, "⚠️ İPTAL", cancelled, "İptal kayıt", "red")

    st.markdown("---")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.subheader("📊 Durum Dağılımı")
        status_df = df["CFS Durumu"].replace("", "Boş").value_counts().reset_index()
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
        soon = temp[(temp["Kalan Gün"] >= 0) & (temp["Kalan Gün"] <= 7)].sort_values("Kalan Gün")
        if soon.empty:
            st.success("7 gün içinde yaklaşan EXP Date yok.")
        else:
            st.dataframe(soon[["Container No", "DO No", "EXP Date", "Kalan Gün", "CFS Durumu"]], use_container_width=True)

    st.subheader("🕘 Son Kayıtlar")
    st.dataframe(df.tail(10), use_container_width=True)


def page_delivery_order(df: pd.DataFrame) -> None:
    st.subheader("📄 Delivery Order PDF Yükle")
    parsed = {k: "" for k in ["Container No", "DO No", "BL No", "Acente", "Consignee", "Vessel", "Voyage", "Size/Type", "Seal No", "EXP Date"]}
    pdf_saved_path = ""
    uploaded_pdf = st.file_uploader("Delivery Order PDF seç", type=["pdf"])

    if uploaded_pdf is not None:
        try:
            text = extract_pdf_text(uploaded_pdf)
            parsed = parse_do(text)
            pdf_saved_path = save_uploaded_pdf(uploaded_pdf, parsed.get("Container No", "UNKNOWN"))
            st.success("PDF okundu ve arşive kaydedildi.")
            st.info(f"PDF Dosya Yolu: {pdf_saved_path}")
        except Exception as e:
            st.error(f"PDF okunamadı: {e}")

    c1, c2 = st.columns(2)
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
    c3, c4 = st.columns(2)
    with c3:
        cfs_durumu = st.selectbox("CFS Durumu", STATUS_LIST)
        cfs_location = st.text_input("CFS Lokasyon", placeholder="Örn: A01 / B12 / CFS-3")
        acim_tarihi = st.text_input("Açım Tarihi", placeholder="Örn: 26-06-2026")
        cargo_type = st.text_input("Cargo Type")
        quantity = st.text_input("Quantity")
    with c4:
        hasar = st.selectbox("Hasar Durumu", DAMAGE_LIST)
        delivery_tarihi = st.text_input("Delivery Tarihi", placeholder="Örn: 26-06-2026")
        truck_no = st.text_input("Truck No")
        driver_name = st.text_input("Driver Name")
        released_by = st.text_input("Released By")
    note = st.text_area("Not")

    if st.button("💾 Kaydet", use_container_width=True):
        if not container_no.strip():
            st.error("Container No boş olamaz.")
        else:
            new_row = {
                "Kayıt ID": next_record_id(df),
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
                "CFS Lokasyon": cfs_location.strip(),
                "Açım Tarihi": acim_tarihi.strip(),
                "Cargo Type": cargo_type.strip(),
                "Quantity": quantity.strip(),
                "Hasar Durumu": hasar,
                "Delivery Tarihi": delivery_tarihi.strip(),
                "Truck No": truck_no.strip(),
                "Driver Name": driver_name.strip(),
                "Released By": released_by.strip(),
                "Kayıt Yapan": st.session_state.username,
                "Son Güncelleyen": "",
                "Son Güncelleme": "",
                "PDF Dosya Yolu": pdf_saved_path,
                "Not": note.strip(),
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Kayıt başarıyla kaydedildi.")


def page_edit_delete(df: pd.DataFrame, role: str) -> None:
    st.subheader("✏️ Kayıt Düzenle / Sil")
    search_edit = st.text_input("Container No / DO No / BL No girin")
    if not search_edit:
        st.info("Düzenleme için arama yapın.")
        return
    result = df[
        df["Container No"].astype(str).str.contains(search_edit, case=False, na=False) |
        df["DO No"].astype(str).str.contains(search_edit, case=False, na=False) |
        df["BL No"].astype(str).str.contains(search_edit, case=False, na=False)
    ]
    if result.empty:
        st.warning("Kayıt bulunamadı.")
        return
    st.dataframe(result, use_container_width=True)
    selected_index = st.selectbox("Düzenlenecek kaydı seç", result.index.tolist())
    row = df.loc[selected_index]

    c1, c2 = st.columns(2)
    with c1:
        edit_container = st.text_input("Container No", row["Container No"])
        edit_do = st.text_input("DO No", row["DO No"])
        edit_bl = st.text_input("BL No", row["BL No"])
        edit_acente = st.text_input("Acente", row["Acente"])
        edit_consignee = st.text_input("Consignee", row["Consignee"])
        edit_vessel = st.text_input("Vessel", row["Vessel"])
        edit_cfs_location = st.text_input("CFS Lokasyon", row["CFS Lokasyon"])
    with c2:
        edit_voyage = st.text_input("Voyage", row["Voyage"])
        edit_size = st.text_input("Size/Type", row["Size/Type"])
        edit_seal = st.text_input("Seal No", row["Seal No"])
        edit_exp = st.text_input("EXP Date", row["EXP Date"])
        edit_status = st.selectbox("CFS Durumu", STATUS_LIST, index=STATUS_LIST.index(row["CFS Durumu"]) if row["CFS Durumu"] in STATUS_LIST else 0)
        edit_damage = st.selectbox("Hasar Durumu", DAMAGE_LIST, index=DAMAGE_LIST.index(row["Hasar Durumu"]) if row["Hasar Durumu"] in DAMAGE_LIST else 0)
    edit_note = st.text_area("Not", row["Not"])

    pdf_path = str(row.get("PDF Dosya Yolu", ""))
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button("📎 Kayıtlı DO PDF İndir", data=f, file_name=os.path.basename(pdf_path), mime="application/pdf")

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
            df.loc[selected_index, "CFS Lokasyon"] = edit_cfs_location.strip()
            df.loc[selected_index, "Hasar Durumu"] = edit_damage
            df.loc[selected_index, "Son Güncelleyen"] = st.session_state.username
            df.loc[selected_index, "Son Güncelleme"] = datetime.now().strftime("%d-%m-%Y %H:%M")
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


def page_search(df: pd.DataFrame) -> None:
    st.subheader("🔎 Kayıt Ara")
    search = st.text_input("Container / DO / BL / Vessel / Consignee ara")
    if not search:
        st.info("Arama yapmak için bilgi girin.")
        return
    result = df[
        df["Container No"].astype(str).str.contains(search, case=False, na=False) |
        df["DO No"].astype(str).str.contains(search, case=False, na=False) |
        df["BL No"].astype(str).str.contains(search, case=False, na=False) |
        df["Vessel"].astype(str).str.contains(search, case=False, na=False) |
        df["Consignee"].astype(str).str.contains(search, case=False, na=False)
    ]
    st.dataframe(result, use_container_width=True)


def page_records(df: pd.DataFrame) -> None:
    st.subheader("📋 Tüm CFS Kayıtları")
    filter_status = st.selectbox("Duruma göre filtrele", ["Tümü"] + STATUS_LIST)
    show_df = df if filter_status == "Tümü" else df[df["CFS Durumu"] == filter_status]
    st.dataframe(show_df, use_container_width=True)


def page_reports(df: pd.DataFrame) -> None:
    st.subheader("📈 Raporlar")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Acente Bazlı Kayıt")
        agency = df["Acente"].replace("", "Boş").value_counts().reset_index()
        agency.columns = ["Acente", "Adet"]
        if not agency.empty:
            st.plotly_chart(px.bar(agency, x="Acente", y="Adet"), use_container_width=True)
    with c2:
        st.markdown("#### Size/Type Bazlı Kayıt")
        sizes = df["Size/Type"].replace("", "Boş").value_counts().reset_index()
        sizes.columns = ["Size/Type", "Adet"]
        if not sizes.empty:
            st.plotly_chart(px.bar(sizes, x="Size/Type", y="Adet"), use_container_width=True)

    st.markdown("#### Hasar Durumu")
    damage = df["Hasar Durumu"].replace("", "Boş").value_counts().reset_index()
    damage.columns = ["Hasar", "Adet"]
    if not damage.empty:
        st.plotly_chart(px.pie(damage, names="Hasar", values="Adet"), use_container_width=True)


def page_excel(df: pd.DataFrame) -> None:
    st.subheader("⬇️ Excel İndir")
    st.dataframe(df, use_container_width=True)
    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button(
        "Excel Dosyasını İndir",
        data=output.getvalue(),
        file_name="CFS_KAYITLARI.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


def main():
    ensure_storage()
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        login_screen()
        st.stop()

    df = read_data()
    role = st.session_state.role
    menu = render_sidebar(role)
    render_header()

    if menu == "Dashboard":
        page_dashboard(df)
    elif menu == "Delivery Order Kaydı":
        page_delivery_order(df)
    elif menu == "Kayıt Düzenle / Sil":
        page_edit_delete(df, role)
    elif menu == "Kayıt Ara":
        page_search(df)
    elif menu == "Tüm Kayıtlar":
        page_records(df)
    elif menu == "Raporlar":
        page_reports(df)
    elif menu == "Excel İndir":
        page_excel(df)

    st.markdown('<div class="footer">© 2026 ALPORT BANJUL TERMINAL | CFS Automation System v2.0</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
