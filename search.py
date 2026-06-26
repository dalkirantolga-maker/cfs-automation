from datetime import datetime
import pandas as pd
import streamlit as st
from modules.database import read_data, save_data
from modules.pdf_parser import extract_pdf_text, parse_delivery_order


def delivery_order_page():
    uploaded_pdf = st.file_uploader("Delivery Order PDF Yükle", type=["pdf"])

    parsed = {"Container No":"", "DO No":"", "BL No":"", "Acente":"", "Consignee":"", "Vessel":"", "Voyage":"", "Size/Type":"", "Seal No":"", "EXP Date":""}

    if uploaded_pdf is not None:
        try:
            text = extract_pdf_text(uploaded_pdf)
            parsed = parse_delivery_order(text)
            st.success("PDF okundu. Bilgileri kontrol edip kaydedebilirsiniz.")
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
    c1, c2 = st.columns(2)
    with c1:
        cfs_durumu = st.selectbox("CFS Durumu", ["Bekliyor", "CFS Açıldı", "Delivery Yapıldı", "İptal"])
        acim_tarihi = st.text_input("Açım Tarihi", placeholder="26-06-2026")
        cargo_type = st.text_input("Cargo Type")
        quantity = st.text_input("Quantity")
    with c2:
        hasar = st.selectbox("Hasar Durumu", ["Yok", "Var"])
        delivery_tarihi = st.text_input("Delivery Tarihi", placeholder="26-06-2026")
        truck_no = st.text_input("Truck No")
        driver_name = st.text_input("Driver Name")
        released_by = st.text_input("Released By")
    note = st.text_area("Not")

    if st.button("💾 Kaydet", use_container_width=True):
        if not container_no.strip():
            st.error("Container No boş olamaz.")
            return
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
            "Kayıt Yapan Kullanıcı": st.session_state.get("username", ""),
            "Not": note.strip(),
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("Kayıt başarıyla kaydedildi.")
