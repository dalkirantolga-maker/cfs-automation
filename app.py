!pip install ...
import streamlit as st
!pip install ipywidgets pdfplumber openpyxl -q

import os, re, shutil
import pandas as pd
import pdfplumber
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
from google.colab import files
from datetime import datetime

# ==============================
# KLASÖR VE DOSYA AYARLARI
# ==============================
DATA_FILE = "CFS_KAYITLARI.xlsx"
PDF_FOLDER = "DELIVERY_ORDER_PDF"
os.makedirs(PDF_FOLDER, exist_ok=True)

columns = [
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
    "PDF Dosya Yolu",
    "Not"
]

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=columns).to_excel(DATA_FILE, index=False)

# ==============================
# PDF OKUMA FONKSİYONU
# ==============================
def pdf_text_extract(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += "\n" + page_text
    except Exception as e:
        print("PDF okunamadı:", e)
    return text

def find_value(pattern, text, default=""):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else default

def parse_delivery_order(pdf_path):
    text = pdf_text_extract(pdf_path)

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

    # Container No
    cont_match = re.search(r"\b[A-Z]{4}\d{7}\b", text)
    if cont_match:
        data["Container No"] = cont_match.group(0)

    # Delivery Order No
    data["DO No"] = find_value(r"DELIVERY ORDER NO\s*[:\-]?\s*([A-Z0-9]+)", text)

    # BL No
    data["BL No"] = find_value(r"B/L\s*-\s*NO\s*[:\-]?\s*([A-Z0-9]+)", text)

    # Vessel
    data["Vessel"] = find_value(r"VESSEL\s*[:\-]?\s*([A-Z0-9\s]+)", text)
    if data["Vessel"]:
        data["Vessel"] = data["Vessel"].split("\n")[0].strip()

    # Voyage
    data["Voyage"] = find_value(r"VOYAGE\s*[:\-]?\s*([A-Z0-9]+)", text)

    # Size / Type
    size_match = re.search(r"\b(20GP|20DV|20DC|40GP|40HC|40HQ|45HC)\b", text, re.IGNORECASE)
    if size_match:
        data["Size/Type"] = size_match.group(1).upper()

    # Seal No
    seal_match = re.search(r"SEAL\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if seal_match:
        data["Seal No"] = seal_match.group(1)

    # EXP Date
    exp_match = re.search(r"EXP DATE\s*.*?(\d{2}-[A-Z]{3}-\d{2,4})", text, re.IGNORECASE | re.DOTALL)
    if not exp_match:
        exp_match = re.search(r"\b(\d{2}-[A-Z]{3}-\d{2})\b", text, re.IGNORECASE)
    if exp_match:
        data["EXP Date"] = exp_match.group(1).upper()

    # Acente
    if "CMA CGM" in text.upper():
        data["Acente"] = "CMA CGM"

    # Consignee - basit tahmin
    lines = [x.strip() for x in text.split("\n") if x.strip()]
    for line in lines[:20]:
        if not any(word in line.upper() for word in ["DELIVERY", "PAGE", "CMA", "B/L", "VESSEL", "VOYAGE"]):
            if len(line) > 3:
                data["Consignee"] = line
                break

    return data, text

# ==============================
# KAYIT FONKSİYONLARI
# ==============================
def load_data():
    return pd.read_excel(DATA_FILE)

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

def show_header():
    display(HTML("""
    <div style="
        background: linear-gradient(90deg, #002b5c, #0077b6);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-family: Arial;
        margin-bottom: 20px;">
        <h1>⚓ CFS OTOMASYON SİSTEMİ</h1>
        <h3>Delivery Order & Konteyner Takip Paneli</h3>
    </div>
    """))

# ==============================
# WIDGET ALANLARI
# ==============================
container_no = widgets.Text(description="Container:", layout=widgets.Layout(width="400px"))
do_no = widgets.Text(description="DO No:", layout=widgets.Layout(width="400px"))
bl_no = widgets.Text(description="BL No:", layout=widgets.Layout(width="400px"))
acente = widgets.Text(description="Acente:", layout=widgets.Layout(width="400px"))
consignee = widgets.Text(description="Consignee:", layout=widgets.Layout(width="400px"))
vessel = widgets.Text(description="Vessel:", layout=widgets.Layout(width="400px"))
voyage = widgets.Text(description="Voyage:", layout=widgets.Layout(width="400px"))
size_type = widgets.Text(description="Size/Type:", layout=widgets.Layout(width="400px"))
seal_no = widgets.Text(description="Seal No:", layout=widgets.Layout(width="400px"))
exp_date = widgets.Text(description="EXP Date:", layout=widgets.Layout(width="400px"))

cfs_durumu = widgets.Dropdown(
    options=["Bekliyor", "CFS Açıldı", "Delivery Yapıldı", "İptal"],
    description="Durum:",
    layout=widgets.Layout(width="400px")
)

acim_tarihi = widgets.Text(description="Açım Tarihi:", placeholder="örn: 26-06-2026", layout=widgets.Layout(width="400px"))
cargo_type = widgets.Text(description="Cargo:", layout=widgets.Layout(width="400px"))
quantity = widgets.Text(description="Quantity:", layout=widgets.Layout(width="400px"))
hasar = widgets.Dropdown(options=["Yok", "Var"], description="Hasar:", layout=widgets.Layout(width="400px"))
delivery_tarihi = widgets.Text(description="Delivery:", placeholder="örn: 26-06-2026", layout=widgets.Layout(width="400px"))
truck_no = widgets.Text(description="Truck No:", layout=widgets.Layout(width="400px"))
driver = widgets.Text(description="Driver:", layout=widgets.Layout(width="400px"))
released_by = widgets.Text(description="Released:", layout=widgets.Layout(width="400px"))
note = widgets.Textarea(description="Not:", layout=widgets.Layout(width="500px", height="80px"))

pdf_path_global = ""

# ==============================
# BUTON FONKSİYONLARI
# ==============================
def upload_pdf_clicked(b):
    global pdf_path_global

    clear_output()
    show_header()

    print("Lütfen Delivery Order PDF dosyasını seçin...")
    uploaded = files.upload()

    if not uploaded:
        print("PDF yüklenmedi.")
        return

    file_name = list(uploaded.keys())[0]
    original_path = file_name

    data, text = parse_delivery_order(original_path)

    cont = data["Container No"] if data["Container No"] else "UNKNOWN"
    new_pdf_name = f"{cont}_DELIVERY_ORDER.pdf"
    new_pdf_path = os.path.join(PDF_FOLDER, new_pdf_name)
    shutil.copy(original_path, new_pdf_path)
    pdf_path_global = new_pdf_path

    container_no.value = data["Container No"]
    do_no.value = data["DO No"]
    bl_no.value = data["BL No"]
    acente.value = data["Acente"]
    consignee.value = data["Consignee"]
    vessel.value = data["Vessel"]
    voyage.value = data["Voyage"]
    size_type.value = data["Size/Type"]
    seal_no.value = data["Seal No"]
    exp_date.value = data["EXP Date"]

    print("✅ PDF yüklendi ve bilgiler okundu.")
    print("PDF Dosya Yolu:", pdf_path_global)

    display_form()

def save_clicked(b):
    global pdf_path_global

    df = load_data()

    if container_no.value.strip() == "":
        print("❌ Container No boş olamaz.")
        return

    new_row = {
        "Kayıt Tarihi": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "Container No": container_no.value.upper().strip(),
        "DO No": do_no.value.strip(),
        "BL No": bl_no.value.strip(),
        "Acente": acente.value.strip(),
        "Consignee": consignee.value.strip(),
        "Vessel": vessel.value.strip(),
        "Voyage": voyage.value.strip(),
        "Size/Type": size_type.value.strip(),
        "Seal No": seal_no.value.strip(),
        "EXP Date": exp_date.value.strip(),
        "CFS Durumu": cfs_durumu.value,
        "Açım Tarihi": acim_tarihi.value.strip(),
        "Cargo Type": cargo_type.value.strip(),
        "Quantity": quantity.value.strip(),
        "Hasar Durumu": hasar.value,
        "Delivery Tarihi": delivery_tarihi.value.strip(),
        "Truck No": truck_no.value.strip(),
        "Driver Name": driver.value.strip(),
        "Released By": released_by.value.strip(),
        "PDF Dosya Yolu": pdf_path_global,
        "Not": note.value.strip()
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)

    print("✅ Kayıt başarıyla kaydedildi.")

def search_clicked(b):
    clear_output()
    show_header()

    aranan = search_box.value.upper().strip()
    df = load_data()

    if aranan == "":
        print("❌ Arama alanı boş olamaz.")
        display_main()
        return

    result = df[
        df["Container No"].astype(str).str.upper().str.contains(aranan, na=False) |
        df["DO No"].astype(str).str.upper().str.contains(aranan, na=False) |
        df["BL No"].astype(str).str.upper().str.contains(aranan, na=False)
    ]

    if result.empty:
        print("❌ Kayıt bulunamadı.")
    else:
        display(HTML("<h3>🔎 Arama Sonuçları</h3>"))
        display(result)

    display_main()

def list_clicked(b):
    clear_output()
    show_header()
    df = load_data()
    display(HTML("<h3>📋 Tüm CFS Kayıtları</h3>"))
    display(df)
    display_main()

def download_excel_clicked(b):
    files.download(DATA_FILE)

def download_all_clicked(b):
    zip_name = "CFS_SISTEM_YEDEK.zip"
    if os.path.exists(zip_name):
        os.remove(zip_name)

    shutil.make_archive("CFS_SISTEM_YEDEK", "zip", ".", PDF_FOLDER)

    temp_folder = "TEMP_CFS_BACKUP"
    os.makedirs(temp_folder, exist_ok=True)
    shutil.copy(DATA_FILE, os.path.join(temp_folder, DATA_FILE))

    shutil.make_archive("CFS_EXCEL_YEDEK", "zip", temp_folder)

    print("✅ PDF klasörü indiriliyor...")
    files.download(zip_name)
    print("✅ Excel dosyası indiriliyor...")
    files.download(DATA_FILE)

def clear_form_clicked(b):
    global pdf_path_global
    pdf_path_global = ""

    for w in [
        container_no, do_no, bl_no, acente, consignee,
        vessel, voyage, size_type, seal_no, exp_date,
        acim_tarihi, cargo_type, quantity,
        delivery_tarihi, truck_no, driver, released_by, note
    ]:
        w.value = ""

    cfs_durumu.value = "Bekliyor"
    hasar.value = "Yok"
    print("🧹 Form temizlendi.")

# ==============================
# BUTONLAR
# ==============================
upload_pdf_btn = widgets.Button(description="📎 Delivery Order PDF Yükle", button_style="info")
save_btn = widgets.Button(description="💾 Kaydet", button_style="success")
clear_btn = widgets.Button(description="🧹 Formu Temizle", button_style="warning")

search_box = widgets.Text(description="Ara:", placeholder="Container / DO / BL No", layout=widgets.Layout(width="400px"))
search_btn = widgets.Button(description="🔎 Ara", button_style="primary")
list_btn = widgets.Button(description="📋 Tüm Liste", button_style="")
download_excel_btn = widgets.Button(description="⬇️ Excel İndir", button_style="success")
download_all_btn = widgets.Button(description="📦 PDF Yedek İndir", button_style="")

upload_pdf_btn.on_click(upload_pdf_clicked)
save_btn.on_click(save_clicked)
clear_btn.on_click(clear_form_clicked)
search_btn.on_click(search_clicked)
list_btn.on_click(list_clicked)
download_excel_btn.on_click(download_excel_clicked)
download_all_btn.on_click(download_all_clicked)

# ==============================
# EKRANLAR
# ==============================
def display_form():
    display(HTML("<h3>📝 CFS Kayıt Formu</h3>"))
    display(upload_pdf_btn)

    display(widgets.HBox([container_no, do_no]))
    display(widgets.HBox([bl_no, acente]))
    display(widgets.HBox([consignee, vessel]))
    display(widgets.HBox([voyage, size_type]))
    display(widgets.HBox([seal_no, exp_date]))

    display(HTML("<hr><h4>CFS Operasyon Bilgileri</h4>"))
    display(widgets.HBox([cfs_durumu, acim_tarihi]))
    display(widgets.HBox([cargo_type, quantity]))
    display(widgets.HBox([hasar, delivery_tarihi]))
    display(widgets.HBox([truck_no, driver]))
    display(released_by)
    display(note)

    display(widgets.HBox([save_btn, clear_btn]))

def display_main():
    display(HTML("<hr><h3>🔍 Arama ve Rapor</h3>"))
    display(widgets.HBox([search_box, search_btn]))
    display(widgets.HBox([list_btn, download_excel_btn, download_all_btn]))

def start_system():
    clear_output()
    show_header()
    display_form()
    display_main()

start_system()
