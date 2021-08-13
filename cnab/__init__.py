import json
import os
from collections import OrderedDict

CWD = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(CWD, 'data')


class CNABInvalidValueError(Exception):
    """Exceção lançada quando um valor inválido para certo campo é alcançado."""

    def __init__(self, field, value, message='\n\tValor do campo \'{0}\' não pode ser \'{1}\'. '
                                             'Verifique se há algum default pra usar ou defina um valor adequado.'):
        self.message = message.format(field, value)
        super().__init__(self.message)


class CNABInvalidOperationError(Exception):
    """Exceção laançada quando uma operação não suportada por certa classe é chamada."""

    def __init__(self, class_name, method_name, extra_msg='',
                 message='\n\tA classe {0} não suporta o método {1}. {2}'):
        self.message = message.format(class_name, method_name, extra_msg)
        super().__init__(self.message)


def bake_cnab_string(data, strict=False):
    """Navega template de bloco de dados CNAB e gera a string."""

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
                raise CNABInvalidValueError(key, val)
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


class BlocoCNAB:
    header = None
    content = None
    trailer = None
    enclosed = None

    def __init__(self, block_type, enclosed):
        self.enclosed = enclosed

        # Se não for do tipo [header ... footer], não se edita o nome do arquivo a ser carregado pois só há um.
        if not enclosed:
            with open(block_type.value, 'r') as file:
                self.content = json.load(file, object_pairs_hook=OrderedDict)

        # Blocos do tipo [header ... footer] ajustam o nome pra carregar as duas partes.
        else:
            # Carrega template do cabeçalho do lote.
            with open(block_type.value.format('header'), 'r') as file:
                self.header = json.load(file, object_pairs_hook=OrderedDict)

            # Carrega template do rodapé do lote.
            with open(block_type.value.format('trailer'), 'r') as file:
                self.trailer = json.load(file, object_pairs_hook=OrderedDict)

            # Prepara lista para receber os filhos.
            self.content = []

    def make(self, strict=True):

        # Se for do tipo [header ... trailer]
        if self.enclosed:

            # String a receber conteúdo final.
            data_str = ''

            # Concatena conteúdo do cabeçalho do arquivo de remessa.
            data_str += bake_cnab_string(self.header, strict=strict)

            # Passa por todos os lotes, e concatena.
            for batch in self.content:
                data_str += batch.make(strict=strict)

            # Concatena conteúdo do trailer do arquivo de remessa.
            data_str += bake_cnab_string(self.trailer, strict=strict)

        # Senão é do tipo registro único.
        else:
            data_str = bake_cnab_string(self.content, strict=strict)

        # String final.
        return data_str

    def add(self, entry):
        if not self.enclosed:
            raise CNABInvalidOperationError(self.__class__.__name__, 'add(entry)',
                                            'Este método é aplicável apenas para blocos que possuem header e trailer, '
                                            'para adicionar filhos ao seu conteúdo.')
        else:
            self.content.append(entry)

    def __str__(self):
        return self.make(strict=False)
