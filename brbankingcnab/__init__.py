"""Br Banking CNAB - Package for generating Brazilian CNAB banking files as specified by FEBRABAN.

At the current development, only implements a few templates blocks for Itaú bank.
"""

__version__ = '0.3.0-dev.2'
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


def parse_cnab_string(cnab_str, cnab_layout_code, file_template):
    lines_raw = cnab_str.split('\n')
    lines = []

    for line_r in lines_raw:
        line = line_r.replace('\r', '').strip('\n')
        if len(line) > 0:
            lines.append(line)

    # Layout de CNAB 240
    if cnab_layout_code == 240:
        from brbankingcnab.cnab240 import ArquivoCNAB240
        cnab_file = ArquivoCNAB240(file_template)
    else:
        raise CNABError(message='Apenas o layout de arquivo 240 está implementado no momento.')

    cnab_file.fill_cnab_file(lines)

    return cnab_file


def eval_rule(record: str, rule: dict) -> bool:
    """Verifica se string recebida em record obedece à regra descrita.

    Formato de uma regra:
    {'start': int, 'end': int, 'operation': str, 'value': ... }

    Os valores de start e end devem dar os índices de começo e término da substring que contém o valor a ser testado
    contra value através a operação definida em operation.

    O conteúdo de value dependerá da operação escolhida:

    equals    :  testa valor exato da substring, value deve ser string
    in        :  testa valor contra lista de opções válidas, value deve ser lista de strings
    type-num  :  verifica se string descreve um  número, value é ignorado
    type-alfa :  verifica se string descreve letras, value é ignorado

    Returna True caso obedeça ou False caso contrário.
    """

    start = rule['start']
    end = rule['end']
    value = record[start:end]

    if rule['operation'] == 'equals':
        if value == rule['value']:
            return True
        return False

    elif rule['operation'] == 'in':
        if value in rule['value']:
            return True
        return False

    elif rule['operation'] == 'type-num':
        if value.isnumeric():
            return True
        return False

    elif rule['operation'] == 'type-alfa':
        if not value.isnumeric():
            return True
        return False

    else:
        raise CNABError(message=f"Regra de variante de registro inválida: {rule}")


def eval_ruleset(record: str, ruleset: list):
    """Testa string recebida em record contra todas as regras de uma lista recebida em ruleset.
    Retorna True se todas as regras sejam respeitadas ou False caso ao menos uma seja violada.
    Note que segmentos únicos tem uma lista vazia de regras, então esta função retornará True imediatamente.
    """

    for rule in ruleset:
        if not eval_rule(record, rule):
            return False
    return True


class BlocoCNAB:
    """Declaração apenas, para melhor implementação da interface.
    Equivalente a declarar as coisas em C++ para implementar depois, deixando disponível o nome da classe ou função
    para o compilador (ou interpretador nesse caso) fazer as conexões necessárias.
    """
    pass


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
            with open(template.value['path'], 'r') as file:
                self.content = json.load(file, object_pairs_hook=OrderedDict)

        # Blocos do tipo [header ... trailer] ajustam o nome do arquivo de template
        # pra carregar as duas partes, header e trailer.
        else:
            # Carrega template do header do bloco.
            with open(template.value['path'].format('header'), 'r') as file:
                self.header = json.load(file, object_pairs_hook=OrderedDict)

            # Carrega template do trailer do bloco.
            with open(template.value['path'].format('trailer'), 'r') as file:
                self.trailer = json.load(file, object_pairs_hook=OrderedDict)

            # Prepara lista para receber os filhos.
            self.content = []

    def __str__(self):
        """Visualizar conteúdo, tolerando valores ausentes."""
        return 'Conteúdo do CNAB:\n' + self.make(strict=False) + '\nPara gerar o CNAB usável, use o método make() .'

    def fill_cnab_file(self, lines: list):
        """Recebe lista de linhas contendo strings de um arquivo CNAB completo e recosntroi CNAB."""

        if not self.block_type == BlockType.Arquivo:
            raise CNABError(message="BlocoCNAB.fill_canb_file() só pode ser chamado a partir de um ArquivoCNAB***.")

        if len(lines) < 5:
            raise CNABError(message="CNAB com menos de cinco linhas não possui registros e está vazio.")

        self.parse_header_str(lines[0])
        self.parse_content_list(lines[1:-1])
        self.parse_trailer_str(lines[-1])

    def parse_content_list(self, content: list):
        """Recebe lista de strings contento os lotes e seus registros de detalhes de um arquivo CNAB em construção.
        Encontra todos os lotes e seus registros e chama seus métodos de cosntrução e interpretação."""

        while len(content) > 0:
            line = content.pop(0)
            if self.is_batch_header(line):
                # Cria novo arquivo de lote e interpreta cabeçalho
                batch = self.new_batch_from_header(line)
                line = content.pop(0)
                while self.is_record(line):
                    # Cria registro de operação e interpreta conteúdo, adicionando ao lote.
                    batch.add(self.new_record_from_str(batch, line))
                    line = content.pop(0)
                # Ao chegarmos aqui, é obrigatório que line seja trailer de lote.
                if not self.is_batch_trailer(line):
                    raise CNABError(message="CNAB inválido.")
                # Interpreta a linha de trailer de lote. Retorna bool indicando se tudo está correto e válido.
                batch.parse_trailer_str(line)
                self.add(batch)
            else:
                # Só se chega aqui com linhas de trailer de lote.
                raise CNABError(message="CNAB inválido.")

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

        # Windows ANSI shitness
        data_str = data_str.replace('\n', '\r\n')

        # String final.
        return data_str

    def add(self, entry: object):
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

    def parse_header_str(self, header: str):
        """Interpreta string de header de arquivo/lote e retorna dict preenchido."""
        for item in self.header:
            start = self.header[item]['index']
            end = self.header[item]['index'] + self.header[item]['size']
            value = header[start:end]
            if self.header[item]['type'] == "alfanum":
                self.header[item]['val'] = value
            else:
                self.header[item]['val'] = int(value)

    def parse_record_str(self, record: str) -> BlocoCNAB:
        """Interpreta string de registro de detalhe e retorna dict preenchido."""

        if self.enclosed:
            me = self.__class__.__name__
            raise CNABError(message=f"{me}.parse_record_str() é inválido.")

        for item in self.content:
            start = self.content[item]['index']
            end = self.content[item]['index'] + self.content[item]['size']
            value = record[start:end]
            if self.content[item]['type'] == "alfanum":
                self.content[item]['val'] = value
            else:
                self.content[item]['val'] = int(value)

        return self

    def parse_trailer_str(self, trailer: str):
        """Interpreta string trailer de arquivo/lote e retorna dict preenchido."""
        for item in self.trailer:
            start = self.trailer[item]['index']
            end = self.trailer[item]['index'] + self.trailer[item]['size']
            value = trailer[start:end]
            if self.trailer[item]['type'] == "alfanum":
                self.trailer[item]['val'] = value
            else:
                self.trailer[item]['val'] = int(value)

    def is_batch_header(self, line: str) -> bool:
        """Analisa string e verifica se trata-se de um header de lote."""
        pass

    def is_batch_trailer(self, line: str) -> bool:
        """Analisa string e verifica se trata-se de um trailer de lote."""
        pass

    def is_record(self, line: str) -> bool:
        """Analisa string e verifica se trata-se de um registro de detalhes."""
        pass

    def new_batch_from_header(self, line: str) -> BlocoCNAB:
        pass

    def new_record_from_str(self, batch: BlocoCNAB, line: str) -> BlocoCNAB:
        pass
