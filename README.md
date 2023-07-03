# unifi-api-scripts

## Files

### ap_list_request.py

This script retrieves the details of all access points in the UniFi controller's current site. It uses the environment variables defined in the `.env` file for authentication and configuration.

### ap_status_check.py

This script checks the connectivity status of access points in the UniFi controller's current site. If any access points are found to have connection issues, a notification email is sent. The script  relies on the `.env` file for configuration.

### restart_ap_by_mac.py

This script restarts a specific access point identified by its MAC address. The MAC address of the access point to restart should be provided as an environment variable in the `.env` file.

### rolling_restart.py

This script performs a rolling restart of all access points in the UniFi controller's current site. It restarts each access point individually, waits for it to come back online, and then moves on to the next access point. If any access points fail to restart, a notification email is sent. The script relies on the `.env` file for configuration.

### mail_notification.py

A utility script for sending notification emails. It uses the environment variables defined in the `.env` file for the SMTP server configuration and email addresses.


### UAP state values

0 = disconnected
1 = connected
4 = upgrading
5 = provisioning
6 = heartbeat missed


## Installation

1. Clone this repository to your local machine.
2. Install the required dependencies by running `pip install -r requirements.txt`.

## Usage

1. Set up the necessary environment variables by creating a `.env` file and filling in the required values. Use the `.env_example` file as a template.
2. Run the desired script using Python. For example: `python ap_list_request.py`.

## Contributing

Contributions to this repository are welcome. If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.

