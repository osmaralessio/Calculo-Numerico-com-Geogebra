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
    "RegraTrapezios_repetida.ggb": "Regra dos trapézios repetida",
    "RegraSimpson13_repetida.ggb": "Regra 1/3 de Simpson repetida",
    "RegraSimpson38_repetida.ggb": "Regra 3/8 de Simpson repetida",
    "MetodoRomberg.ggb": "Método de Romberg",
    "QuadraturaGaussLegendre.ggb": "Quadratura de Gauss-Legendre",
    "MetodoEuler.ggb": "Método de Euler",
    "RungeKutta2.ggb": "Runge-Kutta de 2ª ordem",
    "RungeKutta4.ggb": "Runge-Kutta de 4ª ordem",
    "OrdemMetodosEDO.ggb": "Ordem dos métodos para EDOs",
    "SistemasEDO_RK4.ggb": "Sistemas de EDOs com RK4",
    "MetodoTiro.ggb": "Método do tiro",
    "DiferencasFinitasPVC.ggb": "Diferenças finitas para PVC",
}

LARGURA_COLUNA = 1080  # largura útil estimada da coluna de texto (px)

# Modo celular: em telas estreitas o aplicativo não é espremido até caber na largura;
# ele abre neste tamanho (fração do original) dentro de uma moldura que rola para os lados.
ESCALA_CELULAR = 0.70  # tamanho inicial no celular
# Tamanhos oferecidos pelos botões − e + no celular (o último aceito vale para os outros aplicativos).
ZOOMS_CELULAR = [0.5, 0.7, 0.85, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
LIMITE_CELULAR = 700        # abaixo desta largura (px) liga o modo celular
LIMITE_CELULAR_TOQUE = 900  # em telas de toque, liga abaixo desta largura (celular deitado)


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
<style>
  html, body {{ margin:0; padding:0; }}
  #barra {{ display:none; align-items:center; gap:6px; height:46px; padding:0 2px;
           font-family:sans-serif; font-size:14px; color:#1f2328; }}
  #barra button {{ min-width:44px; height:40px; font-size:20px; border:1px solid #c9c4b5; padding:0 8px;
                  border-radius:10px; background:#f3f1ea; color:#143c96; touch-action:manipulation; }}
  #barra button:disabled {{ opacity:.4; }}
  #barra #zoomTxt {{ min-width:40px; text-align:center; font-size:13px; color:#555; }}
  #barra #btTela {{ font-size:13px; margin-left:auto; }}
  #barra .sep {{ width:6px; }}
  #moldura.celular {{ overflow:auto; -webkit-overflow-scrolling:touch; }}
  #moldura:fullscreen {{ background:#fff; overflow:auto; }}
</style>
<div id="raiz">
  <div id="barra">
    <button id="btEsq" type="button" aria-label="Deslizar para a esquerda" title="Deslizar para a esquerda">◀</button>
    <button id="btDir" type="button" aria-label="Deslizar para a direita" title="Deslizar para a direita">▶</button>
    <span class="sep"></span>
    <button id="btMenos" type="button" aria-label="Diminuir" title="Diminuir o aplicativo">−</button>
    <span id="zoomTxt">70%</span>
    <button id="btMais" type="button" aria-label="Aumentar" title="Aumentar o aplicativo">+</button>
    <button id="btTela" type="button">Tela cheia</button>
  </div>
  <div id="moldura" style="width:100%;height:{altura_iframe - 4}px;overflow:hidden;font-family:sans-serif">
    <div id="ggb"></div>
    <p id="aviso" style="display:none;color:#7a4b00;background:#fff4dc;padding:12px;border-radius:8px">
      Não foi possível carregar o GeoGebra (é preciso conexão com a internet e acesso a geogebra.org).
      Use o botão <b>Baixar o arquivo .ggb</b> e abra o arquivo no GeoGebra Classic.
    </p>
  </div>
</div>
<script>
  var P = {json.dumps(params)};
  var W = {w}, H = {h}, ALT = {altura_iframe - 4}, BARRA = 50;
  var ZOOMS = {json.dumps(ZOOMS_CELULAR)};
  var API = null, ocupado = false, contador = 0, CELULAR = false;
  P.appletOnLoad = function (api) {{ API = api; ocupado = false; }};

  function ehCelular(larg) {{
    var toque = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
    return larg < {LIMITE_CELULAR} || (toque && larg < {LIMITE_CELULAR_TOQUE});
  }}

  // Tenta mudar a altura do quadro do Streamlit; devolve true se conseguiu.
  function ajustarAltura(px) {{
    try {{
      var f = window.frameElement;
      if (!f) return false;
      f.style.height = px + 'px';
      f.setAttribute('height', px);
      return true;
    }} catch (e) {{ return false; }}
  }}

  function telaCheia() {{
    var alvos = [];
    try {{ if (window.frameElement) alvos.push(window.frameElement); }} catch (e) {{}}
    alvos.push(document.getElementById('raiz'));
    for (var i = 0; i < alvos.length; i++) {{
      var el = alvos[i];
      var f = el.requestFullscreen || el.webkitRequestFullscreen;
      if (f) {{
        try {{
          var r = f.call(el);
          if (r && r.catch) r.catch(function () {{}});
          try {{ screen.orientation.lock('landscape').catch(function () {{}}); }} catch (e) {{}}
          return;
        }} catch (e) {{}}
      }}
    }}
  }}

  function lerZoom() {{
    var z = {ESCALA_CELULAR};
    try {{ var g = parseFloat(localStorage.getItem('ggbZoomCelular')); if (g) z = g; }} catch (e) {{}}
    return Math.min(ZOOMS[ZOOMS.length - 1], Math.max(ZOOMS[0], z));
  }}
  function guardarZoom(z) {{ try {{ localStorage.setItem('ggbZoomCelular', z); }} catch (e) {{}} }}

  // Dimensiona a moldura (e, se possível, o quadro) para a escala s.
  function dimensionar(s) {{
    var mold = document.getElementById('moldura');
    var altApp = Math.ceil(H * s) + 4;
    if (!ajustarAltura(altApp + BARRA + 8)) altApp = Math.min(altApp, ALT - BARRA);
    mold.style.height = altApp + 'px';
    document.getElementById('ggb').style.width = Math.ceil(W * s) + 'px';
    document.getElementById('zoomTxt').textContent = Math.round(s * 100) + '%';
    document.getElementById('btMenos').disabled = s <= ZOOMS[0] + 1e-9;
    document.getElementById('btMais').disabled = s >= ZOOMS[ZOOMS.length - 1] - 1e-9;
  }}

  function injetar() {{
    contador += 1;
    var caixa = document.getElementById('ggb');
    if (CELULAR) {{
      // No celular a caixa tem exatamente o tamanho do zoom escolhido; o GeoGebra se ajusta a ela
      // (scaleContainerClass), em vez de se encolher até caber na largura da tela.
      var cw = Math.ceil(W * P.scale), ch = Math.ceil(H * P.scale);
      caixa.innerHTML = '<div class="caixaGGB" style="width:' + cw + 'px;height:' + ch + 'px">' +
                        '<div id="ggb' + contador + '"></div></div>';
      P.scaleContainerClass = 'caixaGGB';
      P.autoHeight = false;
      P.allowUpscale = true;
    }} else {{
      caixa.innerHTML = '<div id="ggb' + contador + '"></div>';
      P.allowUpscale = P.scale > 1;
    }}
    new GGBApplet(P, true).inject('ggb' + contador);
  }}

  // Troca o zoom guardando o que já foi digitado no aplicativo.
  function mudarZoom(sentido) {{
    if (ocupado) return;
    var atual = P.scale, novo = atual;
    for (var i = 0; i < ZOOMS.length; i++) {{
      if (sentido > 0 && ZOOMS[i] > atual + 1e-9) {{ novo = ZOOMS[i]; break; }}
      if (sentido < 0 && ZOOMS[i] < atual - 1e-9) novo = ZOOMS[i];
    }}
    if (novo === atual) return;
    var mold = document.getElementById('moldura');
    var fx = mold.scrollLeft / Math.max(1, mold.scrollWidth), fy = mold.scrollTop / Math.max(1, mold.scrollHeight);
    var refazer = function () {{
      P.scale = novo; guardarZoom(novo); dimensionar(novo); injetar();
      setTimeout(function () {{ mold.scrollLeft = fx * mold.scrollWidth; mold.scrollTop = fy * mold.scrollHeight; }}, 400);
    }};
    ocupado = true;
    setTimeout(function () {{ ocupado = false; }}, 8000);
    try {{
      if (API && API.getBase64) {{
        API.getBase64(function (b64) {{ if (b64) P.ggbBase64 = b64; refazer(); }});
        return;
      }}
    }} catch (e) {{}}
    refazer();
  }}

  function modoCelular() {{
    var mold = document.getElementById('moldura');
    document.getElementById('barra').style.display = 'flex';
    mold.className = 'celular';
    var s = lerZoom();
    dimensionar(s);
    var passo = function () {{ return Math.max(120, mold.clientWidth * 0.7); }};
    document.getElementById('btEsq').onclick = function () {{ mold.scrollBy({{left: -passo(), behavior: 'smooth'}}); }};
    document.getElementById('btDir').onclick = function () {{ mold.scrollBy({{left: passo(), behavior: 'smooth'}}); }};
    document.getElementById('btMenos').onclick = function () {{ mudarZoom(-1); }};
    document.getElementById('btMais').onclick = function () {{ mudarZoom(1); }};
    var podeTela = false;
    try {{ podeTela = !!(document.fullscreenEnabled || document.webkitFullscreenEnabled); }} catch (e) {{}}
    if (podeTela) document.getElementById('btTela').onclick = telaCheia;
    else document.getElementById('btTela').style.display = 'none';
    P.enableShiftDragZoom = false;  // no toque, arrastar não move a janela gráfica por engano
    P.disableAutoScale = true;     // sem isto o GeoGebra se encolhe sozinho até caber na tela e ignora o zoom
    return s;
  }}

  function iniciar() {{
    var larg = document.getElementById('moldura').clientWidth;
    if (ehCelular(larg)) {{
      CELULAR = true;
      P.scale = modoCelular();
    }} else {{
      P.scale = Math.min({escala_max}, larg / W, ALT / H);
    }}
    injetar();
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
