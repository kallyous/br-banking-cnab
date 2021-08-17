import os
import enum

from brbankingcnab import DATA_DIR, BlocoCNAB, CNABError, CNABInvalidTemplateError, CNABInvalidOperationError


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

    # Registro de seguimento A tipo cheque, OP, DOC, TED, PIX ou crédito em conta corrente.
    Itau_Cheq_OP_DOC_TED_PIX_CredCC = os.path.join(DATA_DIR, 'itau_240_registro_seg_A_cheq_op_doc_ted_pix_credcc.json')


class RegistroCNAB240(BlocoCNAB):
    """Define um registro de detalhes para uma transação que vai dentro de um lote CNAB 240."""

    def __init__(self, record_type):
        # Dispara erro se tipo de registro for inválido/não-implementado.
        if record_type not in [item for item in RecordTemplate240]:
            raise CNABInvalidTemplateError(record_type, self.__class__.__name__, RecordTemplate240)

        # Chama construtor da superclasse, responsável por carregar template em content.
        super().__init__(record_type, enclosed=False)


class LoteCNAB240(BlocoCNAB):
    """Define um lote de registros para um arquivo CNAB 240."""

    def __init__(self, batch_type):
        # Dispara erro se tipo de lote for inválido/não-implementado.
        if batch_type not in [item for item in BatchTemplate240]:
            raise CNABInvalidTemplateError(batch_type, self.__class__.__name__, BatchTemplate240)

        # Chama construtor da superclasse, responsável por carregar header, trailer e preparar content = [].
        super().__init__(batch_type, enclosed=True)

    def add(self, record):

        # Dispara erro se header ou trailer estiver faltando.
        if not self.header or not self.trailer:
            raise CNABInvalidOperationError(
                class_name=self.__class__.__name__, method_name='add(lote)', extra_msg= \
                    'O header de arquivo deve ser iniciado com um template antes de adicionar lotes de registros.')

        # Atualiza 'numero_registro' do registro e o adiciona ao lote.
        try:
            record.content['numero_registro']['val'] = len(self.content) + 1  # Começa em 1 (não em zero).
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

        # Incrementa contagem de lotes no arquivo.
        try:
            self.trailer['total_qtd_registros']['val'] += 1
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

        # Incrementa valor total dos pagamentos do lote.
        try:
            self.trailer['total_valor_pagtos']['val'] += record.content['valor_pagamento']['val']
        except KeyError:
            raise CNAB240KeyError(class_name=self.__class__.__name__, method_name='add(lote)',
                                  template_name=self.template,
                                  field_name='total_valor_pagtos',
                                  message=f'O campo não foi encontrado no trailer de arquivo.')
        except TypeError as e:
            print(f'ERRO: No template {self.template} o campo total_valor_pagtos está com valor inicial'
                  f' diferente de 0 (zero)!!!')
            print(f'O erro ocorreu em {self.__class__.__name__} durante a adição de um registro ao lote, causando uma'
                  f' adição de None + Int. '
                  f'Corrija o valor inicial de total_valor_pagtos para 0 (zero inteiro) no trailer desse template.')
            raise e

        # Código de lote de cada registro é o do lote a que pertemcem.
        record.content['codigo_lote']['val'] = self.header['codigo_lote']['val']

        # Adiciona registro ao lote.
        self.content.append(record)


class ArquivoCNAB240(BlocoCNAB):
    """Define um arquivo de remessa CNAB 240."""

    def __init__(self, file_type):

        # Dispara erro se tipo de arquivo for inválido/não-implementado.
        if file_type not in [item for item in FileTemplate240]:
            raise CNABInvalidTemplateError(file_type, self.__class__.__name__, FileTemplate240)

        # Chama construtor da superclasse, responsável por carregar header, header e preparar content = [].
        super().__init__(file_type, enclosed=True)

    def add(self, batch):
        if not self.header or not self.trailer:
            raise CNABInvalidOperationError(
                class_name=self.__class__.__name__, method_name='add(lote)', extra_msg= \
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
