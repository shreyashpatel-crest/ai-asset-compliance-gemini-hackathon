import json
import os
from faker import Faker
import requests
from dotenv import load_dotenv

from constant import *
from utils import get_logger, update_asset_data

load_dotenv()
fake = Faker()
logging = get_logger()


class CrowdStrikeData:
    def __init__(self):
        """
        Constructor for the CrowdStrikeData class. Initializes
        """
        logging.info("Initializing CrowdStrikeData...")
        self.setup_client()
        self.generate_acces_token()
        self.header = {"Authorization": f"Bearer {self.access_token}"}

    def setup_client(self):
        self.client_id = os.environ.get("CLIENT_ID")
        self.client_secret = os.environ.get("CLIENT_SECRET")

    def generate_acces_token(self):
        payload = {"client_id": self.client_id, "client_secret": self.client_secret}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_url = CROWDSTRIKE_BASE_URL + "oauth2/token"
        response = requests.request("POST", token_url, headers=headers, data=payload)

        if response.status_code == 201:
            data = response.json()
            self.access_token = data.get("access_token")
        else:
            logging.error(
                f"Error: Failed to obtain access token. Status code: {response.status_code}"
            )
            self.access_token = None

    def get_asset_ids(self):
        asset_id_url = CROWDSTRIKE_BASE_URL + "/devices/queries/devices-scroll/v1"

        response = requests.get(asset_id_url, headers=self.header)

        if response.status_code == 200:
            data = response.json()
            return data["resources"]
        else:
            logging.error(
                f"Error: Asset API request failed with status code {response.status_code}"
            )
            return []

    def format_filter(self, ids):
        filter_string = ""
        for id in ids:
            filter_string += f"ids={id}&"
        filter_string = filter_string[:-1]

        return filter_string

    def asset_data(self, asset_ids):
        filter_string = self.format_filter(asset_ids)
        asst_data_url = (
            CROWDSTRIKE_BASE_URL + f"/devices/entities/devices/v2?{filter_string}"
        )

        response = requests.get(asst_data_url, headers=self.header)
        if response.status_code == 200:
            return response.json()["resources"]
        else:
            logging.error(
                f"Error: Asset details API request failed with status code {response.status_code} {response.text}"
            )
            return []

    def get_app_id(self, hostname):
        app_ids = []
        for app in APP_LIST:
            app_id_url = (
                CROWDSTRIKE_BASE_URL
                + f"discover/queries/applications/v1?sort=version&filter=host.hostname%3A%20'{hostname}'%20%2B%20%20name%3A%20'{app}'"
            )
            response = requests.get(app_id_url, headers=self.header)
            if response.status_code == 200:
                data = response.json()["resources"]
                if len(data) > 0:
                    app_ids.append(response.json()["resources"][-1])
            else:
                logging.error(
                    f"Error: Application id API request failed with status code {response.status_code} {response.text}"
                )

        return app_ids

    def fetch_app_data(self, hostname):
        app_id = self.get_app_id(hostname)
        filter_string = self.format_filter(app_id)
        app_data_url = (
            CROWDSTRIKE_BASE_URL + f"discover/entities/applications/v1?{filter_string}"
        )

        response = requests.get(app_data_url, headers=self.header)
        if response.status_code == 200:
            return response.json()["resources"]
        else:
            logging.error(
                f"Error: Application details API request failed with status code {response.status_code} {response.text}"
            )
            return []

    def get_application_data(self, asset_data):
        hostname = asset_data.get("hostname")
        app_data = self.fetch_app_data(hostname)

        formatted_app_data = []

        for data in app_data:
            temp_dict = {
                "name": data.get("name", ""),
                "vendor": data.get("vendor", ""),
                "version": data.get("version", ""),
                "last_used_timestamp": data.get("last_used_timestamp", ""),
                "last_updated_timestamp": data.get("last_updated_timestamp", ""),
            }

            formatted_app_data.append(temp_dict)

        return formatted_app_data

    def load_asset_data(self, storage_file):
        # asset_ids = self.get_asset_ids()
        logging.info("Fetching data from crowdstrike")
        asset_ids = [
            "13d37f5ff2644e518158ae94a6bf596c",
            "c2b24f9b749b4093a0f40cadd9bb5184",
            "71c0be3368a64791a4220109d8c28562",
            "542fee4934f141e0b383e5f04736ef72",
            "65ba14c5c4174017ad6e6d5caddedcfb",
            "2ce412d17b334ad4adc8c1c54dbfec4b",
            "d8da12e0ac8743a4bc70eb157306c824",
            "e9e3f706b8ea4857b72961732d415d4c",
            "8e0f80f0ab774c738830b24ff85089f7",
            "263933b66c3c4ae7a2caf6e25cf16445",
            "f747f0b145cf49c481f550d3adb3a9d3",
            "db559601ded1488887d2e1641503dfaa",
            "263a612b28dd4fb8a8da79fa44b9343d",
            "35f241e421334a90a05e97e10aaa78fa",
            "f0e4e6231a8a4283934416548d2f1714",
            "d1cdaeaf53734ad4909b64fb0a219723",
            "d7347d798bca462794a4777cfe617e2b",
        ]
        asset_data = self.asset_data(asset_ids)

        formatted_asset_data = []

        for data in asset_data:
            temp_dict = {
                "device_id": fake.uuid4(),
                "cid": fake.uuid4(),
                "hostname": data.get("hostname", ""),
                "last_login_user": f"{fake.first_name()}.{fake.last_name()}",
                "os_version": data.get("os_version", ""),
                "kernel_version": data.get("kernel_version", ""),
                "agent_local_time": data.get("agent_local_time", ""),
                "agent_version": data.get("agent_version", ""),
                "external_ip": fake.ipv4(),
                "mac_address": fake.mac_address(),
                "first_seen": data.get("first_seen", ""),
                "last_seen": data.get("last_seen", ""),
                "local_ip": fake.ipv4(),
                "major_version": data.get("major_version", ""),
            }

            formatted_asset_data.append(temp_dict)

        for index in range(len(formatted_asset_data)):
            application_data = self.get_application_data(formatted_asset_data[index])
            formatted_asset_data[index]["application_installed"] = application_data

        update_asset_data(assets_data=formatted_asset_data, storage_file=storage_file)
