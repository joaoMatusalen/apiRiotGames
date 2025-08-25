import requests
import pandas as pd
import ast
import time
from datetime import timedelta, datetime

token = "RGAPI-6a9d5501-8e90-4b3b-972d-a755ced3dfd7"

def editLinkApi(link:str):
    """
    Adiciona o token ao link.
    """
    apiToken = token
    return link, {"api_key": apiToken}

def accountInfo(region:str, nome:str, tag:str):
    """
    Coleta as informações da account.
    Doc: https://developer.riotgames.com/apis#account-v1.
    """
   
    linkApi = "https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{nome}/{tag}"
    linkApi = linkApi.format(region=region, nome=nome, tag=tag)
    url, params = editLinkApi(linkApi)
    max_retries = 5

    for i in range(max_retries):
        resp = requests.get(url, params=params)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Nova tentativa após:", 121)) # Padrão de 121 segundos
            print(f"Limite de requisões realizada. Nova tentativa em {retry_after} segundos...")
            time.sleep(retry_after)
        elif resp.status_code == 200:
            return resp.json()
        else:
            print(f"Error {resp.status_code}: {resp.text}")
            break

    return {}

def idMatchs(region:str, puuid:str, count=50, start=0):
    """
    Coleta os id's das partidas.
    Doc: https://developer.riotgames.com/apis#match-v5.
    """

    linkApi = "https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
    linkApi = linkApi.format(region=region, puuid=puuid, count=count, start=start)
    url, params = editLinkApi(linkApi)

    max_retries = 5
    for i in range(max_retries):
        resp = requests.get(url, params=params)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Nova tentativa após:", 121)) # Padrão de 121 segundos
            print(f"Limite de requisões realizada. Nova tentativa em {retry_after} segundos...")
            time.sleep(retry_after)
        elif resp.status_code == 200:
            return resp.json()
        else:
            print(f"Error {resp.status_code}: {resp.text}")
            break
    return []

def infoMatchs(region, idMatch):
    """
    Coleta as informações de acordo com o id das partidas.
    Doc: https://developer.riotgames.com/apis#match-v5.
    """

    linkApi = "https://{region}.api.riotgames.com/lol/match/v5/matches/{idMatch}"
    linkApi = linkApi.format(region=region, idMatch=idMatch)
    url, params = editLinkApi(linkApi)
    max_retries = 5
    for i in range(max_retries):
        resp = requests.get(url, params=params)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Nova tentativa após:", 121)) # Padrão de 121 segundos
            print(f"Limite de requisões realizada. Nova tentativa em {retry_after} segundos...")
            time.sleep(retry_after)
        elif resp.status_code == 200:
            return resp.json()
        else:
            print(f"Error {resp.status_code}: {resp.text}")
            break
    return {}

def collectMultipleMatchesData(region, nome, tag):
    """
    Coleta dados de todas as partidas para um jogador específico
    
    Args:
        region (str): Região do jogador (ex: "americas")
        nome (str): Nome do jogador
        tag (str): Tag do jogador
    
    Returns:
        list: Lista de dicionários contendo dados das partidas
    """
    # Obter informações da conta
    account = accountInfo(region, nome, tag)
    if not account:
        print("Não foi possível obter informações da conta. Verifique o nome, tag e região.")
        return []
    puuid = account["puuid"]

    print(puuid)
    
    allMatchIds = []
    start_index = 0
    count_per_request = 100 # Maximo de requests por historico de partidas

    while True:
        print(f"Coletando IDs de partidas a partir do índice {start_index}...")
        matchIds_page = idMatchs(region, puuid, count=count_per_request, start=start_index)
        
        if not matchIds_page:
            break # No more match IDs to retrieve
        
        allMatchIds.extend(matchIds_page)
        start_index += count_per_request

    print(f"Total de IDs de partidas coletados: {len(allMatchIds)}")

    # Lista para armazenar dados das partidas
    matchesData = []
    
    # Coletar dados de cada partida
    for i, matchId in enumerate(allMatchIds):
        print(f"Coletando dados da partida {i+1}/{len(allMatchIds)}: {matchId}")
        
        # Obter informações da partida
        matchInfo = infoMatchs(region, matchId)
        
        if not matchInfo:
            print(f"Não foi possível obter informações para a partida {matchId}")
            continue

        # Encontrar posição do jogador na lista de participantes
        participants = matchInfo["info"]["participants"]
        playerPosition = None
        
        for j, participant in enumerate(participants):
            if participant["puuid"] == puuid:
                playerPosition = j
                break
        
        if playerPosition is None:
            print(f"Jogador não encontrado na partida {matchId}")
            continue
        
        # Extrair dados relevantes da partida
        playerData = participants[playerPosition]
        
        matchData = {
            "matchId": matchId,
            "gameCreation": matchInfo["info"]["gameCreation"],
            "gameDuration": matchInfo["info"]["gameDuration"],
            "gameMode": matchInfo["info"]["gameMode"],
            "championName": playerData["championName"],
            "championId": playerData["championId"],
            "kills": playerData["kills"],
            "deaths": playerData["deaths"],
            "assists": playerData["assists"],
            "lane": playerData["lane"],
            "pentaKills": playerData["pentaKills"],
            "win": playerData["win"],
            "totalDamageDealtToChampions": playerData["totalDamageDealtToChampions"],
            "totalMinionsKilled": playerData["totalMinionsKilled"],
            "goldEarned": playerData["goldEarned"],
            "visionScore": playerData["visionScore"],
            "wardsPlaced": playerData["wardsPlaced"],
            "wardsKilled": playerData["wardsKilled"],
            "firstBloodKill": playerData["firstBloodKill"],
            "doubleKills": playerData["doubleKills"],
            "tripleKills": playerData["tripleKills"],
            "quadraKills": playerData["quadraKills"],
            "teamPosition": playerData["teamPosition"],
            "totalDamageTaken": playerData["totalDamageTaken"]
        }
        
        matchesData.append(matchData)
    
    return matchesData

def convertToDataFrame(matchesData):
    """
    Converte lista de dados das partidas em DataFrame do pandas
    
    Args:
        matchesData (list): Lista de dicionários com dados das partidas
    
    Returns:
        pandas.DataFrame: DataFrame com os dados das partidas
    """
    return pd.DataFrame(matchesData)

def analyzeMatchData(df):
    """
    Realiza análises nos dados das partidas coletadas.
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados das partidas.
        
    Returns:
        dict: Dicionário contendo os resultados das análises.
    """
    analysisResults = {}
    
    # KDA (Kills + Assists / Deaths)
    df['kda'] = (df['kills'] + df['assists']) / df['deaths'].replace(0, 1) # Avoid division by zero
    analysisResults['average_kda'] = df['kda'].mean()
    
    # Win Total/Rate
    analysisResults['total_win'] = df['win'].sum() 
    analysisResults['total_loss'] = (~df['win']).sum() 
    analysisResults['win_rate'] = df['win'].mean() * 100 # Convert to percentage
    
    # stats per game
    analysisResults['total_kills'] = df['kills'].sum()
    analysisResults['average_kills'] = df['kills'].mean()
    analysisResults['total_deaths'] = df['deaths'].sum()
    analysisResults['average_deaths'] = df['deaths'].mean()
    analysisResults['total_assists'] = df['assists'].sum()
    analysisResults['average_assists'] = df['assists'].mean()
    analysisResults['total_damage_dealt'] = df['totalDamageDealtToChampions'].sum()
    analysisResults['average_damage_dealt'] = df['totalDamageDealtToChampions'].mean()
    analysisResults['total_minions_killed'] = df['totalMinionsKilled'].sum()
    analysisResults['average_minions_killed'] = df['totalMinionsKilled'].mean()
    analysisResults['total_gold_earned'] = df['goldEarned'].sum()
    analysisResults['average_gold_earned'] = df['goldEarned'].mean()
    analysisResults['total_vision_score'] = df['visionScore'].sum()
    analysisResults['average_vision_score'] = df['visionScore'].mean()
    
    # Total stats
    analysisResults['total_penta_kills'] = df['pentaKills'].sum()
    analysisResults['total_double_kills'] = df['doubleKills'].sum()
    analysisResults['total_triple_kills'] = df['tripleKills'].sum()
    analysisResults['total_quadra_kills'] = df['quadraKills'].sum()

    # Most played champion, KDA and Win Rate
    champion_stats = df.groupby("championName").agg(
        games_played=("championName", "size"),
        total_kills=("kills", "sum"),
        total_deaths=("deaths", "sum"),
        total_assists=("assists", "sum"),
        total_wins=("win", "sum")
    ).reset_index()
    champion_stats["kda"] = (champion_stats["total_kills"] + champion_stats["total_assists"]) / champion_stats["total_deaths"].replace(0, 1)
    champion_stats["win_rate"] = (champion_stats["total_wins"] / champion_stats["games_played"]) * 100

    # Order for games_played in asc and catch the first champion
    champion_stats = champion_stats.sort_values("games_played", ascending=False)
    most_played_champion = champion_stats.iloc[0]

    analysisResults["most_played_champion"] = most_played_champion["championName"]
    analysisResults["most_played_champion_total_kills"] = most_played_champion["total_kills"]
    analysisResults["most_played_champion_total_deaths"] = most_played_champion["total_deaths"]
    analysisResults["most_played_champion_total_assists"] = most_played_champion["total_assists"]
    analysisResults["most_played_champion"] = most_played_champion["championName"]
    analysisResults["most_played_champion_kda"] = most_played_champion["kda"]
    analysisResults["most_played_champion_win_rate"] = most_played_champion["win_rate"]
    analysisResults["most_played_champion_qtd_matchs"] = most_played_champion["games_played"]

    # Most played lane, KDA and Win Rate
    lane_stats = df.groupby("lane").agg(
        games_played=("lane", "size"),
        total_kills=("kills", "sum"),
        total_deaths=("deaths", "sum"),
        total_assists=("assists", "sum"),
        total_wins=("win", "sum")
    ).reset_index()
    lane_stats["kda"] = (lane_stats["total_kills"] + lane_stats["total_assists"]) / lane_stats["total_deaths"].replace(0, 1)
    lane_stats["win_rate"] = (lane_stats["total_wins"] / lane_stats["games_played"]) * 100
    most_played_lane = lane_stats.loc[lane_stats["games_played"].idxmax()]
    
    analysisResults["most_played_lane"] = most_played_lane["lane"]
    analysisResults["most_played_lane_total_kills"] = most_played_lane["total_kills"]
    analysisResults["most_played_lane_total_deaths"] = most_played_lane["total_deaths"]
    analysisResults["most_played_lane_total_assists"] = most_played_lane["total_assists"]
    analysisResults["most_played_lane_kda"] = most_played_lane["kda"]
    analysisResults["most_played_lane_win_rate"] = most_played_lane["win_rate"]

    # Most played game mode
    most_played_game_mode = df["gameMode"].value_counts().idxmax()
    analysisResults["most_played_game_mode"] = most_played_game_mode

    # Time matchs
    analysisResults['total_time_played'] = str(timedelta(seconds=int(df['gameDuration'].sum())))
    analysisResults['last_match_played'] = datetime.fromtimestamp(df["gameCreation"].iloc[-1]/1000).strftime("%d/%m/%Y")

    return analysisResults

# Example of how to use the new functions
if __name__ == "__main__":
    # Replace with actual player data
    player_region = "americas"
    player_name = "m1ll4dy"
    player_tag = "br1"

    print(f"Coletando dados de partidas para {player_name}#{player_tag}...")

    allMatchesData = collectMultipleMatchesData(player_region, player_name, player_tag)

    if allMatchesData:
        df_matches = convertToDataFrame(allMatchesData)
        print("Dados das partidas coletados:")
        print(df_matches.head())

        analysis_results = analyzeMatchData(df_matches)
        print("\nResultados da Análise:")
        for key, value in analysis_results.items():
            if isinstance(value, str):
                print(f"{key.replace('_', ' ').title()}: {value}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value:.2f}")
    else:
        print("Nenhum dado de partida foi coletado.")