import os
import time

import requests
import urllib3
from dotenv import load_dotenv

# load environment variables from .env_example file in same directory
from mail_notification import mail_notification

load_dotenv()

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
    print("Login successful.")
    cookies = login_response.cookies

    ap_response = requests.get(ap_url, cookies=cookies, verify=False)
    if ap_response.status_code == 200:
        ap_list = ap_response.json()["data"]

        # Create a new list to store ap's items
        new_ap_list = []

        for ap in ap_list:
            if "name" not in ap: # devices without alias don't have a 'name' field
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
            subject = "UAP connectivity check"
            body = "The following devices are experiencing issues\n\n"
            for ap in new_ap_list:
                for key, value in ap.items():
                    body += f"{key}: {value}\n"
                body += "\n"

            mail_notification(subject, body)

    else:
        print("Failed to retrieve the list of access points. Status Code: ", ap_response.status_code)

    # Logout from UniFi controller
    logout_response = requests.post(logout_url, cookies=cookies, verify=False)
    if logout_response.status_code == 200:
        print("Logout successful.")
    else:
        print("Failed to logout.")
else:
    print("Login failed. Status Code: ", login_response.status_code)
