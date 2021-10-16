"""Br Banking CNAB - Package for generating Brazilian CNAB banking files as specified by FEBRABAN.

At the current development, only implements a few templates blocks for Itaú bank.
"""

__version__ = '0.2.0-dev.2'
__author__ = 'Lucas Carvalho Flores'

import enum
import json
import os
from collections import OrderedDict

CWD = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(CWD, 'templates')


class BlockType(enum.Enum):
    Arquivo = 'arquivo'
    Lote = 'lote'
    Regsitro = 'registro'


class CNABError(Exception):
    """Exceção base dos erros de CNAB."""

    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)


class CNABInvalidValueError(CNABError):
    """Exceção lançada quando um valor inválido para certo campo é alcançado."""

    def __init__(self, field, value, message='\n\tValor do campo \'{0}\' não pode ser \'{1}\'. '
                                             'Verifique se há algum default pra usar ou defina um valor adequado.'):
        super().__init__(message.format(field, value))


class CNABInvalidOperationError(CNABError):
    """Exceção lançada quando uma operação não suportada por certa classe é chamada."""

    def __init__(self, class_name, method_name, extra='', message='\n\tA classe {0} não suporta o método {1}. {2}'):
        super().__init__(message.format(class_name, method_name, extra))


class CNABInvalidTemplateError(CNABError):
    """Exceção lançada quando um nome inválido de template é usado na criação de um BlocoCNAB."""

    def __init__(self, template_type, class_name, valid_templates):
        msg = f'\n\tO template \'{template_type}\' é inválido para \'{class_name}\'. Valores válidos são'
        for value in valid_templates:
            msg += f' {value},'
        super().__init__(msg.rstrip(',') + ' .')


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
                val += ' ' * (size - len(val))
        elif len(val) > size:
            val = val[0:size]

        data_str += val

    return data_str + '\n'


class BlocoCNAB:
    """Representa abstração de um bloco de dados de um arquivo CNAB, seja ele um Caabeçalho+Rodapé ou Registro.

    A rotina de criação de uma String CNAB é direta: cria-se o bloco e se adiciona os dados em
    header['nome_campo']['val'], trailer['nome_campo']['val'] e, exclusivamente para Registros por não terem
    cabeçalho ou rodapé, content['nome_campo']['val'] tem seus dados. Blocos e Lotes guardam uma lista com seus
    filhos content.

    A rotina de leitura de uma string CNAB é menos direta, e a string deve ser passada para um objeto tipo BlocoCNABxxx
    para que esse interprete a string recebida e salve o resultado em si mesma, tendo criado tantos filhos
    quanto necesário.

    Rotina de Leitura:

    BlocoCNAB.read_str(self, data_str, enclosed=True, block_type):  block_type é o template a ser usado.
        if enclosed: self.parse_header()  analisa cabeçalho, se houver
        content_str = ...  rotina que separa conteúdo interno do cabeçalho e rodapé
        self.parse_content_str(data_str, enclosed, block_type)  vai chamar o read_str no que falta
        if enclosed: self.parse_trailer(data_str)
        return self

    """

    header = None
    content = None
    trailer = None
    enclosed = None
    block_type = None
    template = 'Desconhecido'

    def __init__(self, template, enclosed):
        self.enclosed = enclosed
        self.template = template.value

        # Se não for do tipo [header ... trailer], não se edita o nome do arquivo de template
        # a ser carregado pois só há um.
        if not enclosed:
            with open(template.value, 'r') as file:
                self.content = json.load(file, object_pairs_hook=OrderedDict)

        # Blocos do tipo [header ... trailer] ajustam o nome do arquivo de template
        # pra carregar as duas partes, header e trailer.
        else:
            # Carrega template do header do bloco.
            with open(template.value.format('header'), 'r') as file:
                self.header = json.load(file, object_pairs_hook=OrderedDict)

            # Carrega template do trailer do bloco.
            with open(template.value.format('trailer'), 'r') as file:
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
