import zipfile
import os
import base64
from firmware.items import FirmwareImage

class Unpacker:
    def __init__(self, firmware_image):
        self.firmware_image = firmware_image
        self.zip_file = "./output/" + self.firmware_image['files'][0]['path']
        self.binary = None
        self.destination = None

    def extract(self):
        self.destination = os.path.splitext(self.zip_file)[0]
        with zipfile.ZipFile(self.zip_file, 'r') as zip_ref:
            zip_ref.extractall(self.destination)
        return self.destination

    def has_binary(self):
        with zipfile.ZipFile(self.zip_file, 'r') as zip_ref:
            for name in zip_ref.namelist():
                if name.endswith(".bin"):
                    self.binary = name
                    return True
        return False

    def file_to_base64(self):
        if self.destination and self.binary:
            binary_path = self.destination + "/" + self.binary
            print(binary_path)
        with open(binary_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode("utf-8")
        return encoded_string


