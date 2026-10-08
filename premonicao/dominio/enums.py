from enum import Enum

class StatusRodada(Enum):
    PALPITES = 1
    JOGADAS = 2
    FINAL = 3

class StatusPartida(Enum):
    INICIO = 1
    RODADAS = 2
    FINAL = 3