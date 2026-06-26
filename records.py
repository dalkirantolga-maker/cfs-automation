import streamlit as st
from modules.database import read_data


def search_page():
    df = read_data()
    search = st.text_input("Container No / DO No / BL No / Vessel ile ara")
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
            st.dataframe(result, use_container_width=True, hide_index=True)
    else:
        st.info("Arama yapmak için bilgi girin.")
