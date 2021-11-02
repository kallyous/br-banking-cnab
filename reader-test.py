import os
import sys

from brbankingcnab import parse_cnab_string
from brbankingcnab.cnab240 import FileTemplate240

if __name__ == '__main__':
    cnab_in_path = sys.argv[1]

    if not os.path.isfile(cnab_in_path):
        print(f'{cnab_in_path} não é um arquivo.')
        exit(1)

    with open(cnab_in_path, 'r') as file:
        in_data_str = file.read()

    cnab_file = parse_cnab_string(in_data_str, 240, FileTemplate240.FileItau)

    print(cnab_file.make(strict=False), end='')
