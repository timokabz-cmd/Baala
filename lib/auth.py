"""Simple shared-password admin gate, same pattern as the rooms app.
Role-based staff login (per-person PIN) can be layered on later; for
tonight, one admin password protects all back-of-house pages."""
import streamlit as st


def require_admin():
    if st.session_state.get("is_admin"):
        return True

    st.subheader("🔒 Staff / Admin Login")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == st.secrets.get("admin_password", ""):
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()
