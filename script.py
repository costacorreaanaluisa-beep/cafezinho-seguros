"""
Cafezinho do Seguro
Robô que envia e-mail diário com conteúdo de seguro de vida PJ.
Roda via GitHub Actions todo dia às 10h UTC (7h de Brasília).
"""

import os
import json
import smtplib
import requests
import feedparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


# =============================================================
# PARTE 1 — INTELIGÊNCIA ARTIFICIAL (Google Gemini, gratuito)
# =============================================================
# A função abaixo manda um pedido para a IA e recebe de volta
# o Termo do Dia, a Dica Técnica e o Cenário Econômico.

def gerar_conteudo_ia():
    # Groq é gratuito, sem restrição de região, usa o modelo Llama 3
    prompt = """Você é um especialista em seguros de vida coletivo PJ no Brasil, com profundo conhecimento técnico, regulatório e de mercado.

Gere conteúdo original para o e-mail de hoje do "Cafezinho do Seguro".

Retorne SOMENTE um objeto JSON válido, sem markdown, sem ``` e sem qualquer texto fora do JSON.

Formato exigido:
{
  "termo": {
    "nome": "nome do termo técnico de seguro de vida PJ",
    "explicacao": "explicação simples e clara em 2 a 3 frases, como se falasse com alguém leigo",
    "exemplo": "um exemplo prático e concreto em 1 a 2 frases"
  },
  "dica": {
    "titulo": "título curto e direto para a dica",
    "conteudo": "conhecimento técnico em 3 a 4 frases sobre coberturas, modalidades, regulação da SUSEP ou casos típicos de seguro de vida coletivo PJ. Varie o tema a cada dia."
  },
  "cenario": {
    "selic": "valor percentual aproximado da taxa Selic atual, ex: 10,50% a.a.",
    "ipca": "valor percentual aproximado do IPCA acumulado em 12 meses, ex: 4,83%",
    "impacto": "1 a 2 frases explicando como esse cenário econômico impacta o mercado de seguro de vida PJ no Brasil"
  }
}"""

    resposta = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        },
        timeout=30
    )

    texto = resposta.json()["choices"][0]["message"]["content"].strip()
    # Remove blocos de markdown caso a IA os inclua por engano
    if texto.startswith("```"):
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
    return json.loads(texto.strip())


# =============================================================
# PARTE 2 — COTAÇÃO DO DÓLAR EM TEMPO REAL (API gratuita)
# =============================================================
# Usa a AwesomeAPI, que é 100% gratuita e não precisa de cadastro.

def buscar_dolar():
    try:
        resposta = requests.get(
            "https://economia.awesomeapi.com.br/json/last/USD-BRL",
            timeout=10
        )
        dados = resposta.json()
        valor = float(dados["USDBRL"]["bid"])
        return f"R$ {valor:.2f}"
    except Exception:
        # Se der qualquer erro de conexão, retorna mensagem amigável
        return "indisponível"


# =============================================================
# PARTE 3 — NOTÍCIA DO SETOR SEGURADOR (RSS da CNseg)
# =============================================================
# RSS é um formato de notícias que sites publicam automaticamente.
# A gente lê esse feed e pega a notícia mais recente.

def buscar_noticia_cnseg():
    try:
        feed = feedparser.parse("https://cnseg.org.br/feed/")
        if feed.entries:
            entrada = feed.entries[0]
            return {"titulo": entrada.title, "link": entrada.link}
    except Exception:
        pass
    return {"titulo": "Sem notícias disponíveis no momento.", "link": "#"}


# =============================================================
# PARTE 4 — TOP 3 MANCHETES GERAIS (RSS da Agência Brasil)
# =============================================================

def buscar_noticias_brasil():
    try:
        feed = feedparser.parse(
            "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml"
        )
        noticias = []
        for entrada in feed.entries[:3]:
            noticias.append({"titulo": entrada.title, "link": entrada.link})
        return noticias
    except Exception:
        return []


# =============================================================
# PARTE 5 — MONTAR O E-MAIL EM HTML
# =============================================================
# HTML é a linguagem dos e-mails bonitos (igual à de sites).
# Cada bloco abaixo é uma seção do e-mail.

def montar_email(conteudo_ia, dolar, noticia_cnseg, noticias_brasil):
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    # Monta os itens de notícias da Agência Brasil em HTML
    itens_brasil = ""
    for noticia in noticias_brasil:
        itens_brasil += f"""
        <div class="news-item">
          <a href="{noticia['link']}" target="_blank">{noticia['titulo']}</a>
          <p class="fonte">Fonte: Agência Brasil</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cafezinho do Seguro</title>
<style>
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    background-color: #f5efe6;
    margin: 0;
    padding: 20px;
    color: #2c1a06;
  }}
  .container {{
    max-width: 620px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(74, 44, 10, 0.15);
  }}
  .header {{
    background: #3b1f08;
    color: #ffffff;
    padding: 32px 30px;
    text-align: center;
  }}
  .header h1 {{
    margin: 0 0 6px 0;
    font-size: 26px;
    letter-spacing: 1px;
  }}
  .header .subtitulo {{
    color: #d4a96a;
    font-size: 13px;
    margin: 0;
  }}
  .section {{
    padding: 24px 30px;
    border-bottom: 1px solid #f0e4d0;
  }}
  .section-title {{
    font-family: Arial, sans-serif;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #8a6a4a;
    margin: 0 0 12px 0;
  }}
  .term-name {{
    font-size: 22px;
    font-weight: bold;
    color: #3b1f08;
    margin: 0 0 10px 0;
  }}
  .destaque {{
    background: #fdf6ee;
    border-left: 4px solid #d4a96a;
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    margin-top: 12px;
    font-size: 14px;
    line-height: 1.6;
  }}
  p {{
    line-height: 1.7;
    font-size: 15px;
    margin: 8px 0;
  }}
  .dica-titulo {{
    font-size: 17px;
    font-weight: bold;
    color: #3b1f08;
    margin: 0 0 10px 0;
  }}
  .econ-grid {{
    display: flex;
    gap: 12px;
    margin-bottom: 14px;
  }}
  .econ-item {{
    flex: 1;
    background: #fdf6ee;
    border: 1px solid #e8d5b7;
    padding: 14px 10px;
    border-radius: 10px;
    text-align: center;
  }}
  .econ-valor {{
    font-size: 20px;
    font-weight: bold;
    color: #3b1f08;
    display: block;
    margin-bottom: 4px;
  }}
  .econ-label {{
    font-family: Arial, sans-serif;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #8a6a4a;
  }}
  .aviso-ia {{
    font-family: Arial, sans-serif;
    font-size: 11px;
    color: #aaa;
    margin-top: 10px;
    font-style: italic;
  }}
  .news-item {{
    margin-bottom: 14px;
  }}
  .news-item a {{
    color: #3b1f08;
    text-decoration: none;
    font-weight: 600;
    font-size: 15px;
    line-height: 1.5;
  }}
  .news-item a:hover {{
    text-decoration: underline;
  }}
  .fonte {{
    font-family: Arial, sans-serif;
    font-size: 11px;
    color: #aaa;
    margin: 3px 0 0 0;
  }}
  .footer {{
    background: #3b1f08;
    color: #d4a96a;
    text-align: center;
    padding: 22px 20px;
    font-family: Arial, sans-serif;
    font-size: 12px;
    line-height: 1.8;
  }}
</style>
</head>
<body>
<div class="container">

  <!-- CABEÇALHO -->
  <div class="header">
    <h1>&#9749; Cafezinho do Seguro</h1>
    <p class="subtitulo">{data_hoje} &mdash; Seu caf&#233; com conhecimento em seguro de vida PJ</p>
  </div>

  <!-- SEÇÃO 1: TERMO DO DIA -->
  <div class="section">
    <p class="section-title">&#128218; Termo do Dia</p>
    <p class="term-name">{conteudo_ia['termo']['nome']}</p>
    <p>{conteudo_ia['termo']['explicacao']}</p>
    <div class="destaque">
      <strong>Exemplo pr&#225;tico:</strong> {conteudo_ia['termo']['exemplo']}
    </div>
  </div>

  <!-- SEÇÃO 2: DICA TÉCNICA -->
  <div class="section">
    <p class="section-title">&#128161; Dica T&#233;cnica</p>
    <p class="dica-titulo">{conteudo_ia['dica']['titulo']}</p>
    <p>{conteudo_ia['dica']['conteudo']}</p>
  </div>

  <!-- SEÇÃO 3: CENÁRIO ECONÔMICO -->
  <div class="section">
    <p class="section-title">&#128200; Cen&#225;rio Econ&#244;mico</p>
    <div class="econ-grid">
      <div class="econ-item">
        <span class="econ-valor">{conteudo_ia['cenario']['selic']}</span>
        <span class="econ-label">Selic</span>
      </div>
      <div class="econ-item">
        <span class="econ-valor">{conteudo_ia['cenario']['ipca']}</span>
        <span class="econ-label">IPCA (12m)</span>
      </div>
      <div class="econ-item">
        <span class="econ-valor">{dolar}</span>
        <span class="econ-label">D&#243;lar</span>
      </div>
    </div>
    <p>{conteudo_ia['cenario']['impacto']}</p>
    <p class="aviso-ia">&#9888;&#65039; Selic e IPCA s&#227;o refer&#234;ncias aproximadas geradas por intelig&#234;ncia artificial. O d&#243;lar &#233; em tempo real. Consulte o Banco Central para dados oficiais.</p>
  </div>

  <!-- SEÇÃO 4: MANCHETE DO SETOR SEGURADOR -->
  <div class="section">
    <p class="section-title">&#128240; Manchete do Setor Segurador</p>
    <div class="news-item">
      <a href="{noticia_cnseg['link']}" target="_blank">{noticia_cnseg['titulo']}</a>
      <p class="fonte">Fonte: CNseg</p>
    </div>
  </div>

  <!-- SEÇÃO 5: OUTRAS MANCHETES -->
  <div class="section">
    <p class="section-title">&#128newspapers; Outras Manchetes</p>
    {itens_brasil}
  </div>

  <!-- RODAPÉ -->
  <div class="footer">
    <p><strong>Cafezinho do Seguro</strong></p>
    <p>Conhecimento di&#225;rio em seguro de vida PJ &mdash; enviado automaticamente toda manh&#227; &#9749;</p>
  </div>

</div>
</body>
</html>"""

    return html


# =============================================================
# PARTE 6 — ENVIAR O E-MAIL VIA GMAIL
# =============================================================

def enviar_email(conteudo_html):
    # Pega as credenciais salvas como segredos no GitHub
    remetente = os.environ["EMAIL_REMETENTE"]
    senha = os.environ["EMAIL_SENHA"]
    destinatario = "costacorreaanaluisa@gmail.com"

    # Monta a mensagem de e-mail
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"☕ Cafezinho do Seguro — {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"] = remetente
    msg["To"] = destinatario

    # Anexa o conteúdo HTML ao e-mail
    parte_html = MIMEText(conteudo_html, "html", "utf-8")
    msg.attach(parte_html)

    # Conecta ao servidor do Gmail e envia
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(remetente, senha)
        servidor.sendmail(remetente, destinatario, msg.as_string())

    print("E-mail enviado com sucesso!")


# =============================================================
# EXECUÇÃO PRINCIPAL
# =============================================================
# Aqui é onde tudo começa quando o robô acorda no GitHub Actions.

if __name__ == "__main__":
    print("Gerando conteudo com IA...")
    conteudo_ia = gerar_conteudo_ia()

    print("Buscando cotacao do dolar...")
    dolar = buscar_dolar()

    print("Buscando noticia da CNseg...")
    noticia_cnseg = buscar_noticia_cnseg()

    print("Buscando manchetes da Agencia Brasil...")
    noticias_brasil = buscar_noticias_brasil()

    print("Montando e-mail...")
    html = montar_email(conteudo_ia, dolar, noticia_cnseg, noticias_brasil)

    print("Enviando e-mail...")
    enviar_email(html)
