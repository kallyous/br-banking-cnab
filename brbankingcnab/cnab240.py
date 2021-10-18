import os
import enum

from brbankingcnab import DATA_DIR, BlocoCNAB, CNABError, CNABInvalidTemplateError, CNABInvalidOperationError, \
    BlockType

SEGMENTO_A = 'A'  # Código do seguimento A.


class CNAB240KeyError(CNABError):
    """Erro para campos inválidos ou ausentes no template de CNABs 240 ou durante a sua leitura e validação."""

    def __init__(self, class_name, method_name, field_name, template_name, message=''):
        super().__init__(f'\n\tEm {class_name}, com o template{template_name}, o método {method_name} tentou acessar'
                         f' o campo {field_name}. {message}')


class FileTemplate240(enum.Enum):
    """Enumera tipos válidos de Arquivo de Remessa CNAB 240 implementados.

    Exemplo de uso:

    1 - Carregar o template do header de um arquivo CNAB 240 do Itaú:
        template_path = FileType240.FileItau.value.format('header')
        with open(template_path, 'r') as file:
            header = json.load(file, object_pairs_hook=OrderedDict)

    2 - Carregar o template do trailer do mesmo arquivo:
        template_path = FileType240.FileItau.value.format('trailer')
        with open(template_path, 'r') as file:
            trailer = json.load(file, object_pairs_hook=OrderedDict)
    """

    FileItau = os.path.join(DATA_DIR, 'itau_240_arquivo_{0}.json')


class BatchTemplate240(enum.Enum):
    """Templates de tipos de lotes CNAB 240 presentes e implementados.

    Exemplo de uso:

    1 - Carregar o template do header de um lote de boletos:
        template_path = BatchType240.Boleto_PIXqrcode.value.format('header')
        with open(template_path, 'r') as file:
            header = json.load(file, object_pairs_hook=OrderedDict)

    2 - Carregar o template do trailer do mesmo lote:
        template_path = BatchType240.Boleto_PIXqrcode.value.format('trailer')
        with open(template_path, 'r') as file:
            trailer = json.load(file, object_pairs_hook=OrderedDict)
    """

    # Template de header/trailer de lote Itaú para pagamentos em cheque, OP, DOC, TED, PIX ou crédito em conta corrente.
    Itau_Cheq_OP_DOC_TED_PIX_CredCC = os.path.join(DATA_DIR, 'itau_240_lote_cheq_op_doc_ted_pix_credcc_{0}.json')

    # Template de header/trailer de lote Itaú para pagamentos em boleto ou PIX QRcode.
    Itau_Boleto_PIXqrcode = None  # TODO: Lote de boletos será o próximo template. ;-)


class RecordTemplate240(enum.Enum):
    """Templates de tipos de registro CNAB 240 presentes e implementados.

    Exemplo de uso:

    1 - Carregar o template de registro para um pagamento TED:
        template_path = RecordType240.Itau_Cheq_OP_DOC_TED_PIX_CredCC.value
        with open(template_path, 'r') as file:
            content = json.load(file, object_pairs_hook=OrderedDict)
        """

    # Registro de seguimento A tipo cheque, OP, DOC, TED, PIX ou crédito em conta corrente. Padrão 341 e 409
    Itau_SegA_Cheq_OP_DOC_TED_PIX_CredCC_341_409 = os.path.join(DATA_DIR,
                                                        'itau_240_registro_seg_A_cheq_op_doc_ted_pix_credcc_banco_fav_341_409.json')

    # Registro de seguimento A tipo cheque, OP, DOC, TED, PIX ou crédito em conta corrente. Padrão 341 e 409
    Itau_SegA_Cheq_OP_DOC_TED_PIX_CredCC_misc = os.path.join(DATA_DIR,
                                                        'itau_240_registro_seg_A_cheq_op_doc_ted_pix_credcc_banco_fav_misc.json')

    # Registro de seguimento B tipo cheque, OP, DOC, TED, PIX ou crédito em conta corrente.
    Itau_SegB_Cheq_OP_DOC_TED_CredCC = os.path.join(DATA_DIR,
                                                        'itau_240_registro_seg_B_cheq_op_doc_ted_credcc.json')


class RegistroCNAB240(BlocoCNAB):
    """Define um registro de detalhes para uma transação que vai dentro de um lote CNAB 240."""

    def __init__(self, record_template):
        # Dispara erro se tipo de registro for inválido/não-implementado.
        if record_template not in [item for item in RecordTemplate240]:
            raise CNABInvalidTemplateError(record_template, self.__class__.__name__, RecordTemplate240)

        self.block_type = BlockType.Regsitro

        # Chama construtor da superclasse, responsável por carregar template em content.
        super().__init__(record_template, enclosed=False)


class LoteCNAB240(BlocoCNAB):
    """Define um lote de registros para um arquivo CNAB 240."""

    def __init__(self, batch_template):
        # Dispara erro se tipo de lote for inválido/não-implementado.
        if batch_template not in [item for item in BatchTemplate240]:
            raise CNABInvalidTemplateError(batch_template, self.__class__.__name__, BatchTemplate240)

        self.block_type = BlockType.Lote

        # Chama construtor da superclasse, responsável por carregar header, trailer e preparar content = [].
        super().__init__(batch_template, enclosed=True)

        # Define quantidade de registros para 2: header e trailer.
        self.update_record_count()

    def update_record_count(self):
        num = 2  # Primeiro registro é o header de lote e último o trailer de lote.
        try:
            for record in self.content:
                # Versão que só incrementa no seguimento A
                # if record.content['segmento']['val'] == SEGMENTO_A:
                #     num += 1
                num += 1  # Versão que sempre incrementa.
            self.trailer['total_qtd_registros']['val'] = num
        except KeyError:
            raise CNAB240KeyError(class_name=self.__class__.__name__, method_name='add(lote)',
                                  template_name=self.template,
                                  field_name='total_qtd_registros',
                                  message=f'O campo não foi encontrado no trailer de arquivo.')
        except TypeError as e:
            print(f'ERRO: No template {self.template} o campo total_qtd_registros está com valor inicial'
                  f' diferente de 0 (zero)!!!')
            print(f'O erro ocorreu em {self.__class__.__name__} durante a adição de um registro ao lote, causando uma'
                  f' adição de None + Int. '
                  f'Corrija o valor inicial de total_qtd_registros para 0 (zero inteiro) no trailer desse template.')
            raise e

    def update_total_payment_value(self):
        total_payment_value = 0
        for record in self.content:
            if record.content['segmento']['val'] == SEGMENTO_A:
                try:
                    total_payment_value += record.content['valor_pagamento']['val']
                except KeyError:
                    raise CNAB240KeyError(class_name=record.__class__.__name__, method_name='LoteCNAB240.update_total_payment_value()',
                                          template_name=self.template,
                                          field_name="RegistroCNAB240.content['valor_pagamento']['val']",
                                          message=f'O campo não foi encontrado no registros.')
        self.trailer['total_valor_pagtos']['val'] = total_payment_value

    def get_record_count(self):
        return self.trailer['total_qtd_registros']['val']

    def add(self, record):

        # Dispara erro se header ou trailer estiver faltando.
        if not self.header or not self.trailer:
            raise CNABInvalidOperationError(
                class_name=self.__class__.__name__, method_name='add(lote)', extra= \
                    'O header de arquivo deve ser iniciado com um template antes de adicionar lotes de registros.')

        # Atualiza 'numero_registro' do registro e o adiciona ao lote.
        try:
            # Versão que só incrementa no seguimento A
            # if record.content['segmento']['val'] == SEGMENTO_A:
            #     record.content['numero_registro']['val'] = self.get_record_count() + 1
            # else:
            #     record.content['numero_registro']['val'] = self.get_record_count()
            record.content['numero_registro']['val'] = self.get_record_count() - 1  # count + 1 - 2, pra desconsiderar header e trailer da contagem.
        except KeyError:
            raise CNAB240KeyError(class_name=record.__class__.__name__, method_name='add(lote)',
                                  template_name=record.template,
                                  field_name='numero_registro',
                                  message=f'O campo não foi encontrado no template do registro.')
        except TypeError as e:
            print(f'ERRO: No template {record.template}, o campo numero_registro está com valor inicial diferente'
                  f' de 0 (zero)!!!')
            print(f'O erro ocorreu em {self.__class__.__name__} durante a adição de um registro ao lote, causando uma'
                  f' adição de None + Int. '
                  f'Corrija o valor inicial de numero_registro para 0 (zero inteiro) nesse template.')
            raise e

        # Incrementa valor total dos pagamentos do lote.
        self.update_total_payment_value()

        # Código de lote de cada registro é o do lote a que pertemcem.
        record.content['codigo_lote']['val'] = self.header['codigo_lote']['val']

        # Adiciona registro ao lote.
        self.content.append(record)

        # Incrementa contagem de lotes no arquivo.
        self.update_record_count()


class ArquivoCNAB240(BlocoCNAB):
    """Define um arquivo de remessa CNAB 240."""

    def __init__(self, file_template):

        # Dispara erro se tipo de arquivo for inválido/não-implementado.
        if file_template not in [item for item in FileTemplate240]:
            raise CNABInvalidTemplateError(file_template, self.__class__.__name__, FileTemplate240)

        self.block_type = BlockType.Arquivo

        # Chama construtor da superclasse, responsável por carregar header, header e preparar content = [].
        super().__init__(file_template, enclosed=True)

    def update_total_records(self):
        total_records = 2  # Primeiro registro é o header de arquivo, último é seu trailer.
        for batch in self.content:
            total_records += batch.get_record_count()
        self.trailer['total_qtd_registros']['val'] = total_records

    def add(self, batch):
        if not self.header or not self.trailer:
            raise CNABInvalidOperationError(
                class_name=self.__class__.__name__, method_name='add(lote)', extra= \
                    'O header de arquivo deve ser iniciado com um template antes de adicionar lotes de registros.')

        # Incrementa contagem de lotes no arquivo.
        try:
            self.trailer['total_qtd_lotes']['val'] += 1
        except KeyError:
            raise CNAB240KeyError(class_name=self.__class__.__name__, method_name='add(lote)',
                                  template_name=self.template,
                                  field_name='total_qtd_lotes',
                                  message=f'O campo não foi encontrado no trailer de arquivo.')
        except TypeError as e:
            print(f'ERRO: No template {self.template}, o campo total_qtd_lotes está com valor inicial diferente'
                  f' de 0 (zero)!!!')
            print(f'O erro ocorreu em {self.__class__.__name__} durante a adição de um lote, causando uma adição de'
                  f'None + Int. '
                  f'Corrija o valor inicial de total_qtd_lotes para 0 (zero inteiro) no trailer desse template.')

        # Valor de codigo_lote, que informa índice do lote. Começa em 1, por isso o incremento.
        batch_number = len(self.content) + 1

        # Atualiza codigo_lote no header do lote.
        try:
            batch.header['codigo_lote']['val'] = batch_number
        except KeyError:
            raise CNAB240KeyError(class_name=self.__class__.__name__, method_name='add(lote)',
                                  template_name=batch.template,
                                  field_name='codigo_lote',
                                  message=f'O campo não foi encontrado no header de lote.')

        # Atualiza codigo_lote no trailer do lote.
        try:
            batch.trailer['codigo_lote']['val'] = batch_number
        except KeyError:
            raise CNAB240KeyError(class_name=self.__class__.__name__, method_name='add(lote)',
                                  template_name=batch.template,
                                  field_name='codigo_lote',
                                  message=f'O campo não foi encontrado no trailer de lote.')

        # Atualiza codigo_lote em todos os registros do lote.
        for record in batch.content:
            try:
                record.content['codigo_lote']['val'] = batch_number
            except KeyError:
                raise CNAB240KeyError(class_name=self.__class__.__name__, method_name='add(lote)',
                                      template_name=record.template,
                                      field_name='codigo_lote',
                                      message=f'O campo não foi encontrado no template de registro.')

        # Adiciona lote ao arquivo.
        self.content.append(batch)

        # Atualiza contagem de registros dos lotes.
        self.update_total_records()

    def is_batch_header(self, line: str) -> bool:
        if line[7] == '1':
            return True
        else:
            return False

    def is_batch_trailer(self, line: str) -> bool:
        if line[7] == '5':
            return True
        else:
            return False

    def is_record(self, line: str) -> bool:
        if line[7] == '3':
            return True
        else:
            return False

    def new_batch_from_header(self, line: str) -> BlocoCNAB:
        print(line, self.__class__.__name__)
        return LoteCNAB240(BatchTemplate240.Itau_Cheq_OP_DOC_TED_PIX_CredCC)

    def parse_batch_trailer(self, batch: LoteCNAB240, line: str) -> bool:
        print(line, self.__class__.__name__)
        return True

    def new_record_from_str(self, line: str) -> BlocoCNAB:
        print(line, self.__class__.__name__)
        return RegistroCNAB240(RecordTemplate240.Itau_SegA_Cheq_OP_DOC_TED_PIX_CredCC_misc)
