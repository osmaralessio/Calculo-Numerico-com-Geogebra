# Cálculo Numérico Interativo — versão web (Streamlit)

Versão web do livro "Cálculo Numérico Interativo" (Osmar Alessio, UFTM), com o mesmo texto do PDF
e os 36 aplicativos do GeoGebra abrindo dentro das páginas.

## Rodar no seu computador

Windows: dê dois cliques em INICIAR.bat (precisa do Python 3.10 ou mais novo, em python.org).

Linha de comando:

    pip install -r requirements.txt
    streamlit run app.py

O livro abre em http://localhost:8501. Os aplicativos do GeoGebra precisam de internet
(são carregados de geogebra.org).

## Publicar no Streamlit Community Cloud

1. Crie um repositório no GitHub e envie todo o conteúdo desta pasta.
2. Em share.streamlit.io, clique em "Create app", escolha o repositório, o ramo main e o arquivo app.py.
3. O arquivo .streamlit/config.toml já liga o servidor de arquivos estáticos (PDFs e figuras).

Para incluir o livro num app Streamlit que já existe, copie as pastas livro/, paginas/, conteudo/ e
static/ e acrescente as páginas de paginas/ ao st.navigation do seu app (veja app.py), mantendo
enableStaticServing = true no config.toml.

## Estrutura

    app.py                 navegação, estilos dos quadros e botão para baixar o PDF
    paginas/               capa, um arquivo por capítulo, todos os aplicativos, textos complementares
    livro/render.py        desenha o capítulo: texto, fórmulas, quadros, figuras, respostas
    livro/geogebra.py      incorpora os .ggb (deployggb.js + ggbBase64), escala à largura da página
    conteudo/*.json        texto dos capítulos, gerado a partir do LaTeX
    static/ggb/            os arquivos .ggb
    static/complementos/   os textos de apoio em PDF
    static/figuras/        capa e figuras TikZ/pgfplots compiladas
    static/livro.pdf       o livro em PDF
    fonte_latex/           os .tex originais do livro
    conversor/converter.py converte fonte_latex/ em conteudo/ e static/figuras/

## Atualizar o texto depois de editar o LaTeX

Edite os arquivos em fonte_latex/capitulos/, compile o livro como sempre (para atualizar o livro.aux,
que guarda os números de figuras e teoremas) e rode:

    python conversor/converter.py

O conversor precisa de pandoc, pdflatex (com pgfplots e tcolorbox) e pdftoppm (poppler).
Se um aplicativo novo for usado num quadro de atividade, coloque o .ggb em static/ggb/ e, se quiser,
um nome amigável no dicionário NOMES de livro/geogebra.py.
