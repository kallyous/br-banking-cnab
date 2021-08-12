import json
import os
from collections import OrderedDict

CWD = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(CWD, 'data')

HEADER_FILE_DIR = os.path.join(CWD, DATA_DIR, 'header_file.json')
TRAILER_FILE_DIR = os.path.join(CWD, DATA_DIR, 'trailer_file.json')


def FileHeader(file_path=HEADER_FILE_DIR):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return OrderedDict(data)


def FileTrailer(file_path=TRAILER_FILE_DIR):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return OrderedDict(data)
