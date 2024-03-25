import json
from threading import Thread

import pandas as pd
import streamlit as st

import app_navbar
import core.scan as scanner
from constant import *
from core.chatbot.chat import chat_container
from utils import get_asset_data, load_chatbot_context, padding_markdown


def count_applications(assets_data):
    applications_counts = {}

    for _, asset in assets_data.items():
        for app in asset.get("application_installed", []):
            app_name = app.get("name")
            if app_name not in applications_counts:
                applications_counts[app_name] = 0

            applications_counts[app_name] += 1

    return applications_counts


def create_license_view(asset_data):
    with st.container(border=True, height=150):
        cols = st.columns(2)
        app_count = count_applications(asset_data)
        with open(LICENSE_FILE_PATH, "r") as f:
            license_data = json.load(f)

        change_column = True
        index = 0
        for key in license_data:
            if app_count.get(key, 0):
                if change_column:
                    index = 0
                else:
                    index = 1

                change_column = not change_column

                with cols[index]:
                    in_cols = st.columns([0.5, 3, 0.3, 0.5, 0.3, 0.5, 2, 3])
                    with in_cols[0]:
                        padding_markdown()
                        st.image(f"icons/{key}.svg", width=20)
                    with in_cols[1]:
                        st.markdown(
                            f"""
                            <p style="font-family: Montserrat; font-size: 14px; margin-top: 15px">{key}</p>
                        """,
                            unsafe_allow_html=True,
                        )
                    with in_cols[2]:
                        padding_markdown()
                        st.image(f"icons/license.svg", width=15)
                    with in_cols[3]:
                        st.markdown(
                            f"""
                            <p style="font-family: Montserrat; font-size: 14px; font-weight: bold; margin-top: 15px">{license_data.get(key,0)}</p>
                        """,
                            unsafe_allow_html=True,
                        )
                    with in_cols[4]:
                        padding_markdown()
                        st.image(f"icons/asset.svg", width=15)
                    with in_cols[5]:
                        st.markdown(
                            f"""
                            <p style="font-family: Montserrat; font-size: 14px; font-weight: bold; margin-top: 15px">{app_count[key]}</p>
                        """,
                            unsafe_allow_html=True,
                        )
                    with in_cols[6]:
                        status = ""
                        if license_data.get(key, 0) >= app_count[key]:
                            status = "Compliant"
                            st.markdown(
                                f"""
                                <div style="background-color: #DFF4EA; border: none; border-radius: 20px; width: 85px; height: 22px; text-align: center; margin-top: 15px">
                                    <p style="font-size: 14px; color: #2BB472">{status}</p>
                                </div>
                            """,
                                unsafe_allow_html=True,
                            )
                        else:
                            status = "Non-compliant"
                            st.markdown(
                                f"""
                                <div style="background-color: #FFDDDB; border: none; border-radius: 20px; width: 110px; height: 22px; text-align: center; margin-top: 15px">
                                    <p style="font-size: 14px; color: #FF4238">{status}</p>
                                </div>
                            """,
                                unsafe_allow_html=True,
                            )
                    with in_cols[7]:
                        view_asset = st.button("View Details", key=key)
                    if view_asset:
                        st.session_state["show_details"] = True
                        st.session_state["app_name"] = key


def prepare_asset_data(app_name, asset_data):
    prepared_data = []

    for _, data in asset_data.items():
        for item in data.get("application_installed", []):
            if item.get("name", "") == app_name:
                temp_data = {
                    "hostname": data.get("hostname", ""),
                    "last_login_user": data.get("last_login_user", ""),
                    "os_version": f"{data.get('os_version', '')} - {data.get('kernel_version', '')}",
                    "last_used_timestamp": item.get(
                        "last_used_timestamp", item.get("last_updated_timestamp", "")
                    ),
                    "version": item.get("version", ""),
                }
                prepared_data.append(temp_data)
                break

    return prepared_data


def build_asset_headers_manual(headers_name):
    header_cols = st.columns([1.5, 2, 3, 2, 1.5])
    for i, header in enumerate(headers_name):
        with header_cols[i]:
            st.markdown(
                f"""
                    <p style="font-family: Montserrat; font-weight: bold">{header}</p>
                """,
                unsafe_allow_html=True,
            )

    # Insert a visual separator (line) after the headers
    st.markdown(
        "<hr style='margin-top:0.25rem; margin-bottom:0.25rem; box-shadow: 0px 0px 1px rgba(0, 0, 0, 0.5)'/>",
        unsafe_allow_html=True,
    )


def load_asset_details(app_name, asset_data):
    prepared_data = prepare_asset_data(app_name, asset_data)

    headers_name = [
        "Asset ID",
        "Assigned To",
        "OS Version",
        "Application Version",
        "Last Used",
    ]

    asset_container = st.container(height=500)
    with asset_container:
        build_asset_headers_manual(headers_name)
        for asset in prepared_data:
            cols = st.columns([1.5, 2, 3, 2, 1.5])
            with cols[0]:
                st.markdown(
                    f"""<p style="font-family: Montserrat; font-size: 14px">{asset.get("hostname", "-")}</p>""",
                    unsafe_allow_html=True,
                )
            with cols[1]:
                st.markdown(
                    f"""<p style="font-family: Montserrat; font-size: 14px">{asset.get("last_login_user", "-")}</p>""",
                    unsafe_allow_html=True,
                )
            with cols[2]:
                st.markdown(
                    f"""<p style="font-family: Montserrat; font-size: 14px">{asset.get("os_version", "")}</p>""",
                    unsafe_allow_html=True,
                )
            with cols[3]:
                st.markdown(
                    f"""<p style="font-family: Montserrat; font-size: 14px">{asset.get("version", "")}</p>""",
                    unsafe_allow_html=True,
                )
            with cols[4]:
                st.markdown(
                    f"""<p style="font-family: Montserrat; font-size: 14px">{asset.get("last_used_timestamp", asset.get("last_updated_timestamp", ""))}</p>""",
                    unsafe_allow_html=True,
                )
            st.markdown(
                "<hr style='margin-top:0.25rem; margin-bottom:0.25rem;'/>",
                unsafe_allow_html=True,
            )


def load_chatbot():
    """
    A function to load the chatbot interface and styling using HTML and Streamlit components.
    """
    st.markdown(
        """
            <style>
                div[data-testid="stExpander"]
                {
                    right: 0;
                    bottom: 0;
                    position: fixed;
                    margin-bottom: 25px;
                    margin-right: 15px;
                    width: 25rem;
                    background-image: linear-gradient(to right, #7c97ff, #bc75fb);
                    border-radius: 5px;
                }
                div[data-testid="stExpander"] > details > summary
                {
                    padding: 0.75rem 1rem 0rem 1rem
                }
                .st-emotion-cache-g7r313
                {
                    background-color: white
                }
                div[data-testid="stExpander"] > details > summary:hover
                {
                    color: black;
                }
                div[data-testid="stExpander"] > details > summary:hover svg
                {
                    fill: black;
                }
                .st-emotion-cache-s1k4sy > div
                {
                    max-height: 70px;
                }
                details > summary:hover svg
                {
                    transform: rotate(180deg);
                    fill: white !important;
                }
                details > summary > svg
                {
                    transform: rotate(180deg);
                    color: white !important;
                }
                .stAlert
                {
                    display: none;
                }
                .stSpinner > div > i
                {
                    margin-left: 160px
                }
                .st-emotion-cache-6awftf
                {
                    display: block;
                    right: 0rem;
                    position: absolute;
                }
                #ai-security-analyst-chatbot
                {
                    color: white;
                    margin-bottom: 0px;
                }
            </style>
            """,
        unsafe_allow_html=True,
    )

    with st.expander("###### Asset Compliance AI Chatbot", expanded=False):
        chat_container(chat_type="licenses")


def load_dashboard_page():
    st.set_page_config(layout="wide")
    st.text("")
    st.text("")
    app_navbar.load_navbar(1)
    if "chatbot_context" not in st.session_state:
        st.session_state.chatbot_context = load_chatbot_context()

    with st.spinner("Wait for it..."):
        asset_data = get_asset_data()
        if len(asset_data) == 0:
            refresh_status = Thread(target=scanner.refresh_status)
            refresh_status.start()
            st.session_state.chatbot_context = load_chatbot_context()

    if "show_details" not in st.session_state:
        st.session_state.show_details = False

    if "app_name" not in st.session_state:
        st.session_state.app_name = ""

    st.markdown(
        """<link href='https://fonts.googleapis.com/css?family=Montserrat' rel='stylesheet'>
        <p style="font-weight: bold; font-family: Montserrat; font-size: 25px; padding-top: 30px">Licenses Overview</p>""",
        unsafe_allow_html=True,
    )

    create_license_view(asset_data)

    if st.session_state.show_details:
        st.markdown(
            f"""
            <p style="font-weight: bold; font-family: Montserrat; font-size: 25px; padding-top: 30px">Asset List - {st.session_state.app_name}</p>""",
            unsafe_allow_html=True,
        )

        load_asset_details(st.session_state.app_name, asset_data)
    # Load chatbot container
    load_chatbot()


load_dashboard_page()
