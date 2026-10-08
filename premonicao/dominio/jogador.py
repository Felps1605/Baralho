from __future__ import annotations

import time

from dominio.baralho import Deck


class Jogador:
    def __init__(self, id: int, nome: str = "Jogador"):


        self.nome: str = (f"Jogador {id}"if nome == "Jogador" else nome)
        self.id : int = id

        
        self.admin: bool = False
        self.pontos: int = 0
        
        self.ultima_atividade_turno: float | None = None
        self.ultimo_momento_online = time.monotonic()

        self.mao = Deck("Mão")
        self.mao.cartas = [] 
        
        