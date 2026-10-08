class ErroDeDominio(Exception):
    """base para todos os erros de regra do jogo"""
    
class SalaCheia(ErroDeDominio):
    """A sala já atingiu o número máximo de jogadores"""

class SessaoInvalida(ErroDeDominio):
    """O token de sessão não existe ou já foi removido"""