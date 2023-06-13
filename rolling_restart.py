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

    # Retrieve the list of access points
    ap_response = requests.get(ap_url, cookies=cookies, verify=False)
    if ap_response.status_code == 200:
        ap_list = ap_response.json()["data"]

        for ap in ap_list:
            # Restart each access point
            restart_ap_url_with_mac = f"{restart_ap_url}/{ap['_id']}"
            restart_response = requests.post(restart_ap_url_with_mac, cookies=cookies, verify=False)

            if restart_response.status_code == 200:
                print(f"Access point {ap['mac']} restart command issued.")

                # Wait for the access point to come back online or until 5 minutes have passed
                timeout = time.time() + 300  # 5 minutes timeout
                while True:
                    if time.time() > timeout:
                        print(f"Timeout occurred for access point {ap['mac']}. Moving to the next AP.")
                        break

                    # Check the status of the access point
                    ap_status_response = requests.get(ap_url, cookies=cookies, verify=False)
                    if ap_status_response.status_code == 200:
                        ap_status_list = ap_status_response.json()["data"]
                        for ap_status in ap_status_list:
                            if ap_status["_id"] == ap["_id"]:
                                if ap_status["state"] == 1:  # Access point is online
                                    print(f"Access point {ap['mac']} is back online.")
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
                print(f"Failed to issue restart command for access point {ap['mac']}. Status Code: ",
                      restart_response.status_code)

        print("Rolling restart of access points completed.")

        # List for AP's which encountered issues
        body = "List of all UAP's currently online\n"

        # Retrieve AP information and send mail if error occurred
        ap_response = requests.get(ap_url, cookies=cookies, verify=False)
        if ap_response.status_code == 200:
            ap_list = ap_response.json()["data"]

            for ap in ap_list:
                if "name" not in ap:
                    continue
                if ap["state"] == 1 and ap['type'] == "uap":
                    body += "Access Point:" + "\n" f"Name: {ap['name']}" + "\n" f"MAC Address: {ap['mac']}" + "\n\n"

        if body != "":
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
