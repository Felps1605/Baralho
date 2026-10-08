from dominio.baralho import Deck
from dominio.jogador import Jogador
from dominio.turno import Turno

class Jogada:
    turno_jogada: Turno # setado na função nova_jogada da rodada
    def __init__(self, turno_jogada: Turno):
        self.turno_jogada: Turno = turno_jogada
        self.monte: Deck = Deck() 
        self.vencedor: Jogador | None = None
  