import json
from google import generativeai as genai
from pathlib import Path
from constant import ASSET_DATA_PATH, ASSETS_TEXT
import os
from utils import get_logger

logger = get_logger()
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=GOOGLE_API_KEY)


def generate_text_file():
    """To generate a text file from json use this function."""
    assets_data = json.loads(Path(ASSET_DATA_PATH).read_text())
    llm_prompt_template = f"""
        Instructions:
            * Below is the definition of all the json keys. Refer these fields and definition to understand the data.
                - 'last_login_user' : "The user who used the asset/device."
                - 'kernel_version' : "The kernel version of windows system for that asset/device."
                - 'windows_compliant' : "The compliance status for the windows version for that particular asset/device."
                - 'application_installed' : '''List of installed applications on that asset/device. All the applications have some key value pairs (json data) You should iterate over all the installed application to get the detailed information about that installed application. The definition for the key present under the applications are as below..
                        "name": "The name of installed application"
                        "version": "The version of that installed application"
                        "is_compliant": "The compliance status of that installed application for particular asset/device."
            * IMPORTANT: Don't use the markdown or any formatting just write a paragraph.
        Your task is to write a detailed paragraph for each asset data present in the input json data.
        Be accurate for these keys "asset_compliant", "windows_compliant", "last_login_user", "kernel_version", "application_installed", "is_compliant"
        for each assets/device and write in that paragraph about each device in detail for only these keys.

        Input: {assets_data}
        """
    try:
        model = "gemini-pro"
        logger.info("Generating the text file from the json data.")
        llm = genai.GenerativeModel(model)
        response = llm.generate_content(llm_prompt_template)
        with open(ASSETS_TEXT, "w") as f:
            f.write(response.text)
        logger.info("Successfully generated the text file from the json data.")
        return True
    except Exception as ex:
        logger.error(f"Error occurred while generating the text asset data. {ex}")
        return False
