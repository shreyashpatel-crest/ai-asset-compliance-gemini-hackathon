from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from agents.software_lookup import (
    APP_TO_URL_MAP,
    extract_latest_version,
    is_installed_version_lower,
)
from agents.windows_updates_lookup import get_win_build_info
from constant import *
from core.crowdstike_data import CrowdStrikeData
from core.utils.generate_text import generate_text_file
from logger import AppLogger
from utils import (
    get_asset_data,
    is_expired,
    load_checkpoints,
    save_checkpoints,
    update_asset_data,
)

logger = AppLogger.get_instance()
load_dotenv()

versions_cache = {}


def set_sync_interval(hours):
    checkpoints_details = load_checkpoints()
    checkpoints_details[VALID_CACHE_HOURS] = hours
    save_checkpoints(checkpoint_data=checkpoints_details)
    logger.info("Updated the sync interval successfully.")


def update_software_information(app_name, version, cache_hours: int = 24):
    logger.info(f"Updating the cache for {app_name=} with {version=} ")
    if versions_cache.get(app_name) is None:
        versions_cache[app_name] = {}

    versions_cache[app_name]["last_updated"] = datetime.now(timezone.utc) + timedelta(
        hours=int(cache_hours)
    )
    versions_cache[app_name]["version"] = version


def validate_asset_application_compliance(asset: dict, cache_hours: int):
    is_asset_compliant = True
    for application in asset.get("application_installed"):
        app_name = application.get("name")
        if versions_cache.get(app_name) is None or (
            versions_cache.get(app_name)
            and is_expired(versions_cache[app_name].get("last_updated"))
        ):
            # trigger the agents to get the latest version of the software.
            logger.info("searching latest software version of " + app_name)
            version = extract_latest_version(name=app_name)

            # update the cache with latest version of the app
            update_software_information(app_name, version, cache_hours)

        version = versions_cache[app_name]["version"]

        # compare the app_version from json with the cache.
        logger.info(
            f"Comparing the versions of |application name:{app_name}|cached version:{version}|installed version:{application.get('version')}"
        )
        if is_installed_version_lower(
            cached_version=version, application_version=application.get("version")
        ):
            logger.info(f"{app_name} Needs updates.")
            is_asset_compliant = False
            application["is_compliant"] = False
        else:
            logger.info(f"{app_name} is upto date.")
            application["is_compliant"] = True

    asset["asset_compliant"] = is_asset_compliant


def validate_windows_upgrade_compliance(asset, cache_hours):
    default_os = "Windows 11"
    install_os = asset.get("os_version", default_os)

    if versions_cache.get(install_os) is None or (
        versions_cache.get(install_os)
        and is_expired(versions_cache[install_os].get("last_updated"))
    ):
        logger.info("searching for latest windows updates" + install_os)
        version = get_win_build_info(
            os_version=install_os, url=APP_TO_URL_MAP.get(install_os, default_os)["url"]
        )

        update_software_information(install_os, version, cache_hours)

    version = versions_cache[install_os]["version"]
    if is_installed_version_lower(
        cached_version=version, application_version=asset.get("kernel_version")
    ):
        asset["windows_compliant"] = False
    else:
        asset["windows_compliant"] = True


def refresh_status():
    # Trigger method to re-populate the asset and application information.
    checkpoints_details = load_checkpoints()
    if checkpoints_details.get("scan_in_progress", False):
        logger.info("Skipping the sync, as scanning is already in progress.")
        return
    logger.info("Setting syncing status as true.")
    checkpoints_details["scan_in_progress"] = True
    save_checkpoints(checkpoint_data=checkpoints_details)

    data_object = CrowdStrikeData()
    data_object.load_asset_data(storage_file=ANALYZED_DATA_PATH)

    assets_data = get_asset_data(storage_file_path=ANALYZED_DATA_PATH)

    for asset in assets_data:
        logger.info(f"validating application of {asset.get('last_login_user')}")
        validate_asset_application_compliance(
            asset=asset, cache_hours=checkpoints_details["valid_cache_hours"]
        )
        validate_windows_upgrade_compliance(
            asset=asset, cache_hours=checkpoints_details["valid_cache_hours"]
        )

    final_asset_data = {item.get("hostname"): item for item in assets_data}

    update_asset_data(assets_data=final_asset_data)
    logger.info("Setting syncing status as false.")
    now = datetime.now()
    time_string = now.strftime("%Y-%m-%d %H:%M:%S")
    checkpoints_details[LAST_SCAN_TIME] = time_string
    checkpoints_details["scan_in_progress"] = False
    save_checkpoints(checkpoint_data=checkpoints_details)

    logger.info(f"The versions cache is: {versions_cache=}")
