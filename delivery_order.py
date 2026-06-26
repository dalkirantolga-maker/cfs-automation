import streamlit as st
import plotly.express as px
from modules.database import read_data
from modules.layout import metric_card


def dashboard_page():
    df = read_data()
    total = len(df)
    waiting = len(df[df["CFS Durumu"] == "Bekliyor"]) if not df.empty else 0
    opened = len(df[df["CFS Durumu"] == "CFS Açıldı"]) if not df.empty else 0
    delivered = len(df[df["CFS Durumu"] == "Delivery Yapıldı"]) if not df.empty else 0
    cancelled = len(df[df["CFS Durumu"] == "İptal"]) if not df.empty else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    metric_card(c1, "📦 TOPLAM KAYIT", total, "Tüm zamanlar", "blue-card")
    metric_card(c2, "⏳ BEKLEYEN", waiting, "Bekleyen DO", "orange-card")
    metric_card(c3, "✅ CFS AÇILDI", opened, "CFS işlemi açıldı", "green-card")
    metric_card(c4, "🚛 DELIVERY YAPILDI", delivered, "Teslim edildi", "purple-card")
    metric_card(c5, "⚠️ İPTAL", cancelled, "İptal kayıtlar", "red-card")

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1, 1])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Durum Dağılımı")
        if total > 0:
            status_df = df["CFS Durumu"].value_counts().reset_index()
            status_df.columns = ["Durum", "Adet"]
            fig = px.pie(status_df, names="Durum", values="Adet", hole=0.55)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Henüz kayıt yok.")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Son Kayıtlar")
        st.dataframe(df.tail(8), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
