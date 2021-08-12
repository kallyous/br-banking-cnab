import json
import os
import enum
from collections import OrderedDict

from cnab import FileHeader, FileTrailer, DATA_DIR


class BatchType(enum.Enum):
    """Templates de tipos de lotes presentes e implementados (ou a caminho).

    Exemplo de uso:
        1 - carregar o template do cabeçalho de um lote de boletos:
            template_path = BatchType.Boleto_PIXqrcode.value.format('header')
            with open(template_path, 'r') as file:
                header_batch_data = json.load(file, object_pairs_hook=OrderedDict)

        2 - carregar o template do rodapé do mesmo lote:
            template_path = BatchType.Boleto_PIXqrcode.value.format('trailer')
            with open(template_path, 'r') as file:
                trailer_batch_data = json.load(file, object_pairs_hook=OrderedDict)
    """

    # Template de header/trailer de lote para pagamentos em cheque, OP, DOC, TED, PIX ou crédito em conta corrente.
    Cheq_OP_DOC_TED_PIX_CredCC = os.path.join(DATA_DIR, '{0}_batch_check_op_doc_ted_pix.json')

    # Template de header/trailer de lote para pagamentos em boleto ou PIX QRcode.
    Boleto_PIXqrcode = 'NÃO IMPLEMENTADO! Será o própximo a ser feito.'


class CNAB240InvalidValueError(Exception):
    """Exceção lançada quando um valor inválido para certo campo é alcançado."""

    def __init__(self, field, value, message='\n\tValor do campo \'{0}\' não pode ser \'{1}\'. '
                                             'Verifique se há algum default pra usar ou defina um valor adequado.'):
        self.message = message.format(field, value)
        super().__init__(self.message)


class CNAB240InvalidBatchType(Exception):
    """Exceção lançada quando um tipo inválido de lote é usado na criação de um lote de registros."""

    def __init__(self, reg_type):
        self.message = f'\n\tTipo de lote \'{reg_type}\' é inválido. Valores possíveis são'
        for value in BatchType:
            self.message += f' {value},'
        self.message = self.message.rstrip(',') + ' .'
        super().__init__(self.message)


def bake_cnab240_string(data, strict=False):
    """Navega template de bloco de dados CNAB 240 e gera a string."""

    # String a receber conteúdo final.
    data_str = ''

    # Concatena conteúdo iterando por seus elementos
    for key in data:

        val = data[key]['val']  # Valor do campo.
        size = data[key]['size']  # Tamanho do campo.
        val_type = data[key]['type']  # Tipo do valor.

        # Tratamento de valor nulo.
        if val is None:
            if strict:
                raise CNAB240InvalidValueError(key, val)
            else:
                val = '?' * size
        # Valores válidos são usados como strings.
        else:
            val = str(val)

        # Completa os campos de tamanho variável com ' ' até atingir o tamanho certo e expande
        # os campos que são em branco mesmo. Usa 0 à esquerda para valores numéricos.
        if len(val) < size:
            if val_type == 'num':
                val = '0' * (size - len(val)) + str(val)
            else:
                val = ' ' * (size - len(val)) + val

        data_str += val

    return data_str


class RegistroCNAB240:
    """Define um registro de detalhes para uma transação que vai dentro de um lote CNAB 240."""
    fuck = 'me'


class LoteCNAB240:
    """Define um lote genérico para um arquivo CNAB 240."""

    batch_header = None
    records = []
    batch_trailer = None

    def __init__(self, batch_type):

        # Dispara erro se tipo de lote for inválido/não-implementado.
        if batch_type not in [item for item in BatchType]:
            raise CNAB240InvalidBatchType(batch_type)

        # Carrega template do cabeçalho do lote.
        with open(batch_type.value.format('header'), 'r') as file:
            self.batch_header = json.load(file, object_pairs_hook=OrderedDict)

        # Carrega template do rodapé do lote.
        with open(batch_type.value.format('trailer'), 'r') as file:
            self.batch_trailer = json.load(file, object_pairs_hook=OrderedDict)

    def make(self, strict=True):

        # String a receber conteúdo final.
        data_str = ''

        # Concatena conteúdo do cabeçalho do arquivo de remessa.
        data_str += bake_cnab240_string(self.batch_header, strict=strict)

        # Passa por todos os lotes, e concatena.
        for record in self.records:
            data_str += record.make(strict=strict)

        # Concatena conteúdo do trailer do arquivo de remessa.
        data_str += bake_cnab240_string(self.batch_trailer, strict=strict)

        # String final.
        return data_str

    def __str__(self):
        return self.make(strict=False)


class ArquivoCNAB240:
    """Define um arquivo CNAB 240."""

    file_header = FileHeader()
    batches = []
    file_trailer = FileTrailer()

    def make(self, strict=True):

        # String a receber conteúdo final.
        data_str = ''

        # Concatena conteúdo do cabeçalho do arquivo de remessa.
        data_str += bake_cnab240_string(self.file_header, strict=strict)

        # Passa por todos os lotes, e concatena.
        for batch in self.batches:
            data_str += batch.make(strict=strict)

        # Concatena conteúdo do trailer do arquivo de remessa.
        data_str += bake_cnab240_string(self.file_trailer, strict=strict)

        # String final.
        return data_str

    def __str__(self):
        return self.make(strict=False)
