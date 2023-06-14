import requests
import json
import logging
import time
logger = logging.getLogger(__name__)

class FactREST:
    #TODO add the remaining REST PUT and GET methods from http://localhost:5000/doc/
    #TODO add return values to methods
    def __init__(self, address):
        self.address = address
        self.get_status()

    def get_status(self):
        url = f"{self.address}/rest/status"
        response = requests.get(url)

        if response.status_code == 200:
            logger.info("Rest get_status request successful")
            data = response.json()
            logger.info("Backend Status: %s ", data['system_status']['backend']['status'])
            logger.info("Database Status: %s ", data['system_status']['database']['status'])
            logger.info("Frontend Status: %s", data['system_status']['frontend']['status'])
            return data
        else:
            logger.warning("Request failed with status code: %s ", response.status_code)
            data = response.json()
            return data

    def get_fw(self, offset=0, limit=0, query={}, recursive=False, inverted=False, uid=None, summary=False):
        if uid:
            url = f"{self.address}/rest/firmware/{uid}"
            params = {
                'request': {
                    'summary': summary
                }
            }
        else:
            url = f"{self.address}/rest/firmware"
            params = {
                'request': {
                    'offset': offset,
                    'limit': limit,
                    'query': query,
                    'recursive': recursive,
                    'inverted': inverted
                }
            }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            logger.info("Rest get_fw was successful")
            data = response.json()
            # Process the firmware data as needed
            logger.debug("Firmware data:", data)
        else:
            logger.warning("Request failed with status code:", response.status_code)

    def put_fw(self, payload):
        url = f"{self.address}/rest/firmware"

        headers = {
            'Content-Type': 'application/json'
        }
        status = self.get_status()
        if status['system_status']['backend']['unpacking']['is_throttled']:
            print("Unpacking throttled: Sleep")
            time.sleep(60)
        response = requests.put(url, data=json.dumps(payload), headers=headers)

        if response.status_code == 200:
            logger.info("Rest put_fw was successful")
            data = response.json()
            # Process the response data as needed
            logger.debug("Response data:", data)
        else:
            logger.warning("Request failed with status code:", response.status_code)

    def update_fw_analysis(self, uid, update):
        url = f"{self.address}/rest/firmware/{uid}"
        params = {
            'update': json.dumps(update)
        }
        response = requests.put(url, params=params)

        if response.status_code == 200:
            logger.info("Rest update_fw_analysis was successful")
            data = response.json()
            # Process the response data as needed
            logger.debug("Response data:", data)
        else:
            logger.warning("Request failed with status code:", response.status_code)
