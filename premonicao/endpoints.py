
import uvicorn
from fastapi import FastAPI, Response, Cookie, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import time
import asyncio
import secrets
from contextlib import asynccontextmanager
from __future__ import annotations
import os 

from classes import partida, rodada, jogada, turno, jogador, status_partida, status_rodada, LIMITE_TURNO, LIMITE_OFFLINE




async def vigiar_inativos():
    while True:
        await asyncio.sleep(5)
        for codigo, jogo in list(jogos.items()):

            try:
                jogo.expulsar_inativos(LIMITE_TURNO, LIMITE_OFFLINE)
            except Exception as e:
                print("Erro ao expulsar inativos:", repr(e))

            if time.monotonic() - jogo.ultima_atividade > 1800:
                del jogos[codigo]

@asynccontextmanager
async def lifespan(app):
    tarefa = asyncio.create_task(vigiar_inativos())
    yield
    tarefa.cancel()


app = FastAPI(lifespan = lifespan)

#jogo = partida()

jogos: dict[str, partida]= {}

ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
def novo_codigo() -> str:
    while True:
        c = "".join(secrets.choice(ALFABETO) for _ in range(5))
        if c not in jogos:
            return c

def sala_atual(codigo: str)-> partida:
    jogo = jogos.get(codigo.upper())
    if jogo is None:
        raise HTTPException(404, "Sala não encontrada")
    jogo.ultima_atividade = time.monotonic()
    return jogo

def usuario_atual(jogo: partida = Depends(sala_atual),
                  sessao: str | None = Cookie(default = None)) -> jogador:
    
    if sessao in jogo.removidos:
        raise HTTPException(status_code = 401, detail = jogo.removidos[sessao]) # ex: "Você foi expulso por ana"
    if sessao is None or sessao not in jogo.sessoes:
        raise HTTPException(status_code = 401, detail = "Sem sessão válida")
    j = jogo.sessoes[sessao]
    j.ultimo_momento_online = time.monotonic()
    return j 


@app.get("/")
def pagina():
    return FileResponse(Path(__file__).parent / "index.html")



@app.get("/sala/{codigo}/eu")
def quem_sou_eu(usuario: jogador = Depends(usuario_atual)):
    return {"nome": usuario.nome, "id": usuario.id, "admin": usuario.admin}

@app.post("/sala")
def criar_sala(nome: str, response: Response):
    if(len(jogos) >= 20):
        raise HTTPException(503, "servidor cheio, tente denovo mais tarde")
    if(len(nome) > 20 or len(nome) < 1):
        raise HTTPException(422, "O nome deve ter entre 1 e 20 caracteres")
    codigo = novo_codigo()
    jogos[codigo] = partida()
    resultado = jogos[codigo].entrar(nome, response, None)
    return {"codigo": codigo, "resultado": resultado}


@app.post("/sala/{codigo}/entrar")
def entrar( nome: str, response: Response, jogo: partida = Depends(sala_atual), sessao: str | None = Cookie(default = None)):
    if(len(nome) > 20 or len(nome) < 1):
        raise HTTPException(422, "O nome deve ter entre 1 e 20 caracteres")
    return jogo.entrar(nome, response, sessao)

@app.get("/sala/{codigo}/rodada/mao")
def ver_mao(jogo: partida = Depends(sala_atual), usuario: jogador = Depends(usuario_atual)):
    return usuario.mao


@app.get("/sala/{codigo}/rodada/palpites")
def ver_palpites(jogo: partida = Depends(sala_atual)):
    return jogo.rodada_atual.ver_palpites() if jogo.rodada_atual else {}
    
@app.get("/sala/{codigo}/rodada/carta")
def ver_carta_da_rodada(jogo: partida = Depends(sala_atual)):
    return jogo.rodada_atual.carta_da_rodada if jogo.rodada_atual else None

@app.get("/sala/{codigo}/jogadores/")
async def ver_lista_de_jogadores(jogo: partida = Depends(sala_atual)):
    return [{"nome": j.nome, "id": j.id, "pontos": j.pontos} for j in jogo.sessoes.values()]

@app.get("/sala/{codigo}/estado")
def consultar_estado_da_partida(jogo: partida = Depends(sala_atual)):
   return jogo.status_completo()

@app.post("/sala/{codigo}/iniciar")
async def iniciar_partida( n_rodadas: int = 10, jogo: partida = Depends(sala_atual), usuario: jogador = Depends(usuario_atual)):
    return jogo.iniciar( n_rodadas, usuario )

@app.post("/sala/{codigo}/rodada/palpite")
def fazer_palpite(palpite: int, jogo: partida = Depends(sala_atual), usuario: jogador = Depends(usuario_atual)):
    #provavelmente deveria limpar isso
    return jogo.rodada_atual.fazer_palpite(palpite, usuario) if jogo.status == status_partida.RODADAS else {"mensagem": "Só é possível fazer palpites durante a fase de rodadas"}
    
@app.post("/sala/{codigo}/rodada/jogar")
def fazer_jogada(indice: int, jogo: partida = Depends(sala_atual), usuario: jogador = Depends(usuario_atual)):
    return jogo.fazer_jogada(indice, usuario) 

@app.post("/sala/{codigo}/rodada/presente")
def presente(presente: bool = False, jogo: partida = Depends(sala_atual), usuario: jogador = Depends(usuario_atual)):
    if presente and jogo.jogador_da_vez() is usuario:
        usuario.ultima_atividade_turno = time.monotonic()
    return presente
    
@app.get("/sala/{codigo}/mesa")
def ver_mesa(jogo: partida = Depends(sala_atual)):
    return jogo.ver_mesa()
   
@app.post("/sala/{codigo}/encerrar")
def encerrar_partida(jogo: partida = Depends(sala_atual), usuario: jogador = Depends(usuario_atual)):
    return jogo.encerrar(usuario)

@app.post("/sala/{codigo}/nova")
def nova_partida(jogo: partida = Depends(sala_atual), usuario: jogador = Depends(usuario_atual)):
    return jogo.nova_partida(usuario)
    
@app.post("/sala/{codigo}/sair")
def sair_da_partida(response: Response, jogo: partida = Depends(sala_atual), sessao: str | None = Cookie(default = None)):
    return jogo.sair_da_partida(response, sessao)

@app.post("/sala/{codigo}/expulsar")
def expulsar_jogador(id: int, jogo: partida = Depends(sala_atual), usuario: jogador = Depends(usuario_atual)):
    return jogo.expulsar_jogador(usuario, id)

@app.get("/sala/{codigo}/eventos")
def ver_eventos(desde: int | None = None, jogo: partida = Depends(sala_atual)):
    return jogo.eventos_desde(desde)
    
    

if __name__ == "__main__":
    uvicorn.run("endpoints:app", host= "0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload = False)