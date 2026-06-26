import os
import pandas as pd

DATA_FILE = "data/CFS_KAYITLARI.xlsx"

COLUMNS = [
    "Kayıt Tarihi", "Container No", "DO No", "BL No", "Acente", "Consignee",
    "Vessel", "Voyage", "Size/Type", "Seal No", "EXP Date", "CFS Durumu",
    "Açım Tarihi", "Cargo Type", "Quantity", "Hasar Durumu", "Delivery Tarihi",
    "Truck No", "Driver Name", "Released By", "Kayıt Yapan Kullanıcı", "Not"
]

def init_db():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=COLUMNS).to_excel(DATA_FILE, index=False)

def read_data():
    init_db()
    df = pd.read_excel(DATA_FILE)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[COLUMNS]

def save_data(df):
    os.makedirs("data", exist_ok=True)
    df.to_excel(DATA_FILE, index=False)
