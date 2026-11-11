import streamlit as st

st.title("Referências bibliográficas")
st.caption("Obras de referência do livro, no formato ABNT (NBR 6023).")

REFERENCIAS = [
    "BURDEN, Richard L.; FAIRES, J. Douglas. **Análise numérica**. Tradução da 8. ed. norte-americana. "
    "São Paulo: Cengage Learning, 2008.",
    "RUGGIERO, Márcia A. Gomes; LOPES, Vera Lúcia da Rocha. **Cálculo numérico**: aspectos teóricos e "
    "computacionais. 2. ed. São Paulo: Makron Books, 1996.",
]

for ref in REFERENCIAS:
    with st.container(border=True):
        st.markdown(ref)
