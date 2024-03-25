import os
import re

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI

from core.tools import get_software_information
from logger import AppLogger

load_dotenv()
logger = AppLogger.get_instance()
gemini_model = os.getenv("GEMINI_MODEL", "gemini-pro")


def windows_upgrade_lookup(windows_version: str) -> str:
    """Method to get the latest windows updates available on the internet.

    Args:
        windows_version (str): Windows version

    Returns:
        str: OS build number of the latest windows update.
    """
    template_1 = """
Task:
Retrieve the latest {windows_version} full version number in the format Major.Minor.Build.Rev. Utilize Google Search APIs and employ reliable information extraction techniques to ensure accuracy.
Instructions:
1. Identifying the Major version:
Search query: Focus on keywords like "Windows 11 Pro", "latest version", and "major version".
Information extraction: Look for explicit mentions of the major version number, often presented prominently in headings or introductory text.
Example: If the retrieved information states "Windows 11 Pro version 22H2", we identify the Major version as 22H2.
2. Identifying the Build number:
Search query: Further refine the search using the identified Major and Minor versions, adding keywords like "build number".
Information extraction: Look for specific mentions of the build number, often listed alongside the version name.
Example: the Build number is identified as 22621.
3. Identifying the Revision number:
Search query: Use the identified Major, Minor, and Build numbers to refine the search, adding keywords like "revision number".
Information extraction: Look for detailed release notes or technical specifications where the revision number might be mentioned.
Example: Following the previous example, the revision number consists of numbers of any length.
Note: The Revision number might not always be readily available or explicitly mentioned. If unavailable, you can report the Build number.
"""
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
        template=template_1, input_variables=["windows_version"]
    )

    logger.info(
        f"Invoking agent to get the latest windows updates for {windows_version}"
    )
    try:
        result = agent_executor.invoke(
            input={
                "input": prompt_template.format_prompt(windows_version=windows_version)
            }
        )
        logger.info(f"Result returned for windows update search {result=}")
        return result.get("output")
    except Exception as ex:
        raise ex
        logger.error(
            f"Error occurred while processing query in windows_upgrade_lookup tool. {ex}"
        )
        return "Sorry, I encountered an issue while processing your query."


def get_win_build_info(
    os_version,
    url="https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information",
):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    # Scrape the release names
    release_names = []
    for version in soup.find_all("strong"):
        if (
            "Version" in version.contents[0]
            and version.contents[0] not in release_names
        ):
            release_names.append(version.contents[0])
    # Scrape the release data and match them with their corresponding release names
    i = 0
    release_list = []
    tables = soup.find_all("table", class_="cells-centered")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            row_dict = {
                "os_major_version": os_version,
                "feature_release_version": release_names[i].split(" ")[1],
                "release_full_name": release_names[i],
            }
            if row_dict["feature_release_version"] != "23H2":
                continue
            cols = row.find_all("td")

            for data in cols:
                if re.match("\d+-\d+-\d+", data.text):
                    row_dict["release_date"] = data.text
                elif re.match("\d+\.\d+", data.text):
                    row_dict["build_number"] = data.text
                elif re.match("KB\d+", data.text):
                    row_dict["kb"] = data.text
            if "release_date" in row_dict:
                release_list.append(row_dict)
        i = i + 1

    return "10.0." + release_list[0].get("build_number")
