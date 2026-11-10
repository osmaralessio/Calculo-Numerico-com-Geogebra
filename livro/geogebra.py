"""Incorporação dos aplicativos .ggb no Streamlit (mecanismo oficial deployggb.js + ggbBase64)."""
from __future__ import annotations

import base64
import json
import re
import zipfile
from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

PASTA_GGB = Path(__file__).resolve().parents[1] / "static" / "ggb"

# Nomes amigáveis dos aplicativos (usados nas abas e na página "Todos os aplicativos").
NOMES = {
    "MudancaDeBase.ggb": "Mudança de base",
    "SistemaPontoFlutuante_reta.ggb": "Sistema F(β,t,m,M) na reta",
    "Maquina_PontoFlutuante_8bits.ggb": "Máquina de 8 bits",
    "Maquina_PontoFlutuante_16bits.ggb": "Máquina de 16 bits",
    "Maquina_PontoFlutuante_32bits.ggb": "Máquina de 32 bits",
    "Maquina_PontoFlutuante_64bits.ggb": "Máquina de 64 bits",
    "metodoBisseccao_2026_corrigido.ggb": "Bisseção (versão 1)",
    "metodoBisseccao_2026_correto_and.ggb": "Bisseção (versão 2)",
    "metodoposicaofalsa_2026_correto.ggb": "Posição falsa (versão 1)",
    "metodoposicaofalsa_2026_correto_and.ggb": "Posição falsa (versão 2)",
    "metodopontofixoJAVASCRIPT_2026_final_corrigido.ggb": "Ponto fixo",
    "metodopontofixoJAVASCRIPT_2026_CORRIGIDO_ex02_CONVERGINDO.ggb": "Ponto fixo — converge",
    "metodopontofixoJAVASCRIPT_2026_CORRIGIDO_ex02_DIVERGINDO.ggb": "Ponto fixo — diverge",
    "metodoNewtonRaphson_2026_corrigido.ggb": "Newton-Raphson",
    "metododasecanteJAVASCRIPT_2026_CORRIGIDO.ggb": "Secante",
    "EliminacaoGauss_sistema4x5_compacto.ggb": "Eliminação de Gauss 4×4",
    "FatoracaoLU_3x3.ggb": "Fatoração LU 3×3",
    "FatoracaoLU_4x4.ggb": "Fatoração LU 4×4",
    "GaussJacobi_sistema3x3_rolagem.ggb": "Gauss-Jacobi 3×3",
    "GaussSeidel_sistema3x3_rolagem.ggb": "Gauss-Seidel 3×3",
    "EliminacaoGauss_Interpolacao_4pontos_automatico.ggb": "Interpolação por sistema linear",
    "Interpolacao_Lagrange_4pontos_automatico.ggb": "Interpolação de Lagrange",
    "Interpolacao_Newton_4pontos_automatico.ggb": "Interpolação de Newton",
    "01_metodo_dos_minimos_quadrados_linear_simples_TCC_2026.ggb": "MMQ: reta (5 pontos)",
    "metodo_dos_minimos_quadrados_reta_rolagem.ggb": "MMQ: reta com rolagem",
    "metodo_dos_minimos_quadrados_exemplo02_parabola_rolagem.ggb": "MMQ: parábola (11 pontos)",
    "aproximacao_funcao_mmq_rolagem.ggb": "MMQ: parábola (pontos A…K)",
    "03_metodo_dos_minimos_quadrados_linear_combinada_TCC_2026.ggb": "MMQ: combinação de funções",
    "02_RegressaoLinearUsandoGradienteDescendente_junho.ggb": "Gradiente descendente: reta",
    "05_aproximacaoGDescCombFuncao.ggb": "Gradiente: combinação sem padronizar",
    "06_aproximacaoGDescCombFuncao_Escalonada.ggb": "Gradiente: combinação padronizada",
    "04_aproximacaoGDescCombFuncoespadronizada_03_07.ggb": "Gradiente: padronizada com volta",
}

LARGURA_COLUNA = 1080  # largura útil estimada da coluna de texto (px)


def nome_app(arquivo: str) -> str:
    return NOMES.get(arquivo, arquivo.removesuffix(".ggb").replace("_", " "))


@lru_cache(maxsize=64)
def _dados(arquivo: str) -> tuple[str, int, int]:
    caminho = PASTA_GGB / arquivo
    raw = caminho.read_bytes()
    largura, altura = 1200, 640
    try:
        with zipfile.ZipFile(caminho) as z:
            xml = z.read("geogebra.xml").decode("utf-8", "replace")
        m = re.search(r'<window width="(\d+)" height="(\d+)"', xml)
        if m:
            largura, altura = int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return base64.b64encode(raw).decode(), largura, altura


def baixar(arquivo: str, chave: str) -> None:
    st.download_button(
        "Baixar o arquivo .ggb",
        data=(PASTA_GGB / arquivo).read_bytes(),
        file_name=arquivo,
        mime="application/vnd.geogebra.file",
        key=f"dl-{chave}",
        icon=":material/download:",
    )


def applet(arquivo: str, largura_coluna: int = LARGURA_COLUNA, escala_max: float = 1.0) -> None:
    """Desenha o aplicativo ajustado à largura da coluna, sem cortar nada."""
    b64, w, h = _dados(arquivo)
    escala = min(escala_max, largura_coluna / w)
    altura_iframe = int(h * escala) + 8
    params = {
        "appName": "classic",
        "width": w,
        "height": h,
        "ggbBase64": b64,
        "showToolBar": False,
        "showMenuBar": False,
        "showAlgebraInput": False,
        "showResetIcon": True,
        "enableRightClick": False,
        "enableShiftDragZoom": True,
        "showFullscreenButton": True,
        "language": "pt",
        "borderColor": "#FFFFFF",
    }
    html = f"""
<div id="moldura" style="width:100%;height:{altura_iframe - 4}px;overflow:hidden;font-family:sans-serif">
  <div id="ggb"></div>
  <p id="aviso" style="display:none;color:#7a4b00;background:#fff4dc;padding:12px;border-radius:8px">
    Não foi possível carregar o GeoGebra (é preciso conexão com a internet e acesso a geogebra.org).
    Use o botão <b>Baixar o arquivo .ggb</b> e abra o arquivo no GeoGebra Classic.
  </p>
</div>
<script>
  var P = {json.dumps(params)};
  function iniciar() {{
    var W = {w}, H = {h};
    var larg = document.getElementById('moldura').clientWidth;
    var alt = {altura_iframe - 4};
    P.scale = Math.min({escala_max}, larg / W, alt / H);
    P.allowUpscale = P.scale > 1;
    new GGBApplet(P, true).inject('ggb');
  }}
  var s = document.createElement('script');
  s.src = 'https://www.geogebra.org/apps/deployggb.js';
  s.onload = iniciar;
  s.onerror = function () {{ document.getElementById('aviso').style.display = 'block'; }};
  document.head.appendChild(s);
  setTimeout(function () {{ if (typeof GGBApplet === 'undefined') document.getElementById('aviso').style.display = 'block'; }}, 15000);
</script>
"""
    components.html(html, height=altura_iframe, scrolling=False)


def bloco_aplicativos(arquivos: list[str], chave: str, largura_coluna: int = LARGURA_COLUNA - 40) -> None:
    """Botão para abrir o(s) aplicativo(s) da atividade, com abas quando há mais de um."""
    abas = st.tabs([nome_app(a) for a in arquivos]) if len(arquivos) > 1 else [st.container()]
    for i, (arq, aba) in enumerate(zip(arquivos, abas)):
        with aba:
            c1, c2, c3 = st.columns([1.3, 1.1, 2.2], vertical_alignment="center")
            aberto = c1.toggle("Abrir o aplicativo", key=f"tg-{chave}-{i}")
            with c2:
                baixar(arq, f"{chave}-{i}")
            c3.page_link("paginas/aplicativos.py", label="Abrir em página inteira", icon=":material/open_in_full:", query_params={"app": arq})
            if aberto:
                applet(arq, largura_coluna)
