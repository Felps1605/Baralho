from baralho import deck, valores_padrao
import sys

player_id: int = 1


def numero_de_rodadas_valido(n : int,max : int )-> bool:
    if(n <= 0):
        print("Insira um numero inteiro maior que zero")
        return False
    if(n > max):
        print("Há jogadores demais para essa quantidade de rodadas, o máximo é ", max)
        return False
    
    return True

def numero_de_jogadores_valido(n : int)-> bool:
    if(n <= 0):
        print("Insira um numero inteiro maior que zero")
        return False
    if(n > 52):
        print("Há jogadores demais")
        return False
    
    return True

def maior_carta(monte: deck, naipe_trunfo: str)-> int: #retorna o índice da maior carta, que coincide com o índice do jogador que a jogou
    minimo_inteiro = -sys.maxsize - 1
    maior = minimo_inteiro
    indice: int | None = None
    for i, card in enumerate(monte.cartas):
            valor = card.valor
            if card.naipe == naipe_trunfo:
                valor += 1000
            if valor > maior:
                maior = valor
                indice = i
    
    monte.cartas[indice].exibir("Maior carta")
    return indice

class jogador:
    def __init__(self, nome: str = "Jogador"):

        global player_id

        self.nome: str = (f"Jogador {player_id}"if nome == "Jogador" else nome)
        self.id : int = player_id
        self.admin: bool = False
        self.pontos: int = 0
        self.mao = deck("Mão")
        self.mao.cartas = [] 
        self.palpite: int | None = None
        self.jogadas_ganhas = 0
        player_id += 1


    def exibir(self: jogador, rotulo: str | None = None):
        print("\n")
        if rotulo:
            print(f"{rotulo}:")
        print("Nome: ", self.nome)
        print("Id: ", self.id)
        print("Pontos: ", self.pontos)
        print("\n")


def main():
    valores_especificos = valores_padrao.copy()
    valores_especificos["A"] = 14


    jogadores: list[jogador] = []
    while(True):
        numero_de_jogadores = int(input("Insira o numero de jogadores: "))
        if numero_de_jogadores_valido(numero_de_jogadores):
            break

    for i in range(numero_de_jogadores):
        p = jogador()
        jogadores.append(p)



    bolo = deck("Bolo")
    bolo.construir_deck(valores = valores_especificos)
    bolo.embaralhar()


    max = len(bolo.cartas) // len(jogadores)
    while(1):
        numero_de_rodadas = int(input("insira o numero de rodadas que deseja jogar: "))
        if numero_de_rodadas_valido(numero_de_rodadas, max):
            break


    for rodada in range(numero_de_rodadas):

        print(f"\nRODADA {rodada + 1}\n")
    
        bolo.construir_deck(valores = valores_especificos)
        bolo.embaralhar()

        numero_de_cartas = rodada + 1
        print("Numero de cartas:", numero_de_cartas)

        carta_da_rodada = bolo.cartas.pop()

        soma_palpites: int = 0

        for j in jogadores: 

            carta_da_rodada.exibir("Carta/naipe da rodada")

            j.exibir()
            j.palpite = None
            j.jogadas_ganhas = 0
            j.mao.cartas = [] # redundancia
            j.mao.comprar(bolo, numero_de_cartas)
            j.mao.exibir()

              
            while(True):
                palpite = int(input("insira o palpite de quantas jogadas vai ganhar: "))
                if(palpite > numero_de_cartas or palpite < 0 ):
                    print("Insira um valor possível")
                    continue
                if(j == jogadores[-1]):
                    if(palpite + soma_palpites == numero_de_cartas):
                        print("A soma dos palpites não pode igualar a quantidade de cartas da rodada.")
                        print("Você não pode dar o palpite ", palpite)
                        continue
                break
            
            j.palpite = palpite
            soma_palpites += palpite

        print("\nPalpites: \n")

        
        for j in jogadores:
            print(f"{j.nome} : {j.palpite}")
        
            
        print("\n       Hora de jogar \n")


        for i in range(numero_de_cartas):

            monte = deck("Monte")
        
            for j in jogadores:
                print(f"Turno de {j.nome}: ")
                carta_da_rodada.exibir("Carta/Naipe da rodada")
                monte.exibir()
                j.mao.exibir(indices = True)

                while(True):
                    indice = int(input("Insira o indice da carta que deseja jogar: "))
                    if(indice >= len(j.mao.cartas) or indice < 0):
                        print("Insira um índice válido")
                        continue
                    break

                j.mao.jogar(monte, indice)

            monte.exibir()

            p = jogadores[maior_carta(monte, carta_da_rodada.naipe)]

            p.jogadas_ganhas += 1
            p.exibir("Vencedor da jogada")
            print(f"Jogadas ganhas até agora: {p.jogadas_ganhas}, palpite: {p.palpite}")

        for j in jogadores:
            print(f"{j.nome} disse que ia ganhar {j.palpite} jogadas e ganhou {j.jogadas_ganhas}")
            if j.jogadas_ganhas == j.palpite:
                j.pontos += j.palpite + 1
                print(f"{j.nome} acertou o palpite e ganha {j.palpite + 1} pontos")
            else:
                print(f"{j.nome} errou o palpite e não ganha pontos")
            j.exibir()





    print("\n       FIM DO JOGO\n")
    print("PONTUAÇÕES:\n")
    maior_pontuacao = -1000
    for j in jogadores:
        j.exibir()
        

    main()

    
    
    


