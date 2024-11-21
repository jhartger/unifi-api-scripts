import os
import time
import logging
import requests
import urllib3
from dotenv import load_dotenv
from mail_notification import mail_notification

# Load environment variables from .env_example file in the same directory
load_dotenv()

# Setup logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# UniFi controller details
controller_ip = os.getenv("CONTROLLER_IP")
controller_port = os.getenv("CONTROLLER_PORT")
controller_username = os.getenv("CONTROLLER_USERNAME")
controller_password = os.getenv("CONTROLLER_PASSWORD")
site_name = os.getenv("SITE_NAME")

# Subject for mail
subject = os.getenv("SUBJECT")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API endpoints
login_url = f"https://{controller_ip}:{controller_port}/api/login"
logout_url = f"https://{controller_ip}:{controller_port}/api/logout"
ap_url = f"https://{controller_ip}:{controller_port}/api/s/{site_name}/stat/device"
restart_ap_url = f"https://{controller_ip}:{controller_port}/api/s/{site_name}/cmd/devmgr/restart"

# Login to UniFi controller
login_data = {"username": controller_username, "password": controller_password}
login_response = requests.post(login_url, json=login_data, verify=True)

if login_response.status_code == 200:
    logging.info("Login successful. Starting Rolling Restart.")
    cookies = login_response.cookies

    # Retrieve the list of access points
    ap_response = requests.get(ap_url, cookies=cookies, verify=False)
    if ap_response.status_code == 200:
        ap_list = ap_response.json()["data"]

        for ap in ap_list:
            if "name" not in ap:
                continue
            if ap['type'] == "uap":
                # Restart each access point
                restart_response = requests.post(restart_ap_url, json={"mac": ap["mac"]}, cookies=cookies, verify=False)

                if restart_response.status_code == 200:
                    logging.info(f"Access point {ap['mac']} restart command issued.")

                    # Wait for the access point to come back online or until 5 minutes have passed
                    timeout = time.time() + 300  # 5 minutes timeout
                    while True:
                        if time.time() > timeout:
                            logging.warning(f"Timeout occurred for access point {ap['mac']}. Moving to the next AP.")
                            break

                        # Check the status of the access point
                        ap_status_response = requests.get(ap_url, cookies=cookies, verify=False)
                        if ap_status_response.status_code == 200:
                            ap_status_list = ap_status_response.json()["data"]
                            for ap_status in ap_status_list:
                                if ap_status["_id"] == ap["_id"]:
                                    if ap_status["state"] == 1:  # Access point is online
                                        logging.info(f"Access point {ap['mac']} is back online.")
                                        break
                            else:
                                time.sleep(5)  # Wait for 5 seconds before checking the status again
                                continue
                        else:
                            logging.error(f"Failed to retrieve the status of access point {ap['mac']}. Moving to the next AP. "
                                          f"Status Code: {ap_status_response.status_code}")
                            break

                        break  # Break out of the while loop if the access point is online
                else:
                    logging.error(f"Failed to issue restart command for access point {ap['mac']}. Status Code: {restart_response.status_code}")

        # Create a new list to store ap's items
        new_ap_list = []

        for ap in ap_list:
            if "name" not in ap:  # devices without alias don't have a 'name' field
                continue
            if ap["type"] == "uap" and ap["state"] != 1:
                new_ap_list.append({
                    "Name": ap["name"],
                    "MAC Address": ap["mac"],
                    "IP Address": ap["ip"],
                    "State": ap["state"]
                })

        if new_ap_list:
            # Convert new_ap_list into a formatted string
            subject = "UAP restart issues"
            body = "The following devices are experiencing issues\n\n"
            for ap in new_ap_list:
                for key, value in ap.items():
                    body += f"{key}: {value}\n"
                body += "\n"

            mail_notification(subject, body)

    else:
        logging.error(f"Failed to retrieve the list of access points. Status Code: {ap_response.status_code}")

    # Logout from UniFi controller
    logout_response = requests.post(logout_url, cookies=cookies, verify=False)
    if logout_response.status_code == 200:
        logging.info("Logout successful. Rolling Restart completed.")
    else:
        logging.error("Failed to logout.")
else:
    logging.error(f"Login failed. Status Code: {login_response.status_code}")
