import random

valores_padrao = {
    "A": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 11,
    "Q": 12,
    "K": 13
}

naipes = [
    "copas",
    "espadas",
    "ouros",
    "paus"
]


class carta:
    
    def __init__(self, valor_char, valor , naipe: str):
        self.valor_char: str = valor_char
        self.valor : int=  valor
        self.naipe : str= naipe

    def exibir(self, rotulo: str | None = None):
        
        print(f"{rotulo}: {self.valor_char} {self.naipe}" if rotulo else f"{self.valor_char} {self.naipe}")



class deck:
    def __init__(self, rotulo: str = "Deck"):

        self.cartas : list[carta] = []
        self.rotulo : str = rotulo

    
    def construir_deck(self: deck,  naipes: list[str] | None = naipes, valores: dict[str,int] | None = valores_padrao, ):
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
        

