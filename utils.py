import json
from datetime import datetime, timezone
from json import JSONDecodeError

import streamlit as st
import streamlit.components.v1 as components

from constant import *
from logger import AppLogger


def get_logger():
    """
    This function returns the logger.
    Logger act as a singleton class
    """
    return AppLogger.get_instance()


logger = get_logger()


def change_button_colour(
    widget_label, font_color, border_color, background_color="transparent"
):
    htmlstr = f"""
        <script>
            var elements = window.parent.document.querySelectorAll('button');
            for (var i = 0; i < elements.length; ++i) {{
                if (elements[i].innerText == '{widget_label}') {{
                    elements[i].style.color ='{font_color}';
                    elements[i].style.background = '{background_color}';
                    elements[i].style.border = '{border_color}';
                }}
            }}
        </script>
        """
    components.html(f"{htmlstr}", height=0, width=0)


def padding_markdown():
    return st.markdown(
        """
            <style>
                .st-emotion-cache-12w0qpk
                {
                    margin-top: 0px;
                }
            </style>
        """,
        unsafe_allow_html=True,
    )


def is_expired(expires_at):
    """Compares the given time with present time

    Args:
        expires_at (datetime): Time to check if expired.
    """
    # Recreate in case there's no expires_at present
    if expires_at is None:
        return True
    return datetime.now(timezone.utc) >= expires_at


def load_checkpoints():
    try:
        with open(CHECKPOINT_PATH, "r") as f:
            checkpoint_data = json.load(f)
    except Exception as e:
        logger.error(
            f"An error occurred while fetching checkpointing details: {e}. Initializing the checkpoint store."
        )
        now = datetime.now()
        time_string = now.strftime("%Y-%m-%d %H:%M:%S")
        checkpoint_data = {VALID_CACHE_HOURS: 24, LAST_SCAN_TIME: time_string}
    return checkpoint_data


def save_checkpoints(checkpoint_data):
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(checkpoint_data, f)
    logger.info("Successfully saved checkpoints details.")


def update_asset_data(assets_data, storage_file=ASSET_DATA_PATH):
    try:
        with open(storage_file, "w", encoding="utf-8") as f:
            json.dump(assets_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(e)
    logger.info("Successfully saved assets data.")


def get_asset_data(storage_file_path=ASSET_DATA_PATH):
    asset_data = []
    try:
        with open(storage_file_path, "r") as f:
            asset_data = json.load(f)
    except JSONDecodeError:
        logger.error("Error: asset_data.json file is not valid JSON.")
    except Exception as e:
        logger.error(f"Unknown error ocurred while reading the asset data. Error: {e}")
    return asset_data


def load_chatbot_context():
    context = ""
    try:
        with open(ASSETS_TEXT, "r") as f:
            context = f.read()
    except Exception as ex:
        logger.error(f"Error occurred while loading the assets context text file. {ex}")

    return context
