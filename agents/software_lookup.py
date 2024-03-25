import os

import html2text
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.output_parser import software_version_information
from core.tools import get_software_information
from logger import AppLogger

load_dotenv()
logger = AppLogger.get_instance()
gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.0-pro-latest")

APP_TO_URL_MAP = {
    "Visual Studio Code": {"url": "https://code.visualstudio.com/updates"},
    "Zoom Client": {"url": "https://zoom.us/rest/download?os=win"},
    "Adobe Acrobat (64-bit)": {
        "url": "https://www.adobe.com/devnet-docs/acrobatetk/tools/ReleaseNotesDC/"
    },
    "Chrome": {
        "url": "https://chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Windows&num=2"
    },
    "Firefox": {"url": "https://www.mozilla.org/en-US/firefox/releases/"},
    "LibreOffice": {"url": "https://www.libreoffice.org/download/release-notes/"},
    "Docker Desktop": {
        "url": "https://docs.docker.com/desktop/release-notes/",
        "skip_tags": ["ul"],
    },
    "Postman": {"url": "https://www.postman.com/mkapi/release-v10.json"},
    "VMware Workstation": {
        "url": "https://customerconnect.vmware.com/channel/public/api/v1.0/products/getRelatedDLGList?locale=en_US&category=desktop_end_user_computing&product=vmware_workstation_pro&version=17_0&dlgType=PRODUCT_BINARY"
    },
    "Notepad++": {"url": "https://notepad-plus-plus.org/news/"},
    "Windows 11": {
        "url": "https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information"
    },
}


def is_installed_version_lower(cached_version, application_version):
    llm = ChatGoogleGenerativeAI(temperature=0, model=gemini_model)
    prompt = """Provided software versions of an application, identify if the installed version is lower than the latest available version.
               latest available version is `{cached_version}` and the installed version is `{application_version}`.
               return answer in yes or no"""
    # version number: major, minor, patch
    response = llm.invoke(
        prompt.format(
            cached_version=cached_version, application_version=application_version
        )
    )
    logger.debug(f"Received response for version comparison {response}")
    return True if response.content.lower() == "yes" else False


def software_lookup(software_name: str) -> str:
    """Method to get the latest software version available on the internet.

    Args:
        software_name (str): Name of the software

    Returns:
        str: Version of the software
    """
    template_1 = """
    given the name: {software_name} of the software,
    Use its product website to find endpoints like downloads, release notes, robots.txt etc. along with the other resources you find
    relevant use these endpoints also to search for the latest stable release version of that product.Search for windows version of the software.
    Before using any source as base of information, you should check if the information is out-dated or not.
    Return the product version."""

    react_prompt = hub.pull("hwchase17/react")
    tools_for_agent = [
        Tool(
            name="Crawl Google for information about the software and its version.",
            func=get_software_information,
            description="Useful for when you need to search for any software and its version.",
        )
    ]

    llm = ChatGoogleGenerativeAI(temperature=0, model=gemini_model)
    agent = create_react_agent(llm=llm, tools=tools_for_agent, prompt=react_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools_for_agent, verbose=True)

    prompt_template = PromptTemplate(
        template=template_1, input_variables=["software_name"]
    )

    logger.info(f"Invoking agent to get the latest version of {software_name}")
    try:
        result = agent_executor.invoke(
            input={"input": prompt_template.format_prompt(software_name=software_name)}
        )
        return result.get("output")
    except Exception as ex:
        logger.error(
            f"Error occurred while processing query in software_lookup tool. {ex}"
        )
        return "Sorry, I encountered an issue while processing your query."


def extract_html_from_url(url, skipp_tags):
    retry = 3
    while retry > 0:
        try:
            # Fetch HTML content from the URL using requests
            response = requests.get(url, headers={"accept": "application/json"})
            response.raise_for_status()  # Raise an exception for bad responses (4xx and 5xx)

            # Parse HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")
            excluded_tagNames = ["footer", "nav", "blockquote"]
            # Exclude elements with class names 'footer' and 'navbar'
            excluded_tagNames.extend(
                skipp_tags
            )  # Default to an empty list if not provided
            for tag_name in excluded_tagNames:
                for unwanted_tag in soup.find_all(tag_name):
                    unwanted_tag.extract()

            # Convert HTML to plain text using html2text
            text_content = html2text.html2text(str(soup))
            return text_content
        except (requests.exceptions.RequestException, Exception) as e:
            logger.error(f"Error fetching data from {url}: {e}")
            if retry <= 0:
                return f"Error fetching data from {url}: {e}"
            retry -= 1


def extract_latest_version(name):
    try:
        skip_tags = []
        url = ""
        for keys in APP_TO_URL_MAP.keys():
            if keys.lower() in name.lower():
                url = APP_TO_URL_MAP[keys].get("url")
                skip_tags = APP_TO_URL_MAP[keys].get("skip_tags")

        logger.debug(
            f"Selected: {name} || {skip_tags} || {url} for getting application version."
        )
        summary_template = """given the name {name} and information {information} of a software's release notes page in html format, I want you to extract information about the latest stable update released by the version of that software for desktop/windows. You are not allowed to make any assumptions while extracting the information. Every link you provide should be from the information given. There should be no assumptions for Links/URLS. You should not return code to do it.:
            You should identify the  Latest Release or largest version form the provided context.
            You should extract the following text information from the html:
            1. Return only the version of the software.
        """

        llm_model = ChatGoogleGenerativeAI(temperature=0, model=gemini_model)

        prompt = PromptTemplate(
            template=summary_template,
            input_variables=["information", "name"],
            partial_variables={
                "format_instructions": software_version_information.get_format_instructions()
            },
        )
        llm_chain = LLMChain(llm=llm_model, prompt=prompt)
        excluded_tags = skip_tags or []
        software_information_data = extract_html_from_url(url, excluded_tags)
        user_data = llm_chain.invoke(
            input={"information": software_information_data, "name": name},
            return_only_outputs=True,
        )
    except Exception as e:
        logger.error(f"encountered error: {e}")
        return ""
    logger.info(
        f"The latest version for the application {name} is {user_data.get('text')}"
    )
    return user_data.get("text")
