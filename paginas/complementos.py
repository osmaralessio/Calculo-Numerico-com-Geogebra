from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "static" / "complementos"

TEXTOS = [
    ("Capítulo 1", "IEEE754_Nepomuceno_2016.pdf", "Padrão IEEE 754 (Nepomuceno, 2016)"),
    ("Capítulo 1", "IEEE754_Nepomuceno_2018.pdf", "Padrão IEEE 754 (Nepomuceno, 2018)"),
    ("Capítulo 1", "8-Bit_Floating_Point.pdf", "Ponto flutuante de 8 bits"),
    ("Capítulo 2", "material_lacos_fluxograma.pdf", "Laços de repetição e fluxogramas"),
    ("Capítulo 3", "CustoComputacional_SistemasLineares.pdf", "Custo computacional na resolução de sistemas lineares"),
    ("Capítulo 3", "ComparacaoMetodosDiretos.pdf", "Comparação computacional dos métodos diretos"),
]

st.title("Textos complementares")
st.caption("Textos de apoio citados nos quadros verdes de Leitura complementar.")

for cap, arq, titulo in TEXTOS:
    if not (PASTA / arq).exists():
        continue
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1.1, 1.2], vertical_alignment="center")
        c1.markdown(f"**{titulo}**  \n{cap} · `{arq}`")
        c2.download_button("Baixar", (PASTA / arq).read_bytes(), file_name=arq, mime="application/pdf", key=arq, icon=":material/download:")
        c3.markdown(f"[Abrir em nova aba](./app/static/complementos/{arq})")
