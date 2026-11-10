from pathlib import Path

import streamlit as st

from livro.render import indice

RAIZ = Path(__file__).resolve().parents[1]

c1, c2 = st.columns([1, 1.45], gap="large")
with c1:
    st.image(str(RAIZ / "static" / "figuras" / "capa.png"), use_container_width=True)
with c2:
    st.title("Cálculo Numérico Interativo")
    st.markdown(
        "##### Sistemas lineares, zeros de funções e interpolação com aplicativos no GeoGebra\n\n"
        "**Osmar Alessio**  \nUniversidade Federal do Triângulo Mineiro  \n"
        "Licenciatura em Matemática – ICENE  \nUberaba – MG, 2026"
    )
    st.subheader("Apresentação", anchor=False)
    st.markdown(
        """
Este livro reúne textos de Cálculo Numérico preparados para a Licenciatura em Matemática, com uma
característica central: cada método é acompanhado de um ou mais aplicativos no GeoGebra, em que o aluno
executa o método passo a passo, confere as contas e observa a construção geométrica.

**Como usar.** Os quadros laranja *Atividade no GeoGebra* trazem o aplicativo do método: clique em
**Abrir o aplicativo** e ele aparece ali mesmo, na página, pronto para usar. Também é possível abri-lo em
página inteira ou baixar o arquivo `.ggb`. Os quadros verdes *Leitura complementar* trazem textos de
apoio em PDF. As respostas dos exercícios ficam no fim de cada capítulo, num quadro que se abre com um clique.

**Organização.** O Capítulo 1 trata da mudança de base e da representação dos números em ponto flutuante
(padrão IEEE 754), com máquinas de 8, 16, 32 e 64 bits no GeoGebra, e dos erros de arredondamento e
truncamento que acompanham todos os métodos seguintes. O Capítulo 2 apresenta os métodos para zeros de
funções (bisseção, posição falsa, ponto fixo, Newton-Raphson e secante) e sua relação com os laços de
repetição. O Capítulo 3 trata dos sistemas lineares, com métodos diretos (eliminação de Gauss e
fatoração $LU$) e iterativos (Gauss-Jacobi e Gauss-Seidel). O Capítulo 4 trata da interpolação polinomial
por três caminhos (sistema linear, Lagrange e Newton), que levam ao mesmo polinômio. O Capítulo 5 trata do
ajuste de curvas pelo método dos mínimos quadrados, resolvido de forma direta (sistema normal) e iterativa
(gradiente descendente). Cada capítulo termina com exercícios e respostas.
"""
    )

st.divider()
st.subheader("Sumário", anchor=False)
paginas = ["cap1", "cap2", "cap3", "cap4", "cap5"]
cols = st.columns(5)
for col, cap, pag in zip(cols, indice(), paginas):
    with col.container(border=True, height=330):
        st.markdown(f"**Capítulo {cap['numero']}**")
        st.page_link(f"paginas/{pag}.py", label=cap["titulo"])
        st.caption(" · ".join(f"{n} {t}" for n, t in cap["secoes"][:-1]))
