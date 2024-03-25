import json
import os

import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import StructuredTool
from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
from langchain_community.utilities.jira import JiraAPIWrapper
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables and configure logging
from agents.software_lookup import (
    APP_TO_URL_MAP,
    extract_latest_version,
)
from agents.windows_updates_lookup import get_win_build_info
from constant import *
from utils import get_logger

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSETS_FILE_PATH = "Data/asset_data.json"
CREATE_ISSUE = "Create Issue"
logging = get_logger()


class ChatApplication:
    """Class for Chat application."""

    def __init__(self):
        """
        Constructor for initializing the ChatApplication.
        """
        logging.info("Initializing ChatApplication...")
        self.surf_tool = Tool(
            name="Crawl Google for information about the software other than Windows and its version.",
            func=extract_latest_version,
            description="""This tool is used for fetching the latest version of 'application' only and not for os or windows version.
                            IMPORTANT: If you want to find the latest version of any application and not Windows you must use this tool.""",
        )
        self.windows_tool = Tool(
            name="Crawl information about only windows os and its version.",
            func=get_win_build_info,
            description="""This tool is used for fetching the latest version of 'windows' only and not for applications version.
                        IMPORTANT: If you want to find the latest version of windows os you must use this tool.""",
        )
        self.jira_tool = Tool(
            name="Jira tool for performing the jira atlassian operations.",
            func=self.handle_jira_query,
            description="This tool is used for creating a jira issue only if asked to create a jira issue.",
        )
        self.tools = [
            self.contextual_answer_tool(),
            self.windows_tool,
            self.surf_tool,
            self.jira_tool,
        ]
        self.gen_model = genai.GenerativeModel("gemini-pro")
        self.prompt = hub.pull("hwchase17/react-chat")
        # Using gpt-4 for testing
        # self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.memory = ConversationBufferWindowMemory(memory_key="chat_history", k=0)

        self.llm = ChatGoogleGenerativeAI(model="gemini-pro")
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True,
        )
        logging.info("ChatApplication initialized successfully.")

    def handle_jira_query(self, user_input):
        """Handle a jira operation and return the task.

        Args:
            user_input: The user input for the jira query.

        Returns:
            The Task id from jira.
        """
        try:
            example_payload = """
                "fields": {
                    "project": {"key": "PROJECT_KEY"},
                    "summary": "SUMMARY",
                    "description": "DESCRIPTION",
                    "issuetype": {"name": "Task"}
                }
            """
            input_query = {
                "input": f"{user_input}. Make sure your input is having the same schema as this example payload {example_payload}"
            }
            jira = JiraAPIWrapper()
            toolkit = JiraToolkit.from_jira_api_wrapper(jira)
            self.jira_tools = toolkit.get_tools()
            create_jira_tool = []
            for tool in self.jira_tools:
                if tool.name == CREATE_ISSUE:
                    create_jira_tool.append(tool)
                    break
            self.jira_prompt = hub.pull("hwchase17/react")
            self.jira_agent = create_react_agent(
                self.llm, create_jira_tool, self.jira_prompt
            )
            self.jira_agent_executor = AgentExecutor(
                agent=self.jira_agent,
                tools=self.jira_tools,
                verbose=True,
                handle_parsing_errors=True,
            )
            response = self.jira_agent_executor.invoke(input_query)
            return response.get("output")
        except Exception as ex:
            logging.error(f"Error occurred while processing query in jira tool. {ex}")
            return "Sorry, I encountered an issue while processing your query."

    def contextual_answer_tool(self):
        """
        This tool is useful to question and answer based context provided about the asset/device and applications.
        """

        def get_answer(input_query: str):
            try:
                # GET THE CONTEXT FROM SESSION STATE
                context = st.session_state.get("chatbot_context", "")
                prompt = f"""You need to answer the question using the provided context.
                        Context: {context}
                        Input: {input_query}"""

                response = self.gen_model.generate_content(prompt)
                return response.text
            except Exception as ex:
                logging.error(
                    f"Error occurred while processing query in json tool. {ex}"
                )
                return "Sorry, I encountered an issue while processing your query."

        answer = StructuredTool.from_function(
            func=get_answer,
            name="Get asset and application data.",
            description="This tool is useful to question and answer based context provided about the asset/device and applications",
        )

        return answer

    def handle_query(self, user_query):
        prompt = {"input": f"{user_query}"}
        try:
            response = self.agent_executor.invoke(prompt)
            url = None
            for keys in APP_TO_URL_MAP.keys():
                if keys.lower() in user_query.lower():
                    url = APP_TO_URL_MAP[keys].get("url")

            if isinstance(response, str):
                if url is not None:
                    return f"{response}\n[Source]({url})"
                return response
            else:
                if url is not None:
                    return f"{response.get('output')}\n[Source]({url})"
                return response.get("output")
        except Exception as ex:
            logging.error(f"Error occurred while processing query in json tool. {ex}")
            return "Sorry, I encountered an issue while processing your query."


def chat_container(chat_type: str = "dashboard"):
    # st.markdown("#### AI Security Analyst Chatbot")
    data = None
    try:
        with open(CHAT_DATA, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        # Handle the error
        logging.info("chat_data file does not exist.")
    st.caption("🚀 Chatbot Powered by Gemini")
    if chat_type not in st.session_state:
        if not data:
            st.session_state[chat_type] = [
                {"role": "assistant", "content": "How can I help you?"}
            ]
        else:
            st.session_state[chat_type] = data

    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state[chat_type]:
            content = msg["content"]
            st.chat_message(msg["role"]).write(content)
    if (
        "chat_service" not in st.session_state
        or chat_type not in st.session_state.chat_service
    ):
        st.session_state["chat_service"] = {}
        st.session_state["chat_service"][chat_type] = ChatApplication()

    client = st.session_state["chat_service"][chat_type]

    if prompt := st.chat_input(placeholder="Start Typing..."):
        with chat_container:
            st.session_state[chat_type].append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            with st.spinner(text=""):
                msg = client.handle_query(prompt)
                st.chat_message("assistant").write(msg)
                st.session_state[chat_type].append(
                    {"role": "assistant", "content": msg}
                )
        # Store the chatdata in json
        with open(CHAT_DATA, "w") as file:
            json.dump(st.session_state[chat_type], file, indent=4)
