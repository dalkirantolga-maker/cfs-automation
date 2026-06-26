import streamlit as st
from modules.database import read_data, DATA_FILE


def records_page(download=False):
    df = read_data()
    st.dataframe(df, use_container_width=True, hide_index=True)
    if download:
        with open(DATA_FILE, "rb") as file:
            st.download_button(
                "⬇️ Excel Dosyasını İndir",
                data=file,
                file_name="CFS_KAYITLARI.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
