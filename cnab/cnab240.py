import os
import json
from collections import OrderedDict

from cnab import FileHeader, FileTrailer


class CNAB240InvalidValueError(Exception):
    """Exceção lançada quando um valor inválido para certo campo é alcançado."""
    
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class LoteCNAB240:
    """Define um lote genérico para um arquivo CNAB 240."""

    batch_header = None
    batch_trailer = None


class ArquivoCNAB240:
    """Define um arquivo CNAB 240."""

    file_header = FileHeader()
    batches = []
    file_trailer = FileTrailer()

    def __str__(self):

        # String a receber conteúdo final.
        data_str = ''

        # Concatena conteúdo do cabeçalho do arquivo de remessa.
        for key in self.file_header:

            # Valores relevantes.
            val = self.file_header[key]['val']
            if val is None:
                val = ''
            else:
                val = str(val)
            size = self.file_header[key]['size']
            val_type = self.file_header[key]['type']

            # Completa os campos de tamanho variável com ' ' até atingir o tamanho certo,
            # e expande os campos que são em branco mesmo.
            if len(val) < size:
                if val_type == 'num':
                    val = ' ' * (size - len(val)) + str(val)
                else:
                    val += ' ' * (size - len(val))

            data_str += val

        # Passa por todos os lotes.
        for batch in self.batches:
            pass

        # Concatena conteúdo do trailer do arquivo de remessa.
        for key in self.file_trailer:

            # Valores relevantes.
            val = self.file_trailer[key]['val']
            if val is None: val = ''
            else: val = str(val)
            size = self.file_trailer[key]['size']
            val_type = self.file_trailer[key]['type']

            # Completa os campos de tamanho variável com ' ' até atingir o tamanho certo,
            # e expande os campos que são em branco mesmo.
            if len(val) < size:
                if val_type == 'num':
                    # Campos numéricos recebem zeros à esquerda.
                    val = '0' * (size - len(val)) + str(val)
                else:
                    # Campos alfanum recebem espaço em branco.
                    val = val + (' ' * (size - len(val)))

            data_str += val

        # String final.
        return data_str
