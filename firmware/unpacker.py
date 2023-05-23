import zipfile
import os
import base64
import rarfile

'''TODO:
    -Add additional archive types if necessary, for the scope of TP-Link it's enough to have zip and rar
    -add additional binary types if necessary, for scope TP-Link .bin is enough but other vendors could have .img or similar
    -Code the clean_up method, see TODO beyond'''
class Unpacker:
    def __init__(self, firmware_image):
        self.firmware_image = firmware_image
        self.packed_file = "./output/" + self.firmware_image['files'][0]['path']
        # Get the file extension
        packed_file_extension = os.path.splitext(self.packed_file)[1]
        # Assign the file extension to packed_file_type
        self.packed_file_type = packed_file_extension[1:]  # Remove the leading dot
        self.binary = None
        self.destination = None

    def extract(self):
        self.destination = os.path.splitext(self.packed_file)[0]
        match self.packed_file_type:
            case "zip":
                with zipfile.ZipFile(self.packed_file, 'r') as zip_ref:
                    zip_ref.extractall(self.destination)
            case "rar":
                with rarfile.RarFile(self.packed_file, 'r') as rar_ref:
                    rar_ref.extractall(self.destination)
        return self.destination

    def has_binary(self):
        match self.packed_file_type:
            case "zip":
                with zipfile.ZipFile(self.packed_file, 'r') as zip_ref:
                    for name in zip_ref.namelist():
                        if name.endswith(".bin"):
                            self.binary = name
                            return True
            case "rar":
                with rarfile.RarFile(self.packed_file, 'r') as rar_ref:
                    for name in rar_ref.namelist():
                        if name.endswith(".bin"):
                            self.binary = name
                        return True
        return False

    def file_to_base64(self):
        if self.destination and self.binary:
            binary_path = self.destination + "/" + self.binary
            print(binary_path)
        with open(binary_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        return encoded_string

    ''' TODO write a clean up method to delete the unzipped folders because right now the binaries are stored three times in the output folder,
        in the json objects, in the zip files and in the extracted output folder
        when the REST Put methods are working properly it should be enough to keep the zip files since they are used to determine if the files are up to
        date in Scrapy -- maybe look into that to determine if it's possible to change this to the json objects
    '''
    def clean_up(self):
        pass


