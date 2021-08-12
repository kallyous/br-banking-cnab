import os
import json
from collections import OrderedDict

from cnab import FileHeader, FileTrailer


class CNAB240InvalidValueError(Exception):
    """Exceção lançada quando um valor inválido para certo campo é alcançado."""

    def __init__(self, field, message='\n\tValor do campo {0} não pode ser nulo. '
                                           'Verifique se há algum default pra usar ou defina um valor.'):
        self.message = message.format(field)
        super().__init__(self.message)


class LoteCNAB240:
    """Define um lote genérico para um arquivo CNAB 240."""

    batch_header = None
    batch_trailer = None


class ArquivoCNAB240:
    """Define um arquivo CNAB 240."""

    file_header = FileHeader()
    batches = []
    file_trailer = FileTrailer()

    def build(self, data, strict=False):

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
                    raise CNAB240InvalidValueError(key)
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

    def make(self, strict=True):
        # String a receber conteúdo final.
        data_str = ''

        # Concatena conteúdo do cabeçalho do arquivo de remessa.
        data_str += self.build(self.file_header, strict=strict)

        # Passa por todos os lotes, e concatena.
        for batch in self.batches:
            data_str += self.build(batch, strict=strict)

        # Concatena conteúdo do trailer do arquivo de remessa.
        data_str += self.build(self.file_trailer, strict=strict)

        # String final.
        return data_str

    def __str__(self):
        return self.make(strict=False)
