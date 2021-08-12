from cnab.cnab240 import ArquivoCNAB240

cnab = ArquivoCNAB240()

if __name__ == '__main__':
    print(cnab.file_header['codigo_banco']['val'])
    print(cnab.file_trailer['codigo_lote']['val'])
    print('\nDando print() pra debug, preenche com ? nos valores faltando.')
    print(cnab)
    print('\nChamando a função cnab.make() lança erro se algum campo estiver nulo:')
    print(cnab.make())
