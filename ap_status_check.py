import os
import time
import json
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

states = {0: "disconnected",
          1: "connected",
          4: "upgrading",
          5: "provisioning",
          6: "heartbeat missed"}

# File to keep track of offline APs states
offline_aps_file = "offline_aps.json"

# load the APs data
if os.path.exists(offline_aps_file):
    with open(offline_aps_file, "r") as file:
        offline_aps = json.load(file)
else:
    offline_aps = {}

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
            state = ap["state"]
            print(f"Checking Access point {ap['name']} / {ap['mac']}.")
            if "name" not in ap: # devices without alias don't have a 'name' field and won't be checked
                continue
            if ap["state"] != 1 and ap["type"] == "uap":

                # Wait 5 minutes for the access point to come back online, if not add it to the list of access points
                # with issues
                timeout = time.time() + 300  # 5 minutes timeout
                while True:
                    if time.time() > timeout:
                        ap_key = ap["mac"]
                        if ap_key not in offline_aps:
                            new_ap_list.append({
                            "Name": ap["name"],
                            "MAC Address": ap["mac"],
                            "IP Address": ap["ip"],
                            "State": f"{state} ({states[state]})"
                        })
                        offline_aps[ap_key] = True
                        print(f"Added {ap['name']} / {ap['mac']} to offline_aps.")
                        break

                    # Check the status of the access point
                    ap_status_response = requests.get(ap_url, cookies=cookies, verify=False)
                    if ap_status_response.status_code == 200:
                        ap_status_list = ap_status_response.json()["data"]
                        for ap_status in ap_status_list:
                            if ap_status["_id"] == ap["_id"]:
                                if ap_status["state"] == 1:  # Access point is online
                                    ap_key = ap["mac"]
                                    if ap_key in offline_aps:
                                       del offline_aps[ap_key]
                                    break
                        else:
                            time.sleep(5)  # Wait for 5 seconds before checking the status again
                            continue
                    else:
                        print(f"Failed to retrieve the status of access point {ap['mac']}. Moving to the next AP. "
                              f"Status Code: ", ap_status_response.status_code)
                        break

                    break  # Break out of the while loop if the access point is online


            else:
                    print(f"Access point {ap['name']} / {ap['mac']} appears to be online.")
                    ap_key = ap["mac"]
                    if ap_key in offline_aps:
                        del offline_aps[ap_key]
        if new_ap_list:
            # Convert new_ap_list into a formatted string
            subject = "UAP connectivity check"
            body = "The following devices are experiencing issues\n\n"
            for ap in new_ap_list:
                for key, value in ap.items():
                    body += f"{key}: {value}\n"
                body += "\n"

            mail_notification(subject, body)

        with open(offline_aps_file, "w") as file:
            json.dump(offline_aps, file)

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

