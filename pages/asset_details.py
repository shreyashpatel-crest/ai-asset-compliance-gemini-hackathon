import json

import streamlit as st
import streamlit_antd_components as sac

import app_navbar
from constant import *
from core.chatbot.chat import chat_container
from utils import change_button_colour, get_logger, load_checkpoints, padding_markdown

logging = get_logger()


def load_asset_title(asset_data):
    cols = st.columns([0.1, 9.9])
    with cols[0]:
        padding_markdown()
        st.image(f"icons/asset.svg", width=24)
    with cols[1]:
        status = ""
        if asset_data.get("windows_compliant", False) and asset_data.get(
            "asset_compliant", False
        ):
            status = "Compliant"
            st.markdown(
                f"""
                <table>
                    <tr style="border-style: none">
                        <th style="border-style: none;">
                            <p style="font-family: Montserrat; font-size: 25px; margin-top: 3px">{asset_data.get("hostname", "-")}</p>
                        </th>
                        <th style="border-style: none;">
                            <div style="background-color: #DFF4EA; border: none; border-radius: 20px; width: 85px; height: 22px; text-align: center; margin-top: 0px; margin-bottom: 12px">
                                <p style="font-size: 14px; color: #2BB472">{status}</p>
                            </div>
                        </th>
                    </tr style="border-style: none">
                </table>
            """,
                unsafe_allow_html=True,
            )
        else:
            status = "Non-compliant"
            st.markdown(
                f"""
                <table>
                    <tr style="border-style: none">
                        <th style="border-style: none; margin-top: 0px">
                            <p style="font-family: Montserrat; font-size: 25px; margin-top: 3px">{asset_data.get("hostname", "-")}</p>
                        </th>
                        <th style="border-style: none;">
                            <div style="background-color: #FFDDDB; border: none; border-radius: 20px; width: 110px; height: 22px; text-align: center; margin-top: 0px; margin-bottom: 12px">
                                <p style="font-size: 14px; color: #FF4238">{status}</p>
                            </div>
                        </th>
                    </tr style="border-style: none">
                </table>
            """,
                unsafe_allow_html=True,
            )


def prepare_asset_data(asset_data):
    details = []
    part1 = {
        "device_id": asset_data.get("device_id", "-"),
        "cid": asset_data.get("cid", "-"),
        "agent_local_time": asset_data.get("agent_local_time", "-"),
        "agent_version": asset_data.get("agent_version", "-"),
        "external_ip": asset_data.get("external_ip", "-"),
        "mac_address": asset_data.get("mac_address", "-"),
    }
    details.append(part1)

    part2 = {
        "first_seen": asset_data.get("first_seen", "-"),
        "last_login_user": asset_data.get("last_login_user", "-"),
        "last_seen": asset_data.get("last_seen", "-"),
        "local_ip": asset_data.get("local_ip", "-"),
        "kernel_version": asset_data.get("kernel_version", "-"),
        "major_version": asset_data.get("major_version", "-"),
    }
    details.append(part2)

    return details


def asset_details_tab(asset_data):
    prepared_data = prepare_asset_data(asset_data)
    cols = st.columns(2)
    for index in range(len(prepared_data)):
        with cols[index]:
            for key in prepared_data[index]:
                in_cols = st.columns([1, 2])
                with in_cols[0]:
                    st.markdown(
                        f"""
                        <p style="font-family: Montserrat; font-size: 17px; font-weight: bold">{key} :</p>
                    """,
                        unsafe_allow_html=True,
                    )
                with in_cols[1]:
                    st.markdown(
                        f"""
                        <p style="font-family: Montserrat; font-size: 15px; font-weight: medium">{prepared_data[index][key]}</p>
                    """,
                        unsafe_allow_html=True,
                    )


def installed_app_tab(application_data):
    cols = st.columns(2)
    change_column = True
    index = 0
    for app_data in application_data:
        if change_column:
            index = 0
        else:
            index = 1

        change_column = not change_column

        with cols[index]:
            in_cols = st.columns([0.2, 1, 0.8, 1])
            with in_cols[0]:
                padding_markdown()
                st.image(f"icons/{app_data.get('name')}.svg", width=20)
            with in_cols[1]:
                st.markdown(
                    f"""
                    <p style="font-family: Montserrat; font-size: 15px; margin-top: 15px">{app_data.get("name", "-")}</p>
                """,
                    unsafe_allow_html=True,
                )
            with in_cols[2]:
                st.markdown(
                    f"""
                    <p style="font-family: Montserrat; font-size: 15px; margin-top: 15px">{app_data.get("version", "-").replace(",", ".")}</p>
                """,
                    unsafe_allow_html=True,
                )
            with in_cols[3]:
                status = ""
                if app_data.get("is_compliant", False):
                    status = "Compliant"
                    st.markdown(
                        f"""
                        <div style="background-color: #DFF4EA; border: none; border-radius: 20px; width: 85px; height: 22px; text-align: center; margin-top: 15px;">
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


def load_asset_details(asset_data):
    container = st.container(height=500)
    with container:
        investigation_tabs = sac.tabs(
            [
                sac.TabsItem(label="Asset Details"),
                sac.TabsItem(label="Installed Applications"),
            ],
            align="lest",
            color="#466CF3",
            size="l",
        )

        match investigation_tabs:
            case "Asset Details":
                with st.container(height=450):
                    asset_details_tab(asset_data)
            case "Installed Applications":
                with st.container(height=450):
                    installed_app_tab(asset_data.get("application_installed", []))


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
        chat_container()


def asset_details():
    st.set_page_config(layout="wide")
    st.text("")
    st.text("")
    app_navbar.load_navbar(2)

    do_load_asset_details_page = False

    try:
        asset_data = st.session_state["data"]
        do_load_asset_details_page = True
    except Exception as e:
        logging.error(f"Got exception while loading asset details. Ex {str(e)}")

    cols = st.columns(2)
    with cols[0]:
        back_button = st.button("Back To Dashboard")
        change_button_colour(
            "Back To Dashboard", "#0068A2", "2px solid #0068A2", "#FFFFFF"
        )
        if back_button:
            st.switch_page("pages/dashboard.py")
    with cols[1]:
        scan_time = load_checkpoints()
        st.markdown(
            f"""<link href='https://fonts.googleapis.com/css?family=Montserrat' rel='stylesheet'>
                <p style="font-color: #C6CAC7; font-family: Montserrat; font-size: 10px; margin-bottom: 0px; text-align: right">Last Scanned</p>
                <p style="font-weight: bold; font-family: Montserrat; font-size: 14px; margin-top: 0px; text-align: right">{scan_time[LAST_SCAN_TIME]}</p>""",
            unsafe_allow_html=True,
        )

    if do_load_asset_details_page:
        load_asset_title(asset_data)
        load_asset_details(asset_data)
        load_chatbot()


asset_details()
