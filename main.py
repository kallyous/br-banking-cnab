from cnab.cnab240 import ArquivoCNAB240, LoteCNAB240, RegistroCNAB240, BatchTemplate240, FileTemplate240, RecordTemplate240

if __name__ == '__main__':
    print()
    cnabfile = ArquivoCNAB240(FileTemplate240.FileItau)
    cnabbatch = LoteCNAB240(BatchTemplate240.Itau_Cheq_OP_DOC_TED_PIX_CredCC)
    cnabbatch.add(RegistroCNAB240(RecordTemplate240.Itau_Cheq_OP_DOC_TED_PIX_CredCC))
    cnabbatch.add(RegistroCNAB240(RecordTemplate240.Itau_Cheq_OP_DOC_TED_PIX_CredCC))
    cnabfile.add(cnabbatch)
    print(cnabfile)

    # RegistroCNAB240(RecordType240.Cheq_OP_DOC_TED_PIX_CredCC).add('asd')
    # print(cnab.file_header['codigo_banco']['val'])
    # print(cnab.file_trailer['codigo_lote']['val'])
    # print('\nDando print() pra debug, preenche com ? nos valores faltando.')
    # print(cnab)
    # print('\nChamando a função cnab.make() lança erro se algum campo estiver nulo:')
    # print(cnab.make())
    # print('Teste de erro de LoteCNAB240')
    # batch = LoteCNAB240(BatchType.Cheq_OP_DOC_TED_PIX_CredCC)
