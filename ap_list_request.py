import os
import requests
import urllib3

# Retrieve UniFi controller details from environment variables
controller_ip = os.getenv("CONTROLLER_IP")
controller_port = os.getenv("CONTROLLER_PORT")
controller_username = os.getenv("CONTROLLER_USERNAME")
controller_password = os.getenv("CONTROLLER_PASSWORD")
site_name = os.getenv("SITE_NAME")

# Disable warnings about insecure requests to avoid cluttering the output.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API endpoints
login_url = f"https://{controller_ip}:{controller_port}/api/login"
logout_url = f"https://{controller_ip}:{controller_port}/api/logout"
ap_url = f"https://{controller_ip}:{controller_port}/api/s/{site_name}/stat/device"
restart_ap_url = f"https://{controller_ip}:{controller_port}/api/s/{site_name}/cmd/devmgr/restart"

# for debug purposes
# print(requests.get(f"https://{controller_ip}:{controller_port}/status").text)

# Login to UniFi controller
login_data = {"username": controller_username, "password": controller_password}
login_response = requests.post(login_url, json=login_data, verify=True)

if login_response.status_code == 200:
    print("Login successful.")
    cookies = login_response.cookies

    # get data for all access points of current site
    ap_response = requests.get(ap_url, cookies=cookies, verify=True)
    if ap_response.status_code == 200:
        ap_data = ap_response.json()
        access_points = ap_data["data"]

        # Iterate over the access points and print their details
        for ap in access_points:
            print("Access Point:")
            print(f"Name: {ap['name']}")
            print(f"MAC Address: {ap['mac']}")
            print(f"Model: {ap['model']}")
            print(f"Status: {ap['state']}")
            print("")
    else:
        print("AP request failed. Status Code: ", ap_response.status_code)

    # Logout from UniFi controller
    logout_response = requests.post(logout_url, cookies=cookies, verify=False)
    if logout_response.status_code == 200:
        print("Logout successful.")
    else:
        print("Failed to logout. Status Code: ", logout_response.status_code)

else:
    print("Login failed. Status Code: ", login_response.status_code)
