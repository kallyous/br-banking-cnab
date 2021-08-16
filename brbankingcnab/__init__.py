"""Br Banking CNAB - Package for generating Brazilian CNAB banking files as specified by FEBRABAN.

At the current development, only implements a few templates blocks for Itaú bank.
"""

__version__ = '0.1dev2'
__author__ = 'Lucas Carvalho Flores'

import json
import os
from collections import OrderedDict

CWD = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(CWD, 'templates')


class CNABInvalidValueError(Exception):
    """Exceção lançada quando um valor inválido para certo campo é alcançado."""

    def __init__(self, field, value, message='\n\tValor do campo \'{0}\' não pode ser \'{1}\'. '
                                             'Verifique se há algum default pra usar ou defina um valor adequado.'):
        self.message = message.format(field, value)
        super().__init__(self.message)


class CNABInvalidOperationError(Exception):
    """Exceção lançada quando uma operação não suportada por certa classe é chamada."""

    def __init__(self, class_name, method_name, extra_msg='',
                 message='\n\tA classe {0} não suporta o método {1}. {2}'):
        self.message = message.format(class_name, method_name, extra_msg)
        super().__init__(self.message)


class CNABInvalidTemplateError(Exception):
    """Exceção lançada quando um nome inválido de template é usado na criação de um BlocoCNAB."""

    def __init__(self, template_type, class_name, valid_templates):
        self.message = f'\n\tO template \'{template_type}\' é inválido para \'{class_name}\'. Valores válidos são'
        for value in valid_templates:
            self.message += f' {value},'
        self.message = self.message.rstrip(',') + ' .'
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

    return data_str + '\n'


class BlocoCNAB:
    header = None
    content = None
    trailer = None
    enclosed = None

    def __init__(self, block_type, enclosed):
        self.enclosed = enclosed

        # Se não for do tipo [header ... trailer], não se edita o nome do arquivo a ser carregado pois só há um.
        if not enclosed:
            with open(block_type.value, 'r') as file:
                self.content = json.load(file, object_pairs_hook=OrderedDict)

        # Blocos do tipo [header ... trailer] ajustam o nome pra carregar as duas partes, header e trailer.
        else:
            # Carrega template do header do lote.
            with open(block_type.value.format('header'), 'r') as file:
                self.header = json.load(file, object_pairs_hook=OrderedDict)

            # Carrega template do trailer do lote.
            with open(block_type.value.format('trailer'), 'r') as file:
                self.trailer = json.load(file, object_pairs_hook=OrderedDict)

            # Prepara lista para receber os filhos.
            self.content = []

    def make(self, strict=True):
        """Gera string com os dados formatados.
        Se strict == True, campos vazios não são tolerados e geram erros.
        """

        # Se for do tipo [header ... trailer]
        if self.enclosed:

            # String a receber conteúdo final.
            data_str = ''

            # Concatena conteúdo do header do arquivo de remessa.
            data_str += bake_cnab_string(self.header, strict=strict)

            # Passa por todos os filhos, e concatena.
            for child in self.content:
                data_str += child.make(strict=strict)

            # Concatena conteúdo do trailer do arquivo de remessa.
            data_str += bake_cnab_string(self.trailer, strict=strict)

        # Senão, é do tipo registro único. Gera a string e pronto.
        else:
            data_str = bake_cnab_string(self.content, strict=strict)

        # String final.
        return data_str

    def add(self, entry):
        """Adiciona ao final de self.content se o bloco for do tipo [header ... trailer], senão gera erro."""

        name = self.__class__.__name__

        # Se for um registro de detalhes ou similar, gera o erro.
        if not self.enclosed:
            raise CNABInvalidOperationError(name, 'add(entry)',
                                            'Este método é aplicável apenas a blocos que possuem header e trailer, '
                                            'para adicionar filhos ao seu conteúdo.')

        # Caso contrário, damos o .append() em self.content.
        else:
            self.content.append(entry)

        print(f'ATENÇÃO: Se você está lendo isso, o método {name}.add(entry) não foi sobrescrito. Isto não é um erro, '
              f'mas os valores das entradas de {name} não serão atualizados automaticamente. Você deve atualiza-los '
              f'explicitamente até esta funcionalidade ser adicionada em uma atualização futura.')

    def __str__(self):
        """Visualizar conteúdo, tolerando valores ausentes."""
        return 'Conteúdo do CNAB:\n' + self.make(strict=False) + '\nPara gerar o CNAB usável, use o método make() .'
