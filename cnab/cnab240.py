import os
import enum

from cnab import DATA_DIR, BlocoCNAB


class FileType240(enum.Enum):
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


class BatchType240(enum.Enum):
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


class RecordType240(enum.Enum):
    """Templates de tipos de registro CNAB 240 presentes e implementados.

    Exemplo de uso:

    1 - Carregar o template de registro para um pagamento TED:
        template_path = RecordType240.Itau_Cheq_OP_DOC_TED_PIX_CredCC.value
        with open(template_path, 'r') as file:
            content = json.load(file, object_pairs_hook=OrderedDict)
        """

    # Registro de seguimento A tipo cheque, OP, DOC, TED, PIX ou crédito em conta corrente.
    Itau_Cheq_OP_DOC_TED_PIX_CredCC = os.path.join(DATA_DIR, 'itau_240_registro_seg_A_cheq_op_doc_ted_pix_credcc.json')


class CNAB240InvalidRecordTypeError(Exception):
    """Exceção lançada quando um tipo inválido de registro é usado na criação de um registro."""

    def __init__(self, record_type):
        self.message = f'\n\tTipo de registro \'{record_type}\' é inválido. Valores possíveis são'
        for value in RecordType240:
            self.message += f' {value},'
        self.message = self.message.rstrip(',') + ' .'
        super().__init__(self.message)


class CNAB240InvalidBatchTypeError(Exception):
    """Exceção lançada quando um tipo inválido de lote é usado na criação de um lote de registros."""

    def __init__(self, batch_type):
        self.message = f'\n\tTipo de lote \'{batch_type}\' é inválido. Valores possíveis são'
        for value in BatchType240:
            self.message += f' {value},'
        self.message = self.message.rstrip(',') + ' .'
        super().__init__(self.message)


class CNAB240InvalidFileTypeError(Exception):
    """Exceção lançada quando um tipo inválido de arquivo é usado na criação de um arquivo de remessas."""

    def __init__(self, file_type):
        self.message = f'\n\tTipo de arquivo \'{file_type}\' é inválido. Valores possíveis são'
        for value in FileType240:
            self.message += f' {value},'
        self.message = self.message.rstrip(',') + ' .'
        super().__init__(self.message)


class RegistroCNAB240(BlocoCNAB):
    """Define um registro de detalhes para uma transação que vai dentro de um lote CNAB 240."""

    def __init__(self, record_type):

        # Dispara erro se tipo de registro for inválido/não-implementado.
        if record_type not in [item for item in RecordType240]:
            raise CNAB240InvalidRecordTypeError(record_type)

        # Chama construtor da superclasse, responsável por carregar template em content.
        super().__init__(record_type, enclosed=False)


class LoteCNAB240(BlocoCNAB):
    """Define um lote de registros para um arquivo CNAB 240."""

    def __init__(self, batch_type):

        # Dispara erro se tipo de lote for inválido/não-implementado.
        if batch_type not in [item for item in BatchType240]:
            raise CNAB240InvalidBatchTypeError(batch_type)

        # Chama construtor da superclasse, responsável por carregar header, trailer e preparar content = [].
        super().__init__(batch_type, enclosed=True)


class ArquivoCNAB240(BlocoCNAB):
    """Define um arquivo de remessa CNAB 240."""

    def __init__(self, file_type):

        # Dispara erro se tipo de arquivo for inválido/não-implementado.
        if file_type not in [item for item in FileType240]:
            raise CNAB240InvalidFileTypeError(file_type)

        # Chama construtor da superclasse, responsável por carregar header, header e preparar content = [].
        super().__init__(file_type, enclosed=True)
