import random
import sys
from config import *


class carta:
    
    def __init__(self, valor_char: str, valor: int , naipe: str):
        self.valor_char: str = valor_char
        self.valor : int=  valor
        self.naipe : str= naipe

    def exibir(self, rotulo: str | None = None):
        
        print(f"{rotulo}: {self.valor_char} {self.naipe}" if rotulo else f"{self.valor_char} {self.naipe}")



class deck:
    def __init__(self, rotulo: str = "Deck"):

        self.cartas : list[carta] = []
        self.rotulo : str = rotulo

    
    def construir_deck(self: deck,  naipes: list[str] = NAIPES, valores: dict[str,int] = VALORES_PADRAO, ):
        self.cartas = []
        
        for naipe in naipes:
            for valor in valores:
                card = carta(valor, valores[valor], naipe)
                self.cartas.append(card)

    def exibir(self: deck, indices: bool = False):
        print("\n")
        print(f"{self.rotulo}:")
        if self.cartas == []:
            print("Nenhuma carta\n")
            return
        
        if indices:
            for indice, card in enumerate(self.cartas):
                card.exibir(str(indice))
            
        else:
            for card in self.cartas:
                card.exibir()

        print("\n")

    def embaralhar(self: deck):
        random.shuffle(self.cartas)
        random.shuffle(self.cartas)

    def comprar(self: deck, bolo: deck, quantidade: int = 1):
        for i in range(quantidade):
            self.cartas.append(bolo.cartas.pop())

    def jogar(self: deck, alvo: deck, indice: int):
        alvo.cartas.append(self.cartas.pop(indice))

    def juntar(self: deck, bolos: list[deck]):
        for bolo in bolos:
            self.cartas.extend(bolo.cartas)
            bolo.cartas = []

    def maior_carta(self: deck, naipe_trunfo: str | None = None)-> int: #devolve o indice da maior carta

        minimo_inteiro = -sys.maxsize - 1
        maior_valor = minimo_inteiro
        indice: int      
        for i, card in enumerate(self.cartas):
            valor = card.valor
            if card.naipe == naipe_trunfo:
                valor += BONUS_TRUNFO
            if valor > maior_valor:
                maior_valor = valor
                indice = i
                
        return indice 
        

