import streamlit as st

USERS = {
    "admin": {"password": "1234", "role": "Admin"},
    "cfs": {"password": "1234", "role": "CFS Personeli"},
    "viewer": {"password": "1234", "role": "Viewer"},
}

def login_screen():
    st.markdown("""
    <div class="login-card">
        <div class="login-title">⚓ ALPORT CFS SYSTEM</div>
        <div class="login-subtitle">Delivery Order & Container Tracking</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("### Kullanıcı Girişi")
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = USERS[username]["role"]
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı.")

def logout_button():
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"👤 **{st.session_state.get('username', '')}**")
    st.sidebar.markdown(f"🔐 {st.session_state.get('role', '')}")
    if st.sidebar.button("Çıkış Yap", use_container_width=True):
        st.session_state.clear()
        st.rerun()

def get_role():
    return st.session_state.get("role", "Viewer")
