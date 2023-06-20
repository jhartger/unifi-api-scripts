import requests
import urllib3
import os
import dotenv

dotenv.load_dotenv()


# Retrieve UniFi controller details from environment variables
controller_ip = os.getenv("CONTROLLER_IP")
controller_port = os.getenv("CONTROLLER_PORT")
controller_username = os.getenv("CONTROLLER_USERNAME")
controller_password = os.getenv("CONTROLLER_PASSWORD")
site_name = os.getenv("SITE_NAME")
ap_mac_to_restart = os.getenv("AP_MAC_TO_RESTART")

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

    # Retrieve the list of access points
    ap_response = requests.get(ap_url, cookies=cookies, verify=False)
    if ap_response.status_code == 200:
        ap_list = ap_response.json()["data"]
        ap_to_restart = None

        # Find the AP with the specified MAC address
        for ap in ap_list:
            if ap["mac"].lower() == ap_mac_to_restart.lower():
                ap_to_restart = ap

                break

        if ap_to_restart:
            # Restart the specified access point
            restart_response = requests.post(restart_ap_url, json={"mac": ap_to_restart["mac"]}, cookies=cookies, verify=False)

            if restart_response.status_code == 200:
                print("Access point restarted successfully.")
            else:
                print("Failed to restart the access point.")
        else:
            print("No access point found with the specified MAC address.")
    else:
        print("Failed to retrieve the list of access points.")

    # Logout from UniFi controller
    logout_response = requests.post(logout_url, cookies=cookies, verify=False)
    if logout_response.status_code == 200:
        print("Logout successful.")
    else:
        print("Failed to logout. Status Code: ", logout_response.status_code)

else:
    print("Login failed. Status Code: ", login_response.status_code)
