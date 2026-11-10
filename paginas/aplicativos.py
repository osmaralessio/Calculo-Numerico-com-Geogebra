import json
from pathlib import Path

import streamlit as st

from livro.geogebra import applet, baixar, nome_app

RAIZ = Path(__file__).resolve().parents[1]

st.title("Todos os aplicativos do GeoGebra")
st.caption("Escolha um aplicativo para abri-lo em tamanho grande. Eles também aparecem dentro dos capítulos, junto do texto.")


def aplicativos_por_capitulo() -> dict[str, list[str]]:
    grupos: dict[str, list[str]] = {}
    for cap in json.loads((RAIZ / "conteudo" / "indice.json").read_text(encoding="utf-8")):
        dados = json.loads((RAIZ / "conteudo" / f"{cap['id']}.json").read_text(encoding="utf-8"))
        lista: list[str] = []

        def andar(blocos):
            for b in blocos:
                if b.get("estilo") == "atividade":
                    for a in b["aplicativos"]:
                        if a not in lista:
                            lista.append(a)
                andar(b.get("filhos", []))

        andar(dados["blocos"])
        grupos[f"Capítulo {cap['numero']}. {cap['titulo']}"] = lista
    return grupos


grupos = aplicativos_por_capitulo()
todos = [(g, a) for g, lista in grupos.items() for a in lista]
pedido = st.query_params.get("app")
inicial = next((i for i, (_, a) in enumerate(todos) if a == pedido), 0)

c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
escolha = c1.selectbox(
    "Aplicativo",
    range(len(todos)),
    index=inicial,
    format_func=lambda i: f"{todos[i][0].split('.')[0]} — {nome_app(todos[i][1])}",
)
grupo, arquivo = todos[escolha]
st.query_params["app"] = arquivo
with c2:
    baixar(arquivo, "pagina-apps")

st.markdown(f"**{nome_app(arquivo)}** · {grupo} · `{arquivo}`")
applet(arquivo, largura_coluna=1120)
