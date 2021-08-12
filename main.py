from cnab.cnab240 import ArquivoCNAB240

cnab = ArquivoCNAB240()

if __name__ == '__main__':
    print(cnab.file_header['codigo_banco']['val'])
    print(cnab.file_trailer['codigo_lote']['val'])
    print()
    print(cnab)
