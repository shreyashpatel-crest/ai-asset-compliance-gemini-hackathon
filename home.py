import streamlit as st


def load_app():
    st.switch_page("pages/dashboard.py")


if __name__ == "__main__":
    load_app()
