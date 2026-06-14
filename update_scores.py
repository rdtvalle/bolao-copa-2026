#!/usr/bin/env python3
"""
BOLAO COPA DO MUNDO 2026 - Atualizador de Placares
Universidade Federal Fluminense

Como usar:
  python update_scores.py            -> Atualiza uma vez e sai
  python update_scores.py --loop     -> Atualiza a cada 5 minutos
"""

import sys
import time
import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials


# ============================================================
#   CONFIGURACOES  (edite aqui)
# ============================================================

# 1. Chave da API football-data.org (gratuita em https://www.football-data.org/client/register)
API_KEY = "SUA_CHAVE_AQUI"

# 2. Nome exato da sua planilha no Google Sheets (apos importar o .xlsx)
NOME_PLANILHA = "Bolao da Copa do Mundo 2026 UFF v1"

# 3. Caminho para o arquivo de credenciais da conta de servico Google
ARQUIVO_CREDENCIAIS = "credentials.json"

# Intervalo entre atualizacoes no modo --loop (em segundos)
INTERVALO_LOOP = 300  # 5 minutos


# ============================================================
#   Mapeamento nomes PT -> EN (API)
# ============================================================
NOMES_PT_PARA_EN = {
    "Mexico": "Mexico",
    "Africa do Sul": "South Africa",
    "Coreia do Sul": "South Korea",
    "Republica Tcheca": "Czechia",
    "Canada": "Canada",
    "Bosnia": "Bosnia-Herzegovina",
    "Qatar": "Qatar",
    "Suica": "Switzerland",
    "Brasil": "Brazil",
    "Marrocos": "Morocco",
    "Haiti": "Haiti",
    "Escocia": "Scotland",
    "Estados Unidos": "USA",
    "Paraguai": "Paraguay",
    "Australia": "Australia",
    "Turquia": "Turkiye",
    "Alemanha": "Germany",
    "Curacao": "Curacao",
    "Costa do Marfim": "Ivory Coast",
    "Equador": "Ecuador",
    "Holanda": "Netherlands",
    "Japao": "Japan",
    "Suecia": "Sweden",
    "Tunisia": "Tunisia",
    "Belgica": "Belgium",
    "Egito": "Egypt",
    "Ira": "Iran",
    "Nova Zelandia": "New Zealand",
    "Espanha": "Spain",
    "Cabo Verde": "Cape Verde",
    "Arabia Saudita": "Saudi Arabia",
    "Uruguai": "Uruguay",
    "Franca": "France",
    "Senegal": "Senegal",
    "Iraque": "Iraq",
    "Noruega": "Norway",
    "Argentina": "Argentina",
    "Algeria": "Algeria",
    "Austria": "Austria",
    "Jordania": "Jordan",
    "Portugal": "Portugal",
    "Congo": "Congo",
    "Uzbequistao": "Uzbekistan",
    "Colombia": "Colombia",
    "Inglaterra": "England",
    "Croacia": "Croatia",
    "Gana": "Ghana",
    "Panama": "Panama",
}

# Mapeamento inverso EN -> PT
NOMES_EN_PARA_PT = {v: k for k, v in NOMES_PT_PARA_EN.items()}


# ============================================================
#   BUSCAR PARTIDAS NA API
# ============================================================
def buscar_partidas():
    url = "https://api.football-data.org/v4/competitions/WC2026/matches"
    cabecalhos = {"X-Auth-Token": API_KEY}

    try:
        print("[INFO] Buscando partidas na API football-data.org...")
        resposta = requests.get(url, headers=cabecalhos, timeout=15)

        if resposta.status_code == 200:
            dados = resposta.json()
            partidas = dados.get("matches", [])
            print("[OK] " + str(len(partidas)) + " partidas encontradas.")
            return partidas

        elif resposta.status_code == 403:
            print("[ERRO] 403: API Key invalida ou sem permissao.")
            print("       Verifique a variavel API_KEY no inicio do script.")
            return []

        elif resposta.status_code == 429:
            print("[AVISO] 429: Limite de requisicoes atingido. Aguardando 60 segundos...")
            time.sleep(60)
            return buscar_partidas()

        else:
            print("[ERRO] Status " + str(resposta.status_code) + " - " + resposta.text[:200])
            return []

    except requests.exceptions.ConnectionError:
        print("[ERRO] Sem conexao com a internet. Verifique sua rede.")
        return []
    except requests.exceptions.Timeout:
        print("[ERRO] Timeout: A API demorou demais para responder.")
        return []


# ============================================================
#   CONECTAR AO GOOGLE SHEETS
# ============================================================
def conectar_sheets():
    escopos = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    try:
        print("[INFO] Conectando ao Google Sheets...")
        credenciais = Credentials.from_service_account_file(
            ARQUIVO_CREDENCIAIS, scopes=escopos
        )
        cliente = gspread.authorize(credenciais)
        planilha = cliente.open(NOME_PLANILHA)
        print("[OK] Planilha '" + NOME_PLANILHA + "' encontrada.")
        return planilha

    except FileNotFoundError:
        print("[ERRO] Arquivo '" + ARQUIVO_CREDENCIAIS + "' nao encontrado.")
        sys.exit(1)

    except gspread.exceptions.SpreadsheetNotFound:
        print("[ERRO] Planilha '" + NOME_PLANILHA + "' nao encontrada no Google Drive.")
        print("       Verifique o nome exato e se foi compartilhada com o e-mail da conta de servico.")
        sys.exit(1)


# ============================================================
#   TRADUZIR STATUS DO JOGO
# ============================================================
def traduzir_status(status_api):
    mapa = {
        "SCHEDULED": "Agendado",
        "TIMED":     "Agendado",
        "IN_PLAY":   "AO VIVO",
        "PAUSED":    "Intervalo",
        "FINISHED":  "Encerrado",
        "SUSPENDED": "Suspenso",
        "POSTPONED": "Adiado",
        "CANCELLED": "Cancelado",
    }
    return mapa.get(status_api, status_api)


# ============================================================
#   ATUALIZAR ABA "Placares_Reais"
# ============================================================
def atualizar_planilha(planilha, partidas):
    try:
        aba = planilha.worksheet("Placares_Reais")
        aba.clear()
        print("[INFO] Aba 'Placares_Reais' limpa para atualizacao.")
    except gspread.exceptions.WorksheetNotFound:
        aba = planilha.add_worksheet(title="Placares_Reais", rows=200, cols=10)
        print("[INFO] Aba 'Placares_Reais' criada.")

    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    cabecalho = [
        ["BOLAO COPA DO MUNDO 2026 - UFF  |  Atualizado em: " + agora],
        [],
        ["Jogo Nr", "Data", "Hora", "Time 1", "Gols 1", "x", "Gols 2", "Time 2", "Status", "Fase"],
    ]

    encerrados = 0
    ao_vivo    = 0
    agendados  = 0
    linhas_dados = []

    for idx, partida in enumerate(partidas, start=1):
        status  = partida.get("status", "")
        fase_en = partida.get("stage", "")

        fases = {
            "GROUP_STAGE":    "Fase de Grupos",
            "LAST_32":        "1a Eliminatoria",
            "ROUND_OF_16":    "Oitavas de Final",
            "QUARTER_FINALS": "Quartas de Final",
            "SEMI_FINALS":    "Semifinal",
            "THIRD_PLACE":    "Disputa 3o Lugar",
            "FINAL":          "Final",
        }
        fase_pt = fases.get(fase_en, fase_en)

        data_iso = partida.get("utcDate", "")
        try:
            dt = datetime.datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
            dt_local = dt.astimezone(datetime.timezone(datetime.timedelta(hours=-3)))
            data_str = dt_local.strftime("%d/%m/%Y")
            hora_str = dt_local.strftime("%H:%M")
        except Exception:
            data_str = data_iso[:10]
            hora_str = ""

        time1_en = partida.get("homeTeam", {}).get("name", "")
        time2_en = partida.get("awayTeam", {}).get("name", "")
        time1_pt = NOMES_EN_PARA_PT.get(time1_en, time1_en)
        time2_pt = NOMES_EN_PARA_PT.get(time2_en, time2_en)

        score    = partida.get("score", {})
        fulltime = score.get("fullTime", {})

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
            idx, data_str, hora_str,
            time1_pt, gols1, "x", gols2, time2_pt,
            traduzir_status(status), fase_pt,
        ])

    todas_linhas = cabecalho + linhas_dados
    aba.update("A1", todas_linhas)

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

    aba.format("E4:G" + str(len(linhas_dados) + 3), {
        "horizontalAlignment": "CENTER",
    })

    print("")
    print("RESUMO DA ATUALIZACAO:")
    print("  Jogos encerrados : " + str(encerrados))
    print("  Jogos ao vivo    : " + str(ao_vivo))
    print("  Jogos agendados  : " + str(agendados))
    print("  Total de linhas  : " + str(len(linhas_dados)))
    print("  Horario          : " + agora + " (Brasilia)")


# ============================================================
#   FUNCAO PRINCIPAL
# ============================================================
def executar():
    print("")
    print("=" * 60)
    print("BOLAO COPA DO MUNDO 2026 - UFF  |  Atualizando...")
    print("=" * 60)

    partidas = buscar_partidas()
    if not partidas:
        print("[AVISO] Nenhuma partida retornada. Encerrando sem atualizar.")
        return

    planilha = conectar_sheets()
    print("[INFO] Atualizando a planilha...")
    atualizar_planilha(planilha, partidas)

    print("")
    print("[OK] Atualizacao concluida! Abra o Google Sheets para ver o resultado.")
    print("")


# ============================================================
#   MODO LOOP
# ============================================================
if __name__ == "__main__":
    modo_loop = "--loop" in sys.argv

    if modo_loop:
        print("[LOOP] Modo LOOP ativado - atualizando a cada " + str(INTERVALO_LOOP // 60) + " minutos.")
        print("       Pressione Ctrl+C para parar.")
        try:
            while True:
                executar()
                print("[AGUARDANDO] Proxima atualizacao em " + str(INTERVALO_LOOP // 60) + " minutos...")
                time.sleep(INTERVALO_LOOP)
        except KeyboardInterrupt:
            print("\n[INFO] Loop encerrado pelo usuario. Ate logo!")
    else:
        executar()
