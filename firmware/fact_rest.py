import requests
import json
class FactREST:
    #TODO add the remaining REST PUT and GET methods from http://localhost:5000/doc/
    #TODO add return values to methods
    #TODO replace prints with logger
    def __init__(self, address):
        self.address = address
        self.get_status()

    def get_status(self):
        url = f"{self.address}/rest/status"
        response = requests.get(url)

        if response.status_code == 200:
            print("Request was successful")
            data = response.json()
            print("Backend Status: ", data['system_status']['backend']['status'])
            print("Database Status: ", data['system_status']['database']['status'])
            print("Frontend Status: ", data['system_status']['frontend']['status'])
        else:
            print("Request failed with status code: ", response.status_code)

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
            print("Request was successful.")
            data = response.json()
            # Process the firmware data as needed
            print("Firmware data:", data)
        else:
            print("Request failed with status code:", response.status_code)

    def put_fw(self, payload):
        url = f"{self.address}/rest/firmware"

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.put(url, data=json.dumps(payload), headers=headers)

        if response.status_code == 200:
            print("PUT_FW: Request was successful.")
            data = response.json()
            # Process the response data as needed
            print("Response data:", data)
        else:
            print("Request failed with status code:", response.status_code)
            print(response.json())

    def update_fw_analysis(self, uid, update):
        url = f"{self.address}/rest/firmware/{uid}"
        params = {
            'update': json.dumps(update)
        }
        response = requests.put(url, params=params)

        if response.status_code == 200:
            print("Request was successful.")
            data = response.json()
            # Process the response data as needed
            print("Response data:", data)
        else:
            print("Request failed with status code:", response.status_code)
            print(response.json())
