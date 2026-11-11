"""
Converte o livro em LaTeX (pasta fonte_latex/) no conteúdo usado pelo site Streamlit.

Uso (na pasta do projeto):
    python conversor/converter.py

Gera:
    conteudo/<capitulo>.json   blocos de texto (Markdown + LaTeX), quadros, figuras e aplicativos
    static/figuras/*.png       figuras TikZ/pgfplots compiladas com pdflatex

Requisitos: pandoc e uma distribuição LaTeX (pdflatex, pgfplots, tcolorbox) e pdftoppm (poppler).
Depois de editar um .tex, rode o conversor de novo e reinicie o Streamlit.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FONTE = RAIZ / "fonte_latex"
SAIDA = RAIZ / "conteudo"
FIGS = RAIZ / "static" / "figuras"

CAPITULOS = [
    ("ponto_flutuante", "pontoflutuante"),
    ("zeros_de_funcoes", "zeros"),
    ("sistemas_lineares", "sistemas"),
    ("interpolacao", "interp"),
    ("ajuste_de_curvas", "ajuste"),
    ("integracao_numerica", "integracao"),
    ("edo", "edo"),
]

MACROS = r"""
\newcommand{\x}{\mathbf{x}}
\newcommand{\bb}{\mathbf{b}}
\newcommand{\y}{\mathbf{y}}
\newcommand{\bits}[1]{\texttt{#1}}
"""

TEOREMAS = {"definicao": "Definição", "teorema": "Teorema", "proposicao": "Proposição", "corolario": "Corolário"}
CAIXAS = ["atividade", "leitura", "exemplo", "observacao", "tcolorbox", "proof", *TEOREMAS]

PANDOC_FMT = (
    "markdown-smart-simple_tables-multiline_tables-grid_tables-raw_html-raw_attribute-raw_tex"
    "-bracketed_spans-native_divs-native_spans-fenced_divs-header_attributes-link_attributes"
    "-inline_code_attributes-fenced_code_attributes-implicit_figures-subscript-superscript"
)


# ---------------------------------------------------------------------------
# utilidades de parsing
# ---------------------------------------------------------------------------
def ler_chaves(s: str, i: int, abre="{", fecha="}") -> tuple[str, int]:
    """Lê um grupo balanceado começando em s[i] == abre. Retorna (conteúdo, índice após)."""
    assert s[i] == abre, (s[i : i + 30], abre)
    prof = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == abre:
            prof += 1
        elif c == fecha:
            prof -= 1
            if prof == 0:
                return s[i + 1 : j], j + 1
        j += 1
    raise ValueError("grupo não fechado: " + s[i : i + 60])


def pular_espacos(s: str, i: int) -> int:
    while i < len(s) and s[i] in " \t":
        i += 1
    return i


def ler_opcional(s: str, i: int) -> tuple[str | None, int]:
    j = pular_espacos(s, i)
    if j < len(s) and s[j] == "[":
        # colchetes podem conter chaves: conta só colchetes fora de chaves
        prof_ch = 0
        k = j + 1
        while k < len(s):
            c = s[k]
            if c == "\\":
                k += 2
                continue
            if c == "{":
                prof_ch += 1
            elif c == "}":
                prof_ch -= 1
            elif c == "]" and prof_ch == 0:
                return s[j + 1 : k], k + 1
            k += 1
    return None, i


def ler_rotulos_aux() -> dict[str, str]:
    aux = (FONTE / "livro.aux").read_text(encoding="utf-8", errors="replace")
    rot = {}
    for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{(.*?)\}\{", aux):
        val = re.sub(r"\\textbf\s*", "", m.group(2))
        val = re.sub(r"[{}\s]", "", val).rstrip(".")
        rot[m.group(1)] = val
    return rot


# ---------------------------------------------------------------------------
# figuras TikZ
# ---------------------------------------------------------------------------
def compilar_figura(corpo: str, nome: str) -> str:
    preambulo = (FONTE / "preambulo.tex").read_text(encoding="utf-8")
    doc = (
        "\\documentclass[11pt,border=8pt,varwidth=16.5cm]{standalone}\n\\newcounter{chapter}\n"
        + preambulo
        + "\n\\begin{document}\n\\centering\n"
        + corpo
        + "\n\\end{document}\n"
    )
    chave = hashlib.sha1(doc.encode()).hexdigest()[:10]
    destino = FIGS / f"{nome}.png"
    marca = FIGS / f".{nome}.hash"
    if destino.exists() and marca.exists() and marca.read_text() == chave:
        return destino.name
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "fig.tex").write_text(doc, encoding="utf-8")
        r = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "fig.tex"],
            cwd=t, capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(r.stdout[-2500:])
            raise RuntimeError(f"Falha ao compilar a figura {nome}")
        subprocess.run(["pdftoppm", "-r", "220", "-png", "-singlefile", "fig.pdf", "fig"], cwd=t, check=True)
        FIGS.mkdir(parents=True, exist_ok=True)
        shutil.copy(t / "fig.png", destino)
    marca.write_text(chave)
    return destino.name


# ---------------------------------------------------------------------------
# pré-processamento do LaTeX
# ---------------------------------------------------------------------------
def preprocessar(tex: str, cap_num: int, cap_id: str, rotulos: dict[str, str], meta: dict) -> tuple[str, str]:
    # 1) \def\arqX{arquivo} -> substituição
    defs = dict(re.findall(r"^\\def\\(\w+)\{([^}]*)\}", tex, flags=re.M))
    tex = re.sub(r"^\\def\\\w+\{[^}]*\}\s*$", "", tex, flags=re.M)
    tex = re.sub(r"^\\providecommand.*$", "", tex, flags=re.M)
    for nome in sorted(defs, key=len, reverse=True):
        tex = re.sub(r"\\" + nome + r"(?![A-Za-z])", lambda _m, v=defs[nome]: v, tex)
    tex = re.sub(r"(?<!\\)%.*$", "", tex, flags=re.M)  # comentários

    # 2) título do capítulo
    m = re.search(r"\\chapter(\[[^\]]*\])?\{", tex)
    titulo, fim = ler_chaves(tex, m.end() - 1)
    tex = tex[: m.start()] + tex[fim:]
    tex = re.sub(r"\\label\{cap:[^}]*\}", "", tex, count=1)

    # 3) quadro "Como usar": adapta ao site
    tex = re.sub(
        r"trazem (?:o|um) link\s*\\textbf\{\[abrir o aplicativo\]\}\s*,?\s*(?:que abre o arquivo correspondente no GeoGebra Classic)?",
        lambda _m: r"trazem o aplicativo, que abre aqui mesmo na página (botão \textbf{Abrir o aplicativo})",
        tex,
    )
    tex = re.sub(r"Para que os links funcionem.*?(?=\n\s*\n|\\end\{tcolorbox\})", "", tex, flags=re.S)
    tex = tex.replace(r"abrem dois textos de apoio:", r"trazem textos de apoio em PDF:")

    # linhas "Arquivo: ggb/..." do PDF: no site o aplicativo aparece em aba, então só registramos o arquivo
    tex = re.sub(
        r"(?:\\small)?\\textbf\{Arquivo[^}]*\}\\\\\s*\\ggbabrir\{([^}]*)\}\{\\texttt\{ggb/\\arqtxt\{[^}]*\}\}\}",
        lambda mm: "\\ggbabrir{" + mm.group(1) + "}{}",
        tex,
    )

    # cores definidas no preâmbulo -> hexadecimal (o KaTeX não conhece os nomes)
    cores = dict(
        (n, "#%02x%02x%02x" % tuple(int(v) for v in rgb.split(",")))
        for n, rgb in re.findall(r"\\definecolor\{(\w+)\}\{RGB\}\{([\d,]+)\}", (FONTE / "preambulo.tex").read_text(encoding="utf-8"))
    )
    tex = re.sub(r"\\(color|textcolor)\{(\w+)\}", lambda mm: "\\" + mm.group(1) + "{" + cores.get(mm.group(2), mm.group(2)) + "}", tex)

    # 4) símbolos
    tex = tex.replace(r"\ding{51}", "✓").replace(r"\ding{55}", "✗")
    tex = re.sub(r"\\paragraph\{([^}]*)\}", r"\\textbf{\1} ", tex)
    tex = re.sub(r"\\(begin)\{(itemize|enumerate|description)\}\[[^\]]*\]", r"\\\1{\2}", tex)

    # 5) referências cruzadas
    def ref(mm):
        return rotulos.get(mm.group(1), "?")

    tex = re.sub(r"\\ref\{([^}]*)\}", ref, tex)
    tex = re.sub(r"\\label\{[^}]*\}", "", tex)

    # 6) links para aplicativos e PDFs
    def ggb_link(s: str) -> str:
        out, i = [], 0
        while True:
            k = s.find(r"\ggbabrir{", i)
            if k < 0:
                out.append(s[i:])
                return "".join(out)
            arq, j = ler_chaves(s, k + len(r"\ggbabrir"))
            txt, j = ler_chaves(s, j)
            meta["ggb_citados"].append(arq.strip())
            visivel = (r"\textbf{" + txt + "}") if txt.strip() else ""
            out.append(s[i:k] + visivel + f"QQAPP{len(meta['ggb_citados'])}QQ")
            i = j

    def pdf_link(s: str) -> str:
        out, i = [], 0
        while True:
            k = s.find(r"\pdfabrir{", i)
            if k < 0:
                out.append(s[i:])
                return "".join(out)
            arq, j = ler_chaves(s, k + len(r"\pdfabrir"))
            txt, j = ler_chaves(s, j)
            out.append(s[i:k] + r"\href{app/static/complementos/" + arq.strip() + "}{" + txt + "}")
            i = j

    # 7) figuras: blocos figure / center com tikz / tikz solto
    contador_fig = [0]

    def substituir_figuras(s: str) -> str:
        res, i = [], 0
        padrao = re.compile(r"\\begin\{(figure|center)\}|\\begin\{tikzpicture\}")
        while True:
            m = padrao.search(s, i)
            if not m:
                res.append(s[i:])
                return "".join(res)
            env = m.group(1) or "tikzpicture"
            fim_tag = "\\end{" + env + "}"
            k = s.find(fim_tag, m.end())
            bloco = s[m.end() : k]
            if env != "tikzpicture" and "tikzpicture" not in bloco:
                res.append(s[i : k + len(fim_tag)])  # center sem figura: mantém
                i = k + len(fim_tag)
                continue
            if env == "figure":
                _, ini = ler_opcional(bloco, 0)
                bloco = bloco[ini:]
                contador_fig[0] += 1
            cap = ""
            c = bloco.find(r"\caption")
            if c >= 0:
                cap, f = ler_chaves(bloco, c + len(r"\caption"))
                bloco = bloco[:c] + bloco[f:]
            corpo = bloco if env != "tikzpicture" else "\\begin{tikzpicture}" + bloco + "\\end{tikzpicture}"
            corpo = corpo.replace(r"\centering", "")
            n = len(meta["figuras"]) + 1
            nome = f"cap{cap_num}_fig{n:02d}"
            meta["figuras"].append((nome, corpo))
            legenda = (f"\\textbf{{Figura {cap_num}.{contador_fig[0]}.}} " + cap) if cap else ""
            res.append(s[i : m.start()] + f"\n\nQQFIG{n}QQ\n\n{legenda}\n\nQQFIMFIG{n}QQ\n\n")
            i = k + len(fim_tag)

    tex = substituir_figuras(tex)

    # 8) seções numeradas
    sec = [0, 0]

    def secoes(mm):
        tipo, estrela = mm.group(1), mm.group(2)
        return mm.group(0) if estrela else ("\\" + tipo + "*" + "{" + "QQSEC" + tipo + "QQ")

    tex = re.sub(r"\\(section|subsection)(\*?)\{", secoes, tex)

    def numerar(mm):
        if mm.group(1) == "section":
            sec[0] += 1
            sec[1] = 0
            return f"{cap_num}.{sec[0]} "
        sec[1] += 1
        return f"{cap_num}.{sec[0]}.{sec[1]} "

    tex = re.sub(r"QQSEC(section|subsection)QQ", numerar, tex)

    # 9) quadros -> marcadores
    cont_teo = [0]
    pilha: list[int] = []
    res, i = [], 0
    padrao = re.compile(r"\\(begin|end)\{(" + "|".join(CAIXAS) + r")\}")
    while True:
        m = padrao.search(tex, i)
        if not m:
            res.append(tex[i:])
            break
        res.append(tex[i : m.start()])
        acao, env = m.groups()
        j = m.end()
        if acao == "begin":
            bid = len(meta["caixas"]) + 1
            info = {"tipo": env, "titulo": "", "arquivo": ""}
            if env in ("atividade", "leitura"):
                titulo_cx, j = ler_chaves(tex, pular_espacos(tex, j))
                arq, j = ler_chaves(tex, pular_espacos(tex, j))
                info["arquivo"] = arq.strip()
                titulo_cx = ("Atividade no GeoGebra: " if env == "atividade" else "Leitura complementar: ") + titulo_cx
            elif env == "tcolorbox":
                opt, j = ler_opcional(tex, j)
                mt = re.search(r"title=\{", opt or "")
                titulo_cx = ler_chaves(opt, mt.end() - 1)[0] if mt else ""
                info["tipo"] = "como_usar" if titulo_cx.startswith("Como usar") else "algoritmo"
            elif env == "exemplo":
                opt, j = ler_opcional(tex, j)
                opt = (opt or "").strip()
                if opt.startswith("{") and opt.endswith("}"):
                    opt = opt[1:-1]
                titulo_cx = "Exemplo" + opt
            elif env == "observacao":
                titulo_cx = "Observação"
            elif env == "proof":
                opt, j = ler_opcional(tex, j)
                titulo_cx = opt or "Demonstração"
            else:
                opt, j = ler_opcional(tex, j)
                cont_teo[0] += 1
                titulo_cx = f"{TEOREMAS[env]} {cap_num}.{cont_teo[0]}" + (f" ({opt})" if opt else "")
            info["titulo_tex"] = titulo_cx
            meta["caixas"].append(info)
            pilha.append(bid)
            res.append(f"\n\nQQBOX{bid}QQ\n\n{titulo_cx}\n\nQQTITULO{bid}QQ\n\n")
        else:
            bid = pilha.pop()
            res.append(f"\n\nQQFIMBOX{bid}QQ\n\n")
        i = j
    tex = "".join(res)

    # links (depois dos quadros, para registrar arquivos citados dentro das atividades)
    tex = pdf_link(ggb_link(tex))
    return titulo, tex


# ---------------------------------------------------------------------------
# pós-processamento do Markdown e montagem da árvore de blocos
# ---------------------------------------------------------------------------
def pandoc(tex: str) -> str:
    r = subprocess.run(
        ["pandoc", "-f", "latex", "-t", PANDOC_FMT, "--wrap=none"],
        input=MACROS + tex, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    if r.stderr.strip():
        print("  pandoc:", r.stderr.strip()[:400])
    return r.stdout


def ajustar_md(md: str) -> str:
    # matemática em destaque em linhas próprias (o Streamlit exige $$ isolado)
    md = re.sub(r"\$\$(.+?)\$\$", lambda m: "\n\n$$\n" + m.group(1).strip() + "\n$$\n\n", md, flags=re.S)
    # cabeçalhos: seções (nível 1) -> ##, subseções -> ###
    md = re.sub(r"^# ", "## ", md, flags=re.M)
    md = re.sub(r"^## (\d+\.\d+\.\d+ )", r"### \1", md, flags=re.M)
    md = re.sub(r"^## (Respostas|Referências)\s*$", r"### \1", md, flags=re.M)
    # links relativos para PDFs
    md = md.replace("](app/static/", "](./app/static/")
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def montar_arvore(md: str, meta: dict) -> list:
    raiz: list = []
    pilha: list[tuple[dict, list]] = []
    atual = raiz
    buffer: list[str] = []
    modo_titulo: dict | None = None

    def descarregar():
        texto = "\n".join(buffer)
        for k in re.findall(r"QQAPP(\d+)QQ", texto):
            arq = meta["ggb_citados"][int(k) - 1]
            for bloco, _ in reversed(pilha):
                if bloco.get("estilo") == "atividade":
                    if arq not in bloco["aplicativos"]:
                        bloco["aplicativos"].append(arq)
                    break
        texto = ajustar_md(re.sub(r"QQAPP\d+QQ", "", texto))
        buffer.clear()
        if not texto:
            return
        if modo_titulo is not None:
            modo_titulo["titulo"] = (modo_titulo.get("titulo", "") + " " + texto).strip()
        else:
            atual.append({"tipo": "md", "texto": texto})

    for linha in md.split("\n"):
        s = linha.strip()
        if m := re.fullmatch(r"QQBOX(\d+)QQ", s):
            descarregar()
            info = meta["caixas"][int(m.group(1)) - 1]
            bloco = {"tipo": "caixa", "estilo": info["tipo"], "titulo": "", "arquivo": info["arquivo"], "filhos": []}
            if info["tipo"] == "atividade":
                bloco["aplicativos"] = [info["arquivo"]]
            atual.append(bloco)
            pilha.append((bloco, atual))
            atual = bloco["filhos"]
            modo_titulo = bloco
        elif re.fullmatch(r"QQTITULO\d+QQ", s):
            descarregar()
            modo_titulo = None
        elif re.fullmatch(r"QQFIMBOX\d+QQ", s):
            descarregar()
            bloco, atual = pilha.pop()
        elif m := re.fullmatch(r"QQFIG(\d+)QQ", s):
            descarregar()
            nome, _ = meta["figuras"][int(m.group(1)) - 1]
            bloco = {"tipo": "figura", "arquivo": f"{nome}.png", "titulo": "", "filhos": []}
            atual.append(bloco)
            pilha.append((bloco, atual))
            atual = bloco["filhos"]
        elif re.fullmatch(r"QQFIMFIG\d+QQ", s):
            descarregar()
            bloco, atual = pilha.pop()
            bloco["legenda"] = "\n\n".join(f["texto"] for f in bloco.pop("filhos"))
        else:
            buffer.append(linha)
    descarregar()
    return raiz


def coletar_arquivos(blocos: list, meta: dict) -> None:
    """Em cada atividade, lista o aplicativo principal e os outros citados no texto do quadro."""
    for b in blocos:
        if b["tipo"] == "caixa":
            if b["estilo"] == "atividade":
                texto = json.dumps(b["filhos"], ensure_ascii=False)
                extras = [a for a in meta["ordem_ggb"] if a != b["arquivo"] and a in texto]
                b["aplicativos"] = [b["arquivo"], *extras]
            coletar_arquivos(b["filhos"], meta)


def main() -> None:
    rotulos = ler_rotulos_aux()
    SAIDA.mkdir(exist_ok=True)
    indice = []
    for num, (arq, cap_id) in enumerate(CAPITULOS, start=1):
        print(f"Capítulo {num}: {arq}")
        tex = (FONTE / "capitulos" / f"{arq}.tex").read_text(encoding="utf-8")
        meta = {"caixas": [], "figuras": [], "ggb_citados": []}
        titulo, tex2 = preprocessar(tex, num, cap_id, rotulos, meta)
        for nome, corpo in meta["figuras"]:
            compilar_figura(corpo, nome)
        md = pandoc(tex2)
        blocos = montar_arvore(md, meta)
        titulo_md = ajustar_md(pandoc(titulo))
        secoes = []

        def achar(bs):
            for b in bs:
                if b["tipo"] == "md":
                    secoes.extend(re.findall(r"^## (\d+\.\d+) (.+)$", b["texto"], flags=re.M))
                else:
                    achar(b.get("filhos", []))

        achar(blocos)
        dados = {"numero": num, "id": arq, "titulo": titulo_md, "blocos": blocos, "secoes": secoes}
        (SAIDA / f"{arq}.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
        indice.append({"numero": num, "id": arq, "titulo": titulo_md, "secoes": secoes})
        print(f"  {len(meta['caixas'])} quadros, {len(meta['figuras'])} figuras, {len(secoes)} seções")
    (SAIDA / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
