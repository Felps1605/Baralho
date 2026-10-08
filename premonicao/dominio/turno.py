from __future__ import annotations
from dominio.jogador import Jogador
import time


class Turno:
    #disposição dos jogadores na mesa
    def __init__(self, ordem: list[Jogador]):
        self.ordem = ordem
        self.posicao = 0
        self.atual.ultima_atividade_turno = time.monotonic()

    @property
    def atual(self) -> Jogador:
        jogador_atual = self.ordem[self.posicao]
        
        return jogador_atual

    @property
    def eh_o_ultimo(self) -> bool:
        return self.posicao == len(self.ordem) - 1

    def avancar(self):
        if self.posicao != len(self.ordem) - 1:
            self.posicao += 1
            self.atual.ultima_atividade_turno = time.monotonic()


def ordem_a_partir_de(mesa: list[Jogador], inicio: int)-> list[Jogador]:
    inicio %= len(mesa)
    return mesa[inicio:] + mesa[:inicio]
    