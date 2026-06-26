import streamlit as st

from modules.auth import login_screen, logout_button, get_role
from modules.database import init_db
from modules.layout import apply_theme, sidebar_header, page_header
from modules.dashboard import dashboard_page
from modules.delivery_order import delivery_order_page
from modules.search import search_page
from modules.records import records_page
from modules.reports import reports_page

st.set_page_config(
    page_title="ALPORT CFS System",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()
init_db()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

sidebar_header()
role = get_role()

if role == "Admin":
    menu_options = ["Dashboard", "Delivery Order Kaydı", "Kayıt Ara", "Tüm Kayıtlar", "Raporlar", "Excel İndir"]
elif role == "CFS Personeli":
    menu_options = ["Dashboard", "Delivery Order Kaydı", "Kayıt Ara", "Tüm Kayıtlar", "Raporlar"]
else:
    menu_options = ["Dashboard", "Kayıt Ara", "Tüm Kayıtlar"]

menu = st.sidebar.radio("Menü", menu_options)
logout_button()

page_header(menu)

if menu == "Dashboard":
    dashboard_page()
elif menu == "Delivery Order Kaydı":
    delivery_order_page()
elif menu == "Kayıt Ara":
    search_page()
elif menu == "Tüm Kayıtlar":
    records_page(download=False)
elif menu == "Raporlar":
    reports_page()
elif menu == "Excel İndir":
    records_page(download=True)
