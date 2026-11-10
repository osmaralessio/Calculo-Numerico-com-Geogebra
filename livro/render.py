"""Desenha um capítulo (conteudo/<capitulo>.json) com Streamlit."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import streamlit as st
from PIL import Image

from .geogebra import bloco_aplicativos

RAIZ = Path(__file__).resolve().parents[1]
CONTEUDO = RAIZ / "conteudo"
FIGURAS = RAIZ / "static" / "figuras"

ESTILOS = {
    # estilo: (cor do título, ícone)
    "atividade": ("orange", ":material/touch_app:"),
    "leitura": ("green", ":material/menu_book:"),
    "exemplo": ("blue", ":material/edit_note:"),
    "observacao": ("green", ":material/lightbulb:"),
    "definicao": ("gray", ":material/bookmark:"),
    "teorema": ("blue", ":material/verified:"),
    "proposicao": ("blue", ":material/verified:"),
    "corolario": ("blue", ":material/verified:"),
    "algoritmo": ("blue", ":material/account_tree:"),
    "como_usar": ("gray", ":material/info:"),
    "proof": ("gray", ""),
}


@lru_cache(maxsize=32)
def _ler_json(caminho: Path, _mtime: float):
    return json.loads(caminho.read_text(encoding="utf-8"))


def _json(nome: str):
    caminho = CONTEUDO / f"{nome}.json"
    return _ler_json(caminho, caminho.stat().st_mtime)  # relê se o conversor gerar o arquivo de novo


def carregar(capitulo: str) -> dict:
    return _json(capitulo)


def indice() -> list[dict]:
    return _json("indice")


def ancora(numero: str) -> str:
    return "sec-" + numero.replace(".", "-")


def _markdown(texto: str) -> None:
    """Markdown com cabeçalhos numerados viram st.header/st.subheader com âncora estável;
    a seção 'Respostas' fica dentro de um expansor."""
    partes = re.split(r"^(#{2,3} .+)$", texto, flags=re.M)
    alvo = st.container()
    for parte in partes:
        if not parte.strip():
            continue
        m = re.match(r"^(#{2,3}) (.+)$", parte)
        if m:
            nivel, titulo = m.groups()
            num = re.match(r"(\d+(?:\.\d+)+) ", titulo)
            if titulo.strip() == "Respostas":
                alvo = st.expander("Respostas dos exercícios (clique para ver)", icon=":material/task_alt:")
                continue
            alvo = st.container()
            with alvo:
                if nivel == "##":
                    st.header(titulo, anchor=ancora(num.group(1)) if num else None, divider="gray")
                else:
                    st.subheader(titulo, anchor=ancora(num.group(1)) if num else None)
        else:
            with alvo:
                st.markdown(parte)
    # o expansor de respostas continua aberto para os blocos seguintes do mesmo trecho
    return None


def _blocos(blocos: list, chave: str) -> None:
    for i, b in enumerate(blocos):
        k = f"{chave}-{i}"
        if b["tipo"] == "md":
            _markdown(b["texto"])
        elif b["tipo"] == "figura":
            with st.container(key=f"fig-{k}"):
                caminho = FIGURAS / b["arquivo"]
                with Image.open(caminho) as im:
                    largura = int(im.width * 0.55)  # figuras geradas a 220 dpi: ~tamanho do PDF na tela
                st.image(str(caminho), width=largura)
                if b.get("legenda"):
                    st.caption(b["legenda"])
        elif b["tipo"] == "caixa":
            estilo = b["estilo"]
            cor, icone = ESTILOS.get(estilo, ("gray", ""))
            with st.container(border=True, key=f"cx-{estilo}-{k}"):
                if b["titulo"]:
                    if estilo == "proof":
                        st.markdown(f"*{b['titulo']}.*")
                    else:
                        st.markdown(f"{icone} **:{cor}[{b['titulo']}]**")
                _blocos(b["filhos"], k)
                if estilo == "proof":
                    st.markdown("<div style='text-align:right'>■</div>", unsafe_allow_html=True)
                if estilo == "atividade":
                    bloco_aplicativos(b["aplicativos"], k)
                if estilo == "leitura" and b["arquivo"]:
                    pdf = RAIZ / "static" / "complementos" / b["arquivo"]
                    c1, c2 = st.columns([1, 2.5], vertical_alignment="center")
                    c1.download_button("Baixar o PDF", pdf.read_bytes(), file_name=b["arquivo"], mime="application/pdf", key=f"pdf-{k}", icon=":material/download:")
                    c2.markdown(f"[Abrir o texto em nova aba](./app/static/complementos/{b['arquivo']})")


def capitulo(nome: str) -> None:
    dados = carregar(nome)
    st.caption(f"Capítulo {dados['numero']}")
    st.title(dados["titulo"], anchor="topo")
    with st.sidebar:
        st.markdown(f"**Seções do Capítulo {dados['numero']}**")
        st.markdown("\n".join(f"- [{n} {t}](#{ancora(n)})" for n, t in dados["secoes"]))
    _blocos(dados["blocos"], nome)
    st.divider()
    _navegacao(dados["numero"])


def _navegacao(numero: int) -> None:
    caps = indice()
    c1, _, c2 = st.columns([1, 1, 1])
    if numero > 1:
        ant = caps[numero - 2]
        c1.page_link(f"paginas/cap{ant['numero']}.py", label=f"← Capítulo {ant['numero']}", icon=":material/arrow_back:")
    if numero < len(caps):
        prox = caps[numero]
        c2.page_link(f"paginas/cap{prox['numero']}.py", label=f"Capítulo {prox['numero']} →", icon=":material/arrow_forward:")
