"""
Cálculo Numérico Interativo — versão web (Streamlit) do livro, com os aplicativos do GeoGebra.

Executar:  streamlit run app.py
"""
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Cálculo Numérico Interativo",
    page_icon=":material/functions:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
  .block-container { max-width: 1180px; padding-top: 2.2rem; }
  /* quadros do livro (mesmas cores do PDF) */
  [class*="st-key-cx-atividade"]  { border-left: 6px solid #c85a00 !important; background: #fff7ef; }
  [class*="st-key-cx-leitura"]    { border-left: 6px solid #0f6b62 !important; background: #f1faf8; }
  [class*="st-key-cx-exemplo"]    { border-left: 6px solid #3c64b4 !important; background: #f6f8fe; }
  [class*="st-key-cx-observacao"] { border-left: 6px solid #2f8f5a !important; background: #f3fbf5; }
  [class*="st-key-cx-teorema"], [class*="st-key-cx-proposicao"], [class*="st-key-cx-corolario"]
                                  { border-left: 6px solid #143c96 !important; background: #f3f6fd; }
  [class*="st-key-cx-definicao"]  { border-left: 6px solid #8a8f98 !important; background: #f7f7f8; }
  [class*="st-key-cx-algoritmo"]  { border-left: 6px solid #5a78c8 !important; background: #f5f7fd; }
  [class*="st-key-cx-como_usar"]  { border-left: 6px solid #8a8f98 !important; background: #f8f8f6; }
  [class*="st-key-cx-proof"]      { border: none !important; background: transparent; padding-left: 0; }
  [class*="st-key-fig-"] { align-items: center; }
  [class*="st-key-fig-"] img { max-width: 100%; background: #fff; border-radius: 6px; }
  [class*="st-key-fig-"] [data-testid="stCaptionContainer"],
  [class*="st-key-fig-"] [data-testid="stCaptionContainer"] p { text-align: center; max-width: 820px; margin: 0 auto; }
  [class*="st-key-fig-"] [data-testid="stImage"], [class*="st-key-fig-"] [data-testid="stImageContainer"] { margin: 0 auto; }
  @media (prefers-color-scheme: dark) {
    [class*="st-key-cx-"] { background: transparent !important; }
  }
</style>
""",
    unsafe_allow_html=True,
)

paginas = {
    "Livro": [
        st.Page("paginas/capa.py", title="Capa e apresentação", icon=":material/home:", default=True),
        st.Page("paginas/cap1.py", title="1. Ponto flutuante", icon=":material/looks_one:", url_path="ponto-flutuante"),
        st.Page("paginas/cap2.py", title="2. Zeros de funções", icon=":material/looks_two:", url_path="zeros-de-funcoes"),
        st.Page("paginas/cap3.py", title="3. Sistemas lineares", icon=":material/looks_3:", url_path="sistemas-lineares"),
        st.Page("paginas/cap4.py", title="4. Interpolação", icon=":material/looks_4:", url_path="interpolacao"),
        st.Page("paginas/cap5.py", title="5. Ajuste de curvas", icon=":material/looks_5:", url_path="ajuste-de-curvas"),
        st.Page("paginas/cap6.py", title="6. Integração numérica", icon=":material/looks_6:", url_path="integracao-numerica"),
        st.Page("paginas/cap7.py", title="7. Equações diferenciais", icon=":material/counter_7:", url_path="equacoes-diferenciais"),
    ],
    "Materiais": [
        st.Page("paginas/aplicativos.py", title="Todos os aplicativos", icon=":material/apps:", url_path="aplicativos"),
        st.Page("paginas/complementos.py", title="Textos complementares", icon=":material/description:", url_path="complementos"),
    ],
}

pg = st.navigation(paginas)

with st.sidebar:
    st.download_button(
        "Baixar o livro em PDF",
        data=(RAIZ / "static" / "livro.pdf").read_bytes(),
        file_name="Calculo_Numerico_Interativo.pdf",
        mime="application/pdf",
        icon=":material/picture_as_pdf:",
        use_container_width=True,
    )
    st.divider()

pg.run()
