import secrets
import uvicorn
from fastapi import FastAPI, Response, Cookie, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from enum import Enum


from classes import partida, rodada, jogada, turno, jogador, status_partida, status_rodada


app = FastAPI()

jogo = partida()


def usuario_atual(sessao: str | None = Cookie(default = None)) -> jogador:
    if sessao is None or sessao not in jogo.sessoes:
        raise HTTPException(status_code = 401, detail = "Sem sessão válida")
    return jogo.sessoes[sessao] #devolve o jogador que possui a chave sessao



@app.get("/")
def pagina():
    return FileResponse(Path(__file__).parent / "index.html")



@app.get("/eu")
def quem_sou_eu(usuario: jogador = Depends(usuario_atual)):
    return {"nome": usuario.nome, "id": usuario.id, "admin": usuario.admin}



@app.post("/partida/entrar")
def entrar(nome: str, response: Response, sessao: str | None = Cookie(default = None)):
    return jogo.entrar(nome, response, sessao)

@app.get("/partida/rodada/mao")
def ver_mao(usuario: jogador = Depends(usuario_atual)):
    return usuario.mao


@app.get("/partida/rodada/palpites")
def ver_palpites():
    return jogo.rodada_atual.ver_palpites() if jogo.rodada_atual else {}
    
@app.get("/partida/rodada/carta")
def ver_carta_da_rodada():
    return jogo.rodada_atual.carta_da_rodada if jogo.rodada_atual else None

@app.get("/partida/jogadores/")
async def ver_lista_de_jogadores():
    return [{"nome": j.nome, "id": j.id, "pontos": j.pontos} for j in jogo.sessoes.values()]

@app.get("/partida/estado")
def consultar_estado_da_partida():
   return jogo.status_completo()

@app.post("/partida/iniciar")
async def iniciar_partida( n_rodadas: int = 10, usuario: jogador = Depends(usuario_atual)):
    return jogo.iniciar( n_rodadas, usuario )

@app.post("/partida/rodada/palpite")
def fazer_palpite(palpite: int, usuario: jogador = Depends(usuario_atual)):
    #provavelmente deveria limpar isso
    return jogo.rodada_atual.fazer_palpite(palpite, usuario) if jogo.status == status_partida.RODADAS else {"mensagem": "Só é possível fazer palpites durante a fase de rodadas"}
    
@app.post("/partida/rodada/jogar")
def fazer_jogada(indice: int, usuario: jogador = Depends(usuario_atual)):
    return jogo.fazer_jogada(indice, usuario) 
    
@app.get("/partida/mesa")
def ver_mesa():
    return jogo.ver_mesa()
   
@app.post("/partida/encerrar")
def encerrar_partida(usuario: jogador = Depends(usuario_atual)):
    return jogo.encerrar(usuario)

@app.post("/partida/nova")
def nova_partida(usuario: jogador = Depends(usuario_atual)):
    return jogo.nova_partida(usuario)
    
@app.post("/partida/sair")
def sair_da_partida(response: Response, sessao: str | None = Cookie(default = None)):
    return jogo.sair_da_partida(response, sessao) 
    
    

if __name__ == "__main__":
    uvicorn.run("endpoints:app", host= "0.0.0.0", port=8000, reload = True)