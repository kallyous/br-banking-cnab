from cnab.cnab240 import ArquivoCNAB240, LoteCNAB240, RegistroCNAB240, BatchType

if __name__ == '__main__':
    cnab = ArquivoCNAB240()
    cnab.batches.append(LoteCNAB240(BatchType.Cheq_OP_DOC_TED_PIX_CredCC))
    cnab.batches.append(LoteCNAB240(BatchType.Cheq_OP_DOC_TED_PIX_CredCC))
    print(cnab)
    # print(cnab.file_header['codigo_banco']['val'])
    # print(cnab.file_trailer['codigo_lote']['val'])
    # print('\nDando print() pra debug, preenche com ? nos valores faltando.')
    # print(cnab)
    # print('\nChamando a função cnab.make() lança erro se algum campo estiver nulo:')
    # print(cnab.make())
    # print('Teste de erro de LoteCNAB240')
    # batch = LoteCNAB240(BatchType.Cheq_OP_DOC_TED_PIX_CredCC)
