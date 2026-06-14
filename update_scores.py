#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║        BOLÃO COPA DO MUNDO 2026 – Atualizador de Placares    ║
║                  Universidade Federal Fluminense              ║
╚══════════════════════════════════════════════════════════════╝

Como usar:
  python update_scores.py            → Atualiza uma vez e sai
  python update_scores.py --loop     → Atualiza a cada 5 minutos (ideal para dia de jogo)
"""

import sys
import time
import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials


# ╔══════════════════════════════════════════════╗
# ║          ⚙️  CONFIGURAÇÕES  (edite aqui)     ║
# ╚══════════════════════════════════════════════╝

# 1. Chave da API football-data.org (gratuita em https://www.football-data.org/client/register)
API_KEY = "7356e8e14a474883b7ac847b9fde36f2"

# 2. Nome exato da sua planilha no Google Sheets (após importar o .xlsx)
NOME_PLANILHA = "Bolao da Copa do Mundo 2026 UFF v1"

# 3. Caminho para o arquivo de credenciais da conta de serviço Google
ARQUIVO_CREDENCIAIS = "credentials.json"

# Intervalo entre atualizações no modo --loop (em segundos)
INTERVALO_LOOP = 300  # 5 minutos


# ╔══════════════════════════════════════════════╗
# ║    🌍  Mapeamento nomes PT → EN (API)        ║
# ╚══════════════════════════════════════════════╝
# Traduz os nomes da planilha para os nomes usados pela API
NOMES_PT_PARA_EN = {
    "México": "Mexico",
    "África do Sul": "South Africa",
    "Coréia do Sul": "South Korea",
    "República Tcheca": "Czechia",
    "Canadá": "Canada",
    "Bósnia": "Bosnia-Herzegovina",
    "Qatar": "Qatar",
    "Suíça": "Switzerland",
    "Brasil": "Brazil",
    "Marrocos": "Morocco",
    "Haiti": "Haiti",
    "Escócia": "Scotland",
    "Estados Unidos": "USA",
    "Paraguai": "Paraguay",
    "Austrália": "Australia",
    "Turquia": "Türkiye",
    "Alemanha": "Germany",
    "Curaçao": "Curaçao",
    "Costa do Marfim": "Ivory Coast",
    "Equador": "Ecuador",
    "Holanda": "Netherlands",
    "Japão": "Japan",
    "Suécia": "Sweden",
    "Tunísia": "Tunisia",
    "Bélgica": "Belgium",
    "Egito": "Egypt",
    "Irã": "Iran",
    "Nova Zelândia": "New Zealand",
    "Espanha": "Spain",
    "Cabo Verde": "Cape Verde",
    "Arábia Saudita": "Saudi Arabia",
    "Uruguai": "Uruguay",
    "França": "France",
    "Senegal": "Senegal",
    "Iraque": "Iraq",
    "Noruega": "Norway",
    "Argentina": "Argentina",
    "Argélia": "Algeria",
    "Áustria": "Austria",
    "Jordânia": "Jordan",
    "Portugal": "Portugal",
    "Congo": "Congo",
    "Uzbequistão": "Uzbekistan",
    "Colômbia": "Colombia",
    "Inglaterra": "England",
    "Croácia": "Croatia",
    "Gana": "Ghana",
    "Panamá": "Panama",
}
# Mapeamento inverso EN → PT para exibir na planilha
NOMES_EN_PARA_PT = {v: k for k, v in NOMES_PT_PARA_EN.items()}


# ╔══════════════════════════════════════════════╗
# ║         📡  BUSCAR PARTIDAS NA API           ║
# ╚══════════════════════════════════════════════╝
def buscar_partidas():
    """
    Busca todas as partidas da Copa do Mundo 2026 na API football-data.org.
    Retorna uma lista de dicionários com informações de cada jogo.
    """
    # ID da Copa do Mundo 2026 na football-data.org é CWC (Club World Cup) ou FIFA WC 2026
    # O código da competição para Copa do Mundo FIFA é "WC"
    url = "https://api.football-data.org/v4/competitions/WC2026/matches"
    cabecalhos = {
        "X-Auth-Token": API_KEY
    }

    try:
        print("📡 Buscando partidas na API football-data.org...")
        resposta = requests.get(url, headers=cabecalhos, timeout=15)

        if resposta.status_code == 200:
            dados = resposta.json()
            partidas = dados.get("matches", [])
            print(f"   ✅ {len(partidas)} partidas encontradas.")
            return partidas

        elif resposta.status_code == 403:
            print("   ❌ ERRO 403: API Key inválida ou sem permissão.")
            print("      Verifique a variável API_KEY no início do script.")
            return []

        elif resposta.status_code == 429:
            print("   ⚠️  ERRO 429: Limite de requisições atingido. Aguardando 60 segundos...")
            time.sleep(60)
            return buscar_partidas()

        else:
            print(f"   ❌ Erro na API: Status {resposta.status_code} – {resposta.text[:200]}")
            return []

    except requests.exceptions.ConnectionError:
        print("   ❌ Sem conexão com a internet. Verifique sua rede.")
        return []
    except requests.exceptions.Timeout:
        print("   ❌ Timeout: A API demorou demais para responder.")
        return []


# ╔══════════════════════════════════════════════╗
# ║       📊  CONECTAR AO GOOGLE SHEETS          ║
# ╚══════════════════════════════════════════════╝
def conectar_sheets():
    """
    Conecta à conta de serviço Google e abre a planilha do bolão.
    Retorna o objeto da planilha.
    """
    escopos = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    try:
        print("🔗 Conectando ao Google Sheets...")
        credenciais = Credentials.from_service_account_file(
            ARQUIVO_CREDENCIAIS, scopes=escopos
        )
        cliente = gspread.authorize(credenciais)
        planilha = cliente.open(NOME_PLANILHA)
        print(f"   ✅ Planilha '{NOME_PLANILHA}' encontrada.")
        return planilha

    except FileNotFoundError:
        print(f"   ❌ Arquivo '{ARQUIVO_CREDENCIAIS}' não encontrado.")
        print("      Siga o passo 2 do COMO_RODAR.md para criar as credenciais.")
        sys.exit(1)

    except gspread.exceptions.SpreadsheetNotFound:
        print(f"   ❌ Planilha '{NOME_PLANILHA}' não encontrada no Google Drive.")
        print("      Verifique o nome exato e se foi compartilhada com o e-mail da conta de serviço.")
        sys.exit(1)


# ╔══════════════════════════════════════════════╗
# ║       🏆  DETERMINAR STATUS DO JOGO          ║
# ╚══════════════════════════════════════════════╝
def traduzir_status(status_api):
    """Traduz o status da API do inglês para o português."""
    mapa = {
        "SCHEDULED": "⏳ Agendado",
        "TIMED":     "⏳ Agendado",
        "IN_PLAY":   "🔴 AO VIVO",
        "PAUSED":    "⏸️  Intervalo",
        "FINISHED":  "✅ Encerrado",
        "SUSPENDED": "⚠️  Suspenso",
        "POSTPONED": "📅 Adiado",
        "CANCELLED": "❌ Cancelado",
    }
    return mapa.get(status_api, status_api)


# ╔══════════════════════════════════════════════╗
# ║    📝  ATUALIZAR ABA "Placares_Reais"        ║
# ╚══════════════════════════════════════════════╝
def atualizar_planilha(planilha, partidas):
    """
    Cria ou atualiza a aba 'Placares_Reais' com todos os resultados reais.
    A aba existente é limpa e reescrita a cada execução.
    """
    # ── Abrir ou criar a aba ──────────────────────────────────────
    try:
        aba = planilha.worksheet("Placares_Reais")
        aba.clear()
        print("   🗑️  Aba 'Placares_Reais' limpa para atualização.")
    except gspread.exceptions.WorksheetNotFound:
        aba = planilha.add_worksheet(title="Placares_Reais", rows=200, cols=10)
        print("   ✨ Aba 'Placares_Reais' criada.")

    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # ── Cabeçalho da aba ─────────────────────────────────────────
    cabecalho = [
        [f"🏆 BOLÃO COPA DO MUNDO 2026 – UFF  |  Atualizado em: {agora}"],
        [],
        ["Jogo Nº", "Data", "Hora", "Time 1", "Gols 1", "x", "Gols 2", "Time 2", "Status", "Fase"],
    ]

    # ── Processar partidas ────────────────────────────────────────
    encerrados = 0
    ao_vivo    = 0
    agendados  = 0
    linhas_dados = []

    for idx, partida in enumerate(partidas, start=1):
        status   = partida.get("status", "")
        fase_en  = partida.get("stage", "")
        # Traduzir fase
        fases = {
            "GROUP_STAGE":          "Fase de Grupos",
            "LAST_32":              "1ª Eliminatória",
            "ROUND_OF_16":          "Oitavas de Final",
            "QUARTER_FINALS":       "Quartas de Final",
            "SEMI_FINALS":          "Semifinal",
            "THIRD_PLACE":          "Disputa 3º Lugar",
            "FINAL":                "Final",
        }
        fase_pt = fases.get(fase_en, fase_en)

        # Data e hora
        data_iso = partida.get("utcDate", "")
        try:
            dt = datetime.datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
            dt_local = dt.astimezone(datetime.timezone(datetime.timedelta(hours=-3)))  # Horário de Brasília
            data_str = dt_local.strftime("%d/%m/%Y")
            hora_str = dt_local.strftime("%H:%M")
        except Exception:
            data_str = data_iso[:10]
            hora_str = ""

        # Times
        time1_en = partida.get("homeTeam", {}).get("name", "")
        time2_en = partida.get("awayTeam", {}).get("name", "")
        time1_pt = NOMES_EN_PARA_PT.get(time1_en, time1_en)
        time2_pt = NOMES_EN_PARA_PT.get(time2_en, time2_en)

        # Placar
        score  = partida.get("score", {})
        fulltime = score.get("fullTime", {})
        halftime = score.get("halfTime", {})

        if status == "FINISHED":
            gols1 = fulltime.get("home", "-")
            gols2 = fulltime.get("away", "-")
            encerrados += 1
        elif status in ("IN_PLAY", "PAUSED"):
            gols1 = fulltime.get("home", 0)
            gols2 = fulltime.get("away", 0)
            ao_vivo += 1
        else:
            gols1 = "-"
            gols2 = "-"
            agendados += 1

        linhas_dados.append([
            idx,
            data_str,
            hora_str,
            time1_pt,
            gols1,
            "x",
            gols2,
            time2_pt,
            traduzir_status(status),
            fase_pt,
        ])

    # ── Escrever no Sheets ────────────────────────────────────────
    todas_linhas = cabecalho + linhas_dados
    aba.update("A1", todas_linhas)

    # Formatar cabeçalho (negrito + cor)
    aba.format("A1:J1", {
        "textFormat": {"bold": True, "fontSize": 12},
        "backgroundColor": {"red": 0.13, "green": 0.55, "blue": 0.13},
        "horizontalAlignment": "CENTER",
    })
    aba.merge_cells("A1:J1")

    aba.format("A3:J3", {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
        "horizontalAlignment": "CENTER",
    })

    # Centralizar colunas de gols e x
    aba.format(f"E4:G{len(linhas_dados)+3}", {
        "horizontalAlignment": "CENTER",
    })

    print(f"
📊 RESUMO DA ATUALIZAÇÃO:")
    print(f"   ✅ Jogos encerrados : {encerrados}")
    print(f"   🔴 Jogos ao vivo    : {ao_vivo}")
    print(f"   ⏳ Jogos agendados  : {agendados}")
    print(f"   📝 Total de linhas  : {len(linhas_dados)}")
    print(f"   ⏰ Horário          : {agora} (Brasília)")


# ╔══════════════════════════════════════════════╗
# ║              🚀  FUNÇÃO PRINCIPAL            ║
# ╚══════════════════════════════════════════════╝
def executar():
    """Executa uma rodada de atualização completa."""
    print()
    print("=" * 60)
    print("🏆  BOLÃO COPA DO MUNDO 2026 – UFF  |  Atualizando...")
    print("=" * 60)

    partidas  = buscar_partidas()
    if not partidas:
        print("⚠️  Nenhuma partida retornada. Encerrando sem atualizar o Sheets.")
        return

    planilha  = conectar_sheets()
    print("📝 Atualizando a planilha...")
    atualizar_planilha(planilha, partidas)

    print()
    print("✅  Atualização concluída! Abra o Google Sheets para ver o resultado.")
    print()


# ╔══════════════════════════════════════════════╗
# ║                 MODO LOOP                    ║
# ╚══════════════════════════════════════════════╝
if __name__ == "__main__":
    modo_loop = "--loop" in sys.argv

    if modo_loop:
        print(f"🔄 Modo LOOP ativado — atualizando a cada {INTERVALO_LOOP // 60} minutos.")
        print("   Pressione Ctrl+C para parar.")
        try:
            while True:
                executar()
                print(f"💤 Aguardando {INTERVALO_LOOP // 60} minutos para a próxima atualização...")
                time.sleep(INTERVALO_LOOP)
        except KeyboardInterrupt:
            print("\n👋 Loop encerrado pelo usuário. Até logo!")
    else:
        executar()
