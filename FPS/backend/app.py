import os
import sys
import random
import uuid
import copy
import datetime as dt
from typing import Any

# Zapewnienie widoczności silnika w ścieżce Pythona
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from flask import Flask, jsonify, request, session, send_from_directory
from flask_cors import CORS

# Globalny katalog zapisów (ustawiany przez run_server() na Androidzie, np. filesDir)
SAVE_DIRECTORY = None

def get_save_path(filename="career_save.json"):
    if SAVE_DIRECTORY:
        return os.path.join(SAVE_DIRECTORY, filename)
    return os.path.join(PARENT_DIR, filename)

# 1. Obliczamy absolutną ścieżkę do głównego katalogu projektu (wyjście z folderu 'backend')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

sys.path.insert(0, BASE_DIR)

# 2. Tworzymy JEDYNĄ instancję aplikacji z poprawną, absolutną ścieżką do katalogu frontend
app = Flask(__name__, static_folder=FRONTEND_DIR, template_folder=FRONTEND_DIR)
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fps-football-dev-secret-v8-fixed")

# Modyfikacja wsparcia offline / lokalnego mobilnego
app.config["SESSION_COOKIE_SAMESITE"] = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

ALLOWED_MOBILE_ORIGINS = {
    "capacitor://localhost", 
    "http://localhost", 
    "file://", 
    "null"
}

@app.after_request
def add_mobile_cors(response):
    origin = request.headers.get("Origin")
    # Zezwalanie na origin lokalny (file://, capacitor://, localhost) dla trybu offline
    if origin in ALLOWED_MOBILE_ORIGINS or not origin or origin.startswith("http://localhost"):
        response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Vary"] = "Origin"
    return response


# 3. Jawne i bezbłędne serwowanie plików frontendowych
@app.get("/")
def index(): 
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/script.js")
def serve_script():
    if os.path.exists(os.path.join(FRONTEND_DIR, "script.js")):
        return send_from_directory(FRONTEND_DIR, "script.js")
    elif os.path.exists(os.path.join(FRONTEND_DIR, "app.js")):
        return send_from_directory(FRONTEND_DIR, "app.js")
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/<path:path>")
def static_files(path):
    # Jeśli żądany plik istnieje w folderze frontend, zaserwuj go
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    # W przeciwnym razie zwróć index.html (dla SPA)
    return send_from_directory(FRONTEND_DIR, "index.html")


# --- IMPORTY SILNIKA PIŁKARSKIEGO ---

from football_engine.career.attributes import Attributes
from football_engine.career.development import apply_season_development
from football_engine.career.player import Player
from football_engine.career.injury import Injury, InjuryType, check_for_injury
from football_engine.career.position import Position
from football_engine.career.training import TrainingFocus, train
from football_engine.career.perks_and_finance import FinancialEngine, PlayerRelationship, DEFAULT_PERKS
from football_engine.club.manager import Manager
from football_engine.club.squad import select_matchday_squad
from football_engine.cup.cup_engine import CupEngine
from football_engine.match.simulation import simulate_match
from football_engine.national.callup import call_up_squad
from football_engine.national.national_team import NationalTeam, NationalTeamTier
from football_engine.season.season_engine import SeasonEngine
from football_engine.season.standings import build_table
from football_engine.time_engine import GameCalendar
from football_engine.world.club import Club
from football_engine.world.league import League
from football_engine.world.league_system import LeagueSystem

# SŁOWNIK WSZYSTKICH KLUBÓW I KOLORÓW HEX
CLUB_DATA = {
    # POLSKA - 1. Liga
    "Chrobry Głogów": {"ovr": 58, "colors": ["#F58220", "#003B70"]},
    "Lechia Gdańsk": {"ovr": 58, "colors": ["#008A45", "#FFFFFF"]},
    "Arka Gdynia": {"ovr": 57, "colors": ["#F4D03F", "#003B70"]},
    "Ruch Chorzów": {"ovr": 57, "colors": ["#0057A8", "#FFFFFF"]},
    "ŁKS Łódź": {"ovr": 57, "colors": ["#E30613", "#FFFFFF"]},
    "Miedź Legnica": {"ovr": 56, "colors": ["#006B3C", "#FFFFFF"]},
    "Polonia Warszawa": {"ovr": 56, "colors": ["#000000", "#FFFFFF", "#D71920"]},
    "Bruk-Bet Termalica Nieciecza": {"ovr": 55, "colors": ["#F58220", "#000000"]},
    "Puszcza Niepołomice": {"ovr": 55, "colors": ["#F4D03F", "#003B70"]},
    "Polonia Bytom": {"ovr": 54, "colors": ["#C8102E", "#000000"]},
    "Stal Mielec": {"ovr": 54, "colors": ["#0066B3", "#FFFFFF"]},
    "Odra Opole": {"ovr": 53, "colors": ["#0066B3", "#FFFFFF"]},
    "Pogoń Grodzisk Mazowiecki": {"ovr": 53, "colors": ["#D50032", "#003B70"]},
    "Stal Rzeszów": {"ovr": 53, "colors": ["#E30613", "#003B70"]},
    "GKS Jastrzębie": {"ovr": 51, "colors": ["#008A45", "#FFFFFF"]},
    "Pogoń Siedlce": {"ovr": 51, "colors": ["#D50032", "#003B70"]},
    "Świt Szczecin": {"ovr": 50, "colors": ["#000000", "#FFFFFF"]},
    "Wisła Puławy": {"ovr": 49, "colors": ["#0057A8", "#FFFFFF"]},

    # POLSKA - 2. Liga
    "Resovia Rzeszów": {"ovr": 49, "colors": ["#E30613", "#FFFFFF"]},
    "Chojniczanka Chojnice": {"ovr": 48, "colors": ["#E30613", "#FFFFFF"]},
    "Zagłębie Sosnowiec": {"ovr": 48, "colors": ["#E30613", "#0066B3"]},
    "Legia II Warszawa": {"ovr": 47, "colors": ["#FFFFFF", "#008C45", "#000000"]},
    "Kotwica Kołobrzeg": {"ovr": 46, "colors": ["#003B70", "#FFFFFF"]},
    "Rekord Bielsko-Biała": {"ovr": 46, "colors": ["#0066B3", "#FFFFFF"]},
    "Zawisza Bydgoszcz": {"ovr": 46, "colors": ["#0066B3", "#FFFFFF"]},
    "Avia Świdnik": {"ovr": 45, "colors": ["#0066B3", "#FFFFFF"]},
    "Hutnik Kraków": {"ovr": 45, "colors": ["#0066B3", "#FFFFFF"]},
    "Lechia Zielona Góra": {"ovr": 45, "colors": ["#008A45", "#FFFFFF"]},
    "Skra Częstochowa": {"ovr": 45, "colors": ["#0066B3", "#FFFFFF"]},
    "Sokół Kleczew": {"ovr": 45, "colors": ["#008A45", "#FFFFFF"]},
    "Concordia Piotrków Trybunalski": {"ovr": 44, "colors": ["#F4D03F", "#000000"]},
    "Wigry Suwałki": {"ovr": 44, "colors": ["#0057A8", "#FFFFFF"]},
    "Radunia Stężyca": {"ovr": 43, "colors": ["#008A45", "#FFFFFF"]},
    "Unia Skierniewice": {"ovr": 43, "colors": ["#0066B3", "#FFFFFF"]},
    "Warta Poznań II": {"ovr": 43, "colors": ["#008A45", "#FFFFFF"]},
    "Znicz Biała Piska": {"ovr": 42, "colors": ["#F4D03F", "#000000"]},

    # POLSKA - 3. Liga I
    "Polonia Warszawa II": {"ovr": 42, "colors": ["#005CA9", "#FFFFFF"]},
    "Stomil Olsztyn": {"ovr": 42, "colors": ["#005CA9", "#FFFFFF"]},
    "Olimpia Elbląg": {"ovr": 40, "colors": ["#005CA9", "#FFFFFF"]},
    "Świt Nowy Dwór Mazowiecki": {"ovr": 40, "colors": ["#005CA9", "#FFFFFF"]},
    "Huragan Wołomin": {"ovr": 39, "colors": ["#005CA9", "#FFFFFF"]},
    "Pelikan Łowicz": {"ovr": 39, "colors": ["#005CA9", "#FFFFFF"]},
    "Wisła II Płock": {"ovr": 39, "colors": ["#005CA9", "#FFFFFF"]},
    "Mazur Karczew": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Motor II Lublin": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Mławianka Mława": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Sokół Ostróda": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Legionovia Legionowo": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Sparta Świątki": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Ursus Warszawa": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Wkra Żuromin": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Pogoń II Siedlce": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},
    "Victoria Sulejówek": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},
    "Ząbkovia Ząbki": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},

    # POLSKA - 3. Liga II
    "GKS Bełchatów": {"ovr": 41, "colors": ["#005CA9", "#FFFFFF"]},
    "Olimpia Grudziądz": {"ovr": 41, "colors": ["#005CA9", "#FFFFFF"]},
    "Warta Gorzów Wlkp.": {"ovr": 41, "colors": ["#005CA9", "#FFFFFF"]},
    "Gryf Wejherowo": {"ovr": 40, "colors": ["#005CA9", "#FFFFFF"]},
    "Bałtyk Gdynia": {"ovr": 39, "colors": ["#005CA9", "#FFFFFF"]},
    "Odra Wodzisław": {"ovr": 39, "colors": ["#005CA9", "#FFFFFF"]},
    "Chemik Bydgoszcz": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "KKS 1925 Kalisz": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Sokół Pniewy": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Unia Swarzędz": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Elana Toruń": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Polonia Środa Wielkopolska": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Sparta Brodnica": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Włókniarz Kietrz": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Kotwica II Kołobrzeg": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},
    "Pogoń Staszów": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},
    "Sokół Aleksandrów Łódzki": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},
    "Nielba Wągrowiec": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},

    # POLSKA - 3. Liga III
    "Górnik Polkowice": {"ovr": 41, "colors": ["#005CA9", "#FFFFFF"]},
    "Lech II Poznań": {"ovr": 40, "colors": ["#005CA9", "#FFFFFF"]},
    "Ślęza Wrocław": {"ovr": 39, "colors": ["#005CA9", "#FFFFFF"]},
    "Górnik Konin": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Miedź II Legnica": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Polonia Bydgoszcz": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Stal Brzeg": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Victoria Września": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Chrobry II Głogów": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Karkonosze Jelenia Góra": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Piast II Gliwice": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Piast Żmigród": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Warta Sieradz": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Zagłębie II Lubin": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Odra II Opole": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},
    "Rakoniewice": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},
    "Kotwica Kołobrzeg II": {"ovr": 35, "colors": ["#005CA9", "#FFFFFF"]},
    "Unia Turza Śląska": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},

    # POLSKA - 3. Liga IV
    "Cracovia II": {"ovr": 40, "colors": ["#005CA9", "#FFFFFF"]},
    "Karpaty Krosno": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Podhale Nowy Targ": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Stal Rzeszów II": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Stal Sanok": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Wieczysta II Kraków": {"ovr": 38, "colors": ["#005CA9", "#FFFFFF"]},
    "Górnik II Łęczna": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Hetman Zamość": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Igloopol Dębica": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Motor Lublin II": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Resovia II Rzeszów": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Sokół Sokołów Małopolski": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Wisła Sandomierz": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Wisłoka Dębica": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},
    "Czarni Połaniec": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},
    "Orzeł Przeworsk": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},
    "Wisłok Wiśniowa": {"ovr": 36, "colors": ["#005CA9", "#FFFFFF"]},
    "Podlasie Biała Podlaska": {"ovr": 37, "colors": ["#005CA9", "#FFFFFF"]},

    # POLSKA - Ekstraklasa
    "Lech Poznań": {"ovr": 72, "colors": ["#FFFFFF", "#1E3A8A"]},
    "Legia Warszawa": {"ovr": 71, "colors": ["#FFFFFF", "#008C45", "#000000"]},
    "Raków Częstochowa": {"ovr": 68, "colors": ["#C8102E", "#FFFFFF", "#000000"]},
    "Jagiellonia Białystok": {"ovr": 67, "colors": ["#F4D03F", "#D4AF37", "#C8102E"]},
    "Górnik Zabrze": {"ovr": 65, "colors": ["#FFFFFF", "#000000"]},
    "Pogoń Szczecin": {"ovr": 64, "colors": ["#D50032", "#003B70"]},
    "Cracovia": {"ovr": 63, "colors": ["#FFFFFF", "#D71920"]},
    "Piast Gliwice": {"ovr": 63, "colors": ["#0066B3", "#FFFFFF"]},
    "Widzew Łódź": {"ovr": 62, "colors": ["#E30613", "#FFFFFF"]},
    "Wisła Kraków": {"ovr": 62, "colors": ["#D50032", "#FFFFFF", "#003B70"]},
    "Radomiak Radom": {"ovr": 61, "colors": ["#008A45", "#FFFFFF"]},
    "Zagłębie Lubin": {"ovr": 61, "colors": ["#E30613", "#FFFFFF", "#000000"]},
    "Śląsk Wrocław": {"ovr": 61, "colors": ["#008A45", "#FFFFFF"]},
    "GKS Katowice": {"ovr": 60, "colors": ["#F6D500", "#000000"]},
    "Korona Kielce": {"ovr": 60, "colors": ["#F4C300", "#003B70"]},
    "Motor Lublin": {"ovr": 59, "colors": ["#F5D000", "#006B3C"]},
    "Wisła Płock": {"ovr": 58, "colors": ["#0057A8", "#FFFFFF", "#E30613"]},
    "Wieczysta Kraków": {"ovr": 56, "colors": ["#000000", "#FFD700"]},

    # ANGLIA - Championship
    "West Ham United": {"ovr": 74, "colors": ["#7A263A", "#1BB1E7"]},
    "Wolverhampton Wanderers": {"ovr": 73, "colors": ["#FDB913", "#231F20"]},
    "Burnley": {"ovr": 72, "colors": ["#6C1D45", "#99D6EA"]},
    "Sheffield United": {"ovr": 70, "colors": ["#EE2737", "#FFFFFF", "#000000"]},
    "Southampton": {"ovr": 69, "colors": ["#D71920", "#FFFFFF", "#000000"]},
    "Middlesbrough": {"ovr": 68, "colors": ["#E30613", "#FFFFFF"]},
    "West Bromwich Albion": {"ovr": 68, "colors": ["#122F67", "#FFFFFF"]},
    "Norwich City": {"ovr": 67, "colors": ["#FFF200", "#00A650"]},
    "Blackburn Rovers": {"ovr": 65, "colors": ["#009EE0", "#FFFFFF"]},
    "Millwall": {"ovr": 65, "colors": ["#001F5B", "#FFFFFF"]},
    "Sheffield Wednesday": {"ovr": 65, "colors": ["#0054A6", "#FFFFFF"]},
    "Stoke City": {"ovr": 65, "colors": ["#E03A3E", "#FFFFFF"]},
    "Swansea City": {"ovr": 64, "colors": ["#FFFFFF", "#000000"]},
    "Watford": {"ovr": 64, "colors": ["#FBEE23", "#000000", "#E30613"]},
    "Derby County": {"ovr": 63, "colors": ["#FFFFFF", "#000000"]},
    "Portsmouth": {"ovr": 63, "colors": ["#001489", "#FFFFFF"]},
    "Preston North End": {"ovr": 63, "colors": ["#FFFFFF", "#000000"]},
    "Queens Park Rangers": {"ovr": 62, "colors": ["#1D5DA8", "#FFFFFF"]},
    "Wrexham": {"ovr": 62, "colors": ["#E30613", "#FFFFFF"]},
    "Oxford United": {"ovr": 61, "colors": ["#FFD700", "#0000A0"]},
    "Plymouth Argyle": {"ovr": 61, "colors": ["#00594F", "#FFFFFF"]},
    "Cardiff City": {"ovr": 60, "colors": ["#0070B8", "#FFFFFF"]},
    "Charlton Athletic": {"ovr": 60, "colors": ["#D71920", "#FFFFFF"]},
    "Bolton Wanderers": {"ovr": 59, "colors": ["#FFFFFF", "#003B70"]},
    "Lincoln City": {"ovr": 58, "colors": ["#E30613", "#FFFFFF"]},
    "Port Vale": {"ovr": 58, "colors": ["#FFFFFF", "#000000"]},

    # ANGLIA - League One
    "Birmingham City": {"ovr": 62, "colors": ["#6CABDD", "#FFFFFF"]},
    "Wigan Athletic": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Blackpool": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "Peterborough United": {"ovr": 57, "colors": ["#E30613", "#FFFFFF"]},
    "Barnsley": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Bristol Rovers": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Luton Town": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Reading": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Rotherham United": {"ovr": 56, "colors": ["#E30613", "#FFFFFF"]},
    "Stockport County": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Huddersfield Town": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},
    "Leicester City": {"ovr": 55, "colors": ["#6CABDD", "#FFFFFF"]},
    "Leyton Orient": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},
    "Mansfield Town": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},
    "Exeter City": {"ovr": 54, "colors": ["#6CABDD", "#FFFFFF"]},
    "Northampton Town": {"ovr": 54, "colors": ["#005CA9", "#FFFFFF"]},
    "Wycombe Wanderers": {"ovr": 54, "colors": ["#005CA9", "#FFFFFF"]},
    "Burton Albion": {"ovr": 53, "colors": ["#005CA9", "#FFFFFF"]},
    "Shrewsbury Town": {"ovr": 53, "colors": ["#005CA9", "#FFFFFF"]},
    "Crawley Town": {"ovr": 52, "colors": ["#005CA9", "#FFFFFF"]},
    "Doncaster Rovers": {"ovr": 52, "colors": ["#005CA9", "#FFFFFF"]},
    "Bromley": {"ovr": 51, "colors": ["#005CA9", "#FFFFFF"]},
    "Cambridge United": {"ovr": 51, "colors": ["#E30613", "#FFFFFF"]},
    "Chesterfield": {"ovr": 51, "colors": ["#005CA9", "#FFFFFF"]},
    "Stevenage": {"ovr": 53, "colors": ["#E30613", "#FFFFFF"]},
    "Shrewsbury Town II": {"ovr": 50, "colors": ["#005CA9", "#FFFFFF"]},

    # ANGLIA - Premier League
    "Manchester City": {"ovr": 87, "colors": ["#6CABDD", "#FFFFFF"]},
    "Arsenal": {"ovr": 86, "colors": ["#DB0007", "#FFFFFF"]},
    "Liverpool": {"ovr": 85, "colors": ["#C8102E", "#00A398", "#FFFFFF"]},
    "Chelsea": {"ovr": 82, "colors": ["#034694", "#FFFFFF"]},
    "Newcastle United": {"ovr": 80, "colors": ["#241F20", "#FFFFFF"]},
    "Tottenham Hotspur": {"ovr": 80, "colors": ["#132257", "#FFFFFF"]},
    "Aston Villa": {"ovr": 79, "colors": ["#670E36", "#95BFE5"]},
    "Manchester United": {"ovr": 79, "colors": ["#DA291C", "#FBE122", "#000000"]},
    "Brighton & Hove Albion": {"ovr": 76, "colors": ["#0057B8", "#FFFFFF"]},
    "Nottingham Forest": {"ovr": 76, "colors": ["#E53233", "#FFFFFF"]},
    "Crystal Palace": {"ovr": 75, "colors": ["#1B458F", "#C4122E"]},
    "Fulham": {"ovr": 75, "colors": ["#000000", "#FFFFFF"]},
    "Bournemouth": {"ovr": 74, "colors": ["#DA291C", "#000000"]},
    "Everton": {"ovr": 74, "colors": ["#003399", "#FFFFFF"]},
    "Brentford": {"ovr": 73, "colors": ["#E30613", "#FFFFFF"]},
    "Leeds United": {"ovr": 71, "colors": ["#FFCD00", "#FFFFFF"]},
    "Sunderland": {"ovr": 68, "colors": ["#EB172B", "#FFFFFF", "#000000"]},
    "Coventry City": {"ovr": 66, "colors": ["#75BFE5", "#FFFFFF"]},
    "Ipswich Town": {"ovr": 65, "colors": ["#3B5BA7", "#FFFFFF"]},
    "Hull City": {"ovr": 64, "colors": ["#F6A800", "#000000"]},

    # NIEMCY - 2. Bundesliga
    "VfL Wolfsburg": {"ovr": 71, "colors": ["#005CA9", "#FFFFFF"]},
    "1. FC Heidenheim": {"ovr": 66, "colors": ["#005CA9", "#FFFFFF"]},
    "VfL Bochum": {"ovr": 66, "colors": ["#005CA9", "#FFFFFF"]},
    "FC St. Pauli": {"ovr": 65, "colors": ["#005CA9", "#FFFFFF"]},
    "Hertha BSC": {"ovr": 65, "colors": ["#005CA9", "#FFFFFF"]},
    "Holstein Kiel": {"ovr": 65, "colors": ["#005CA9", "#FFFFFF"]},
    "1. FC Kaiserslautern": {"ovr": 64, "colors": ["#005CA9", "#FFFFFF"]},
    "Hannover 96": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "1. FC Magdeburg": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Karlsruher SC": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "1. FC Nürnberg": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Arminia Bielefeld": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Darmstadt 98": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "SpVgg Greuther Fürth": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Dynamo Dresden": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Eintracht Braunschweig": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "VfL Osnabrück": {"ovr": 54, "colors": ["#005CA9", "#FFFFFF"]},
    "Energie Cottbus": {"ovr": 53, "colors": ["#005CA9", "#FFFFFF"]},

    # NIEMCY - Bundesliga
    "Bayern Monachium": {"ovr": 88, "colors": ["#DC052D", "#FFFFFF"]},
    "Bayer Leverkusen": {"ovr": 83, "colors": ["#E32221", "#000000"]},
    "Borussia Dortmund": {"ovr": 82, "colors": ["#FDE100", "#000000"]},
    "RB Lipsk": {"ovr": 81, "colors": ["#FFFFFF", "#E2001A"]},
    "VfB Stuttgart": {"ovr": 78, "colors": ["#FFFFFF", "#E32221"]},
    "Eintracht Frankfurt": {"ovr": 76, "colors": ["#E1000F", "#000000", "#FFFFFF"]},
    "Borussia Mönchengladbach": {"ovr": 73, "colors": ["#000000", "#FFFFFF", "#008F39"]},
    "SC Freiburg": {"ovr": 73, "colors": ["#000000", "#FFFFFF", "#E30613"]},
    "1. FSV Mainz 05": {"ovr": 72, "colors": ["#C8102E", "#FFFFFF"]},
    "Werder Brema": {"ovr": 71, "colors": ["#1D9E4A", "#FFFFFF"]},
    "TSG Hoffenheim": {"ovr": 70, "colors": ["#005CA9", "#FFFFFF"]},
    "Union Berlin": {"ovr": 70, "colors": ["#E30613", "#FFFFFF"]},
    "FC Augsburg": {"ovr": 68, "colors": ["#BA0C2F", "#FFFFFF", "#008F39"]},
    "1. FC Köln": {"ovr": 67, "colors": ["#ED1C24", "#FFFFFF"]},
    "Hamburger SV": {"ovr": 66, "colors": ["#005CA9", "#FFFFFF", "#000000"]},
    "Schalke 04": {"ovr": 65, "colors": ["#004B9B", "#FFFFFF"]},
    "SC Paderborn 07": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "SV Elversberg": {"ovr": 61, "colors": ["#000000", "#FFFFFF"]},

    # FRANCJA - Ligue 1
    "Paris Saint-Germain": {"ovr": 87, "colors": ["#004170", "#DA291C", "#FFFFFF"]},
    "Olympique Marsylia": {"ovr": 79, "colors": ["#2FAEE0", "#FFFFFF"]},
    "AS Monaco": {"ovr": 78, "colors": ["#E30613", "#FFFFFF"]},
    "Olympique Lyon": {"ovr": 77, "colors": ["#004D98", "#FFFFFF", "#E30613"]},
    "LOSC Lille": {"ovr": 76, "colors": ["#E30613", "#003DA5", "#FFFFFF"]},
    "OGC Nice": {"ovr": 74, "colors": ["#E30613", "#000000"]},
    "RC Lens": {"ovr": 74, "colors": ["#FFD700", "#E30613"]},
    "Stade Rennais": {"ovr": 73, "colors": ["#E30613", "#000000"]},
    "RC Strasbourg": {"ovr": 70, "colors": ["#005CA9", "#FFFFFF"]},
    "Stade Brestois": {"ovr": 70, "colors": ["#E30613", "#FFFFFF"]},

    # FRANCJA - Ligue 2
    "Paris FC": {"ovr": 65, "colors": ["#005CA9", "#FFFFFF"]},
    "Troyes": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Guingamp": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Bastia": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Clermont Foot": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Amiens": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Caen": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Grenoble": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Ajaccio": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "Pau FC": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Rodez": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Annecy": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},
    "Laval": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},
    "Red Star": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},
    "Dunkerque": {"ovr": 54, "colors": ["#005CA9", "#FFFFFF"]},
    "Martigues": {"ovr": 53, "colors": ["#005CA9", "#FFFFFF"]},
    "Boulogne": {"ovr": 52, "colors": ["#005CA9", "#FFFFFF"]},
    "Bourg-Péronnas": {"ovr": 51, "colors": ["#005CA9", "#FFFFFF"]},

    # HISZPANIA - La Liga
    "Real Madryt": {"ovr": 89, "colors": ["#FFFFFF", "#00529F", "#FEBE10"]},
    "FC Barcelona": {"ovr": 88, "colors": ["#A50044", "#004D98", "#EDBB00"]},
    "Atlético Madryt": {"ovr": 84, "colors": ["#CB3524", "#FFFFFF", "#1D428A"]},
    "Athletic Bilbao": {"ovr": 78, "colors": ["#EE2523", "#FFFFFF", "#000000"]},
    "Villarreal": {"ovr": 78, "colors": ["#FEE900", "#00529F"]},
    "Real Sociedad": {"ovr": 76, "colors": ["#0067B1", "#FFFFFF"]},
    "Real Betis": {"ovr": 75, "colors": ["#00954C", "#FFFFFF"]},
    "Sevilla": {"ovr": 74, "colors": ["#D00000", "#FFFFFF"]},
    "Girona": {"ovr": 73, "colors": ["#CD2534", "#FFFFFF", "#000000"]},
    "Valencia": {"ovr": 72, "colors": ["#FFFFFF", "#F58220", "#000000"]},
    "Celta Vigo": {"ovr": 71, "colors": ["#8CCEF1", "#FFFFFF"]},
    "Osasuna": {"ovr": 70, "colors": ["#D50032", "#003B70"]},
    "Getafe": {"ovr": 69, "colors": ["#005999", "#FFFFFF"]},
    "Mallorca": {"ovr": 69, "colors": ["#E30613", "#000000"]},
    "Rayo Vallecano": {"ovr": 69, "colors": ["#FFFFFF", "#E30613"]},
    "Alavés": {"ovr": 67, "colors": ["#005CA9", "#FFFFFF"]},
    "Espanyol": {"ovr": 66, "colors": ["#007FC8", "#FFFFFF"]},
    "Elche": {"ovr": 65, "colors": ["#008F39", "#FFFFFF"]},
    "Levante": {"ovr": 65, "colors": ["#E30613", "#005CA9"]},
    "Real Oviedo": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},

    # HISZPANIA - La Liga 2
    "Deportivo La Coruña": {"ovr": 66, "colors": ["#0070B8", "#FFFFFF", "#003B70"]},
    "Las Palmas": {"ovr": 66, "colors": ["#F4D03F", "#003B70"]},
    "Almería": {"ovr": 65, "colors": ["#E30613", "#FFFFFF"]},
    "Racing Santander": {"ovr": 64, "colors": ["#008F39", "#FFFFFF"]},
    "Sporting Gijón": {"ovr": 64, "colors": ["#E30613", "#FFFFFF"]},
    "Cádiz CF": {"ovr": 65, "colors": ["#F4D03F", "#003B70"]},

    # PORTUGALIA - Liga Portugal
    "SL Benfica": {"ovr": 83, "colors": ["#E30613", "#FFFFFF"]},
    "FC Porto": {"ovr": 82, "colors": ["#0050A4", "#FFFFFF"]},
    "Sporting CP": {"ovr": 82, "colors": ["#00843D", "#FFFFFF"]},
    "Sporting Braga": {"ovr": 74, "colors": ["#E30613", "#FFFFFF"]},
    "Vitória Guimarães": {"ovr": 69, "colors": ["#000000", "#FFFFFF"]},
    "Gil Vicente": {"ovr": 65, "colors": ["#005CA9", "#FFFFFF"]},
    "Famalicão": {"ovr": 64, "colors": ["#005CA9", "#FFFFFF"]},
    "Casa Pia": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Estoril": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Arouca": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Moreirense": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Rio Ave": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Santa Clara": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Estrela Amadora": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Nacional": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "AVS": {"ovr": 59, "colors": ["#005CA9", "#FFFFFF"]},
    "Alverca": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Tondela": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},

    # PORTUGALIA - Liga Portugal 2
    "Farense": {"ovr": 60, "colors": ["#000000", "#FFFFFF"]},
    "Marítimo": {"ovr": 60, "colors": ["#00843D", "#E30613"]},
    "Leixões": {"ovr": 58, "colors": ["#E30613", "#FFFFFF"]},
    "Penafiel": {"ovr": 57, "colors": ["#E30613", "#FFFFFF"]},

    # HOLANDIA - Eredivisie
    "PSV Eindhoven": {"ovr": 81, "colors": ["#F00000", "#FFFFFF"]},
    "Ajax Amsterdam": {"ovr": 80, "colors": ["#D2122E", "#FFFFFF"]},
    "Feyenoord": {"ovr": 78, "colors": ["#E30613", "#FFFFFF", "#000000"]},
    "AZ Alkmaar": {"ovr": 73, "colors": ["#ED1C24", "#FFFFFF"]},
    "FC Twente": {"ovr": 71, "colors": ["#E30613", "#FFFFFF"]},
    "FC Utrecht": {"ovr": 70, "colors": ["#E30613", "#FFFFFF"]},
    "SC Heerenveen": {"ovr": 70, "colors": ["#005CA9", "#FFFFFF"]},
    "NEC Nijmegen": {"ovr": 69, "colors": ["#E30613", "#008F39"]},

    # WŁOCHY - Serie A
    "Inter Mediolan": {"ovr": 86, "colors": ["#0068A8", "#000000"]},
    "SSC Napoli": {"ovr": 83, "colors": ["#12A0D7", "#FFFFFF"]},
    "AC Milan": {"ovr": 82, "colors": ["#FB090B", "#000000"]},
    "Juventus": {"ovr": 82, "colors": ["#000000", "#FFFFFF"]},
    "Atalanta": {"ovr": 80, "colors": ["#1E71B8", "#000000"]},
    "AS Roma": {"ovr": 79, "colors": ["#8E1F2F", "#F0BC42", "#FFFFFF"]},
    "Lazio": {"ovr": 76, "colors": ["#87CEEB", "#FFFFFF"]},
    "Bologna": {"ovr": 75, "colors": ["#1E1E1E", "#A6192E", "#FFFFFF"]},
    "Fiorentina": {"ovr": 75, "colors": ["#482E92", "#FFFFFF"]},
    "Torino": {"ovr": 71, "colors": ["#8A1538", "#FFFFFF"]},
    "Como": {"ovr": 69, "colors": ["#005CA9", "#FFFFFF"]},
    "Genoa": {"ovr": 68, "colors": ["#005CA9", "#FFFFFF"]},
    "Udinese": {"ovr": 68, "colors": ["#005CA9", "#FFFFFF"]},
    "Cagliari": {"ovr": 66, "colors": ["#005CA9", "#FFFFFF"]},
    "Hellas Verona": {"ovr": 66, "colors": ["#005CA9", "#FFFFFF"]},
    "Parma": {"ovr": 66, "colors": ["#005CA9", "#FFFFFF"]},
    "Lecce": {"ovr": 65, "colors": ["#005CA9", "#FFFFFF"]},
    "Empoli": {"ovr": 64, "colors": ["#005CA9", "#FFFFFF"]},
    "Cremonese": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Pisa": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},

    # BELGIA - Pro League
    "Club Brugge": {"ovr": 78, "colors": ["#005CA9", "#000000"]},
    "Union Saint-Gilloise": {"ovr": 76, "colors": ["#005CA9", "#F4C300"]},
    "Anderlecht": {"ovr": 73, "colors": ["#4B2E83", "#FFFFFF"]},
    "Genk": {"ovr": 71, "colors": ["#0055A5", "#FFFFFF"]},
    "KAA Gent": {"ovr": 70, "colors": ["#1E4D8F", "#FFFFFF"]},
    "Antwerp": {"ovr": 68, "colors": ["#005CA9", "#FFFFFF"]},
    "Standard Liège": {"ovr": 66, "colors": ["#005CA9", "#FFFFFF"]},
    "Cercle Brugge": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Charleroi": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "KV Mechelen": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "STVV": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Westerlo": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "OH Leuven": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Kortrijk": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "RWDM": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "Dender": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},

    # TURCJA - Süper Lig
    "Galatasaray": {"ovr": 80, "colors": ["#A90432", "#FDB912"]},
    "Fenerbahçe": {"ovr": 79, "colors": ["#002D62", "#F7D117"]},
    "Beşiktaş": {"ovr": 74, "colors": ["#000000", "#FFFFFF"]},
    "Trabzonspor": {"ovr": 72, "colors": ["#76232F", "#5DADE2"]},
    "Başakşehir": {"ovr": 68, "colors": ["#005CA9", "#FFFFFF"]},
    "Samsunspor": {"ovr": 65, "colors": ["#005CA9", "#FFFFFF"]},
    "Antalyaspor": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Kasımpaşa": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Konyaspor": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Kayserispor": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Sivasspor": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Alanyaspor": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Gaziantep FK": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Rizespor": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Göztepe": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Eyüpspor": {"ovr": 59, "colors": ["#005CA9", "#FFFFFF"]},
    "Gençlerbirliği": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Kocaelispor": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},

    # SZKOCJA - Premiership
    "Celtic": {"ovr": 78, "colors": ["#008A45", "#FFFFFF"]},
    "Rangers": {"ovr": 76, "colors": ["#003DA5", "#FFFFFF", "#FFCD00"]},
    "Aberdeen": {"ovr": 66, "colors": ["#005CA9", "#FFFFFF"]},
    "Hearts": {"ovr": 65, "colors": ["#005CA9", "#FFFFFF"]},
    "Hibernian": {"ovr": 64, "colors": ["#005CA9", "#FFFFFF"]},
    "Dundee United": {"ovr": 61, "colors": ["#E30613", "#FFFFFF"]},
    "St Mirren": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Motherwell": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Kilmarnock": {"ovr": 59, "colors": ["#005CA9", "#FFFFFF"]},
    "Dundee": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Ross County": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "St Johnstone": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},

    # AUSTRIA - Bundesliga
    "Red Bull Salzburg": {"ovr": 76, "colors": ["#FFFFFF", "#E30613", "#004C97"]},
    "Sturm Graz": {"ovr": 70, "colors": ["#000000", "#FFFFFF"]},
    "Rapid Wiedeń": {"ovr": 68, "colors": ["#008F39", "#FFFFFF"]},
    "Austria Wiedeń": {"ovr": 65, "colors": ["#4B2E83", "#FFFFFF"]},
    "LASK": {"ovr": 64, "colors": ["#005CA9", "#FFFFFF"]},
    "Wolfsberger AC": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "WSG Tirol": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Altach": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "Blau-Weiß Linz": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "Hartberg": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "Grazer AK": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Rheindorf Altach II/Junior": {"ovr": 52, "colors": ["#005CA9", "#FFFFFF"]},

    # SZWAJCARIA - Super League
    "Young Boys": {"ovr": 74, "colors": ["#F5D000", "#000000"]},
    "FC Basel": {"ovr": 72, "colors": ["#E30613", "#000000"]},
    "FC Zurich": {"ovr": 65, "colors": ["#FFFFFF", "#000000", "#005CA9"]},
    "Servette": {"ovr": 64, "colors": ["#005CA9", "#FFFFFF"]},
    "Lugano": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "St. Gallen": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Grasshopper": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Lucerne": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Sion": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Winterthur": {"ovr": 57, "colors": ["#0068A8", "#000000"]},
    "Thun": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Yverdon": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},

    # DANIA - Superliga
    "FC Kopenhaga": {"ovr": 71, "colors": ["#FFFFFF", "#005CA9"]},
    "Midtjylland": {"ovr": 69, "colors": ["#000000", "#D71920"]},
    "Brøndby": {"ovr": 65, "colors": ["#005CA9", "#F4C300"]},
    "Nordsjælland": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "AGF Aarhus": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Silkeborg": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Randers": {"ovr": 59, "colors": ["#005CA9", "#FFFFFF"]},
    "AaB": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Viborg": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Vejle": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "Sønderjyske": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Hvidovre": {"ovr": 53, "colors": ["#005CA9", "#FFFFFF"]},

    # CZECHY - Czech First League
    "Slavia Praga": {"ovr": 74, "colors": ["#D71920", "#FFFFFF"]},
    "Sparta Praga": {"ovr": 73, "colors": ["#AC1E2D", "#F4C300"]},
    "Viktoria Pilzno": {"ovr": 69, "colors": ["#005CA9", "#FFFFFF"]},
    "Banik Ostrawa": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Slovan Liberec": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Sigma Ołomuniec": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Slovácko": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Mladá Boleslav": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Sparta Praga B": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Bohemians 1905": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Jablonec": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "Hradec Králové": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Teplice": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},
    "Zlín": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},
    "Karviná": {"ovr": 54, "colors": ["#005CA9", "#FFFFFF"]},
    "Pardubice": {"ovr": 54, "colors": ["#005CA9", "#FFFFFF"]},

    # GRECJA - Super League
    "Olympiakos": {"ovr": 76, "colors": ["#E30613", "#FFFFFF"]},
    "PAOK": {"ovr": 73, "colors": ["#000000", "#FFFFFF"]},
    "AEK Ateny": {"ovr": 71, "colors": ["#F4C300", "#000000"]},
    "Panathinaikos": {"ovr": 68, "colors": ["#008F39", "#FFFFFF"]},
    "Aris Saloniki": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Asteras Tripolis": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "OFI Kreta": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "Atromitos": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Panetolikos": {"ovr": 56, "colors": ["#005CA9", "#FFFFFF"]},
    "Volos": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},
    "Kifisia": {"ovr": 54, "colors": ["#005CA9", "#FFFFFF"]},
    "Lamia": {"ovr": 54, "colors": ["#005CA9", "#FFFFFF"]},
    "Levadiakos": {"ovr": 53, "colors": ["#005CA9", "#FFFFFF"]},
    "Panserraikos": {"ovr": 53, "colors": ["#005CA9", "#FFFFFF"]},

    # BRAZYLIA - Série A
    "Flamengo": {"ovr": 82, "colors": ["#000000", "#E30613"]},
    "Palmeiras": {"ovr": 81, "colors": ["#006437", "#FFFFFF"]},
    "Atlético Mineiro": {"ovr": 76, "colors": ["#000000", "#FFFFFF"]},
    "Botafogo": {"ovr": 76, "colors": ["#000000", "#FFFFFF"]},
    "São Paulo": {"ovr": 76, "colors": ["#FFFFFF", "#000000", "#E30613"]},
    "Corinthians": {"ovr": 75, "colors": ["#FFFFFF", "#000000"]},
    "Grêmio": {"ovr": 74, "colors": ["#0099CC", "#000000", "#FFFFFF"]},
    "Internacional": {"ovr": 74, "colors": ["#E30613", "#FFFFFF"]},
    "Fluminense": {"ovr": 73, "colors": ["#7B1E3B", "#00843D", "#FFFFFF"]},
    "Cruzeiro": {"ovr": 72, "colors": ["#003DA5", "#FFFFFF"]},
    "Santos": {"ovr": 70, "colors": ["#FFFFFF", "#000000"]},
    "Bahia": {"ovr": 68, "colors": ["#005CA9", "#E30613", "#FFFFFF"]},
    "Fortaleza": {"ovr": 68, "colors": ["#005CA9", "#E30613", "#FFFFFF"]},
    "Vasco da Gama": {"ovr": 68, "colors": ["#000000", "#FFFFFF", "#E30613"]},
    "Athletico Paranaense": {"ovr": 67, "colors": ["#E30613", "#000000", "#FFFFFF"]},
    "Bragantino": {"ovr": 67, "colors": ["#FFFFFF", "#E30613", "#000000"]},
    "Vitória": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Cuiabá": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Juventude": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Criciúma": {"ovr": 59, "colors": ["#005CA9", "#FFFFFF"]},

    # ARGENTYNA - Liga Profesional
    "River Plate": {"ovr": 82, "colors": ["#FFFFFF", "#E30613"]},
    "Boca Juniors": {"ovr": 81, "colors": ["#003B70", "#F4C300"]},
    "Racing Club": {"ovr": 74, "colors": ["#0066B3", "#FFFFFF"]},
    "Talleres": {"ovr": 71, "colors": ["#005CA9", "#FFFFFF"]},
    "Vélez Sarsfield": {"ovr": 71, "colors": ["#005CA9", "#FFFFFF"]},
    "Estudiantes": {"ovr": 70, "colors": ["#005CA9", "#FFFFFF"]},
    "Independiente": {"ovr": 70, "colors": ["#005CA9", "#FFFFFF"]},
    "San Lorenzo": {"ovr": 68, "colors": ["#003B70", "#E30613"]},
    "Argentinos Juniors": {"ovr": 67, "colors": ["#005CA9", "#FFFFFF"]},
    "Rosario Central": {"ovr": 67, "colors": ["#005CA9", "#FFFFFF"]},
    "Lanús": {"ovr": 65, "colors": ["#005CA9", "#FFFFFF"]},
    "Newell's Old Boys": {"ovr": 65, "colors": ["#005CA9", "#FFFFFF"]},
    "Huracán": {"ovr": 64, "colors": ["#005CA9", "#FFFFFF"]},
    "Defensa y Justicia": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Belgrano": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Banfield": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Gimnasia La Plata": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Tigre": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Central Córdoba": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Godoy Cruz": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},
    "Instituto": {"ovr": 59, "colors": ["#005CA9", "#FFFFFF"]},
    "Platense": {"ovr": 59, "colors": ["#005CA9", "#FFFFFF"]},
    "Atlético Tucumán": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Barracas Central": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Independiente Rivadavia": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Unión": {"ovr": 58, "colors": ["#005CA9", "#FFFFFF"]},
    "Sarmiento": {"ovr": 57, "colors": ["#005CA9", "#FFFFFF"]},
    "Deportivo Riestra": {"ovr": 55, "colors": ["#005CA9", "#FFFFFF"]},

    # MEKSYK - Liga MX
    "Club América": {"ovr": 80, "colors": ["#F4C300", "#003B70"]},
    "Monterrey": {"ovr": 78, "colors": ["#005CA9", "#FFFFFF"]},
    "Tigres UANL": {"ovr": 78, "colors": ["#F4C300", "#003B70"]},
    "Chivas Guadalajara": {"ovr": 74, "colors": ["#E30613", "#FFFFFF", "#003B70"]},
    "Cruz Azul": {"ovr": 74, "colors": ["#005CA9", "#FFFFFF"]},
    "Toluca": {"ovr": 73, "colors": ["#E30613", "#FFFFFF"]},
    "Pumas UNAM": {"ovr": 71, "colors": ["#002B5C", "#F4C300"]},
    "Pachuca": {"ovr": 70, "colors": ["#005CA9", "#FFFFFF"]},
    "León": {"ovr": 68, "colors": ["#005CA9", "#FFFFFF"]},
    "Atlas": {"ovr": 66, "colors": ["#005CA9", "#FFFFFF"]},
    "Santos Laguna": {"ovr": 66, "colors": ["#005CA9", "#FFFFFF"]},
    "Atlético San Luis": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Necaxa": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Puebla": {"ovr": 63, "colors": ["#005CA9", "#FFFFFF"]},
    "Tijuana": {"ovr": 62, "colors": ["#005CA9", "#FFFFFF"]},
    "Juárez": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Mazatlán": {"ovr": 61, "colors": ["#005CA9", "#FFFFFF"]},
    "Querétaro": {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]},

    # USA - MLS
    "Inter Miami": {"ovr": 76, "colors": ["#F7B5CD", "#000000", "#F5A623"]},
    "LAFC": {"ovr": 75, "colors": ["#000000", "#C8C8C8", "#F4C300"]},
    "Columbus Crew": {"ovr": 73, "colors": ["#F4D000", "#000000"]},
    "Philadelphia Union": {"ovr": 72, "colors": ["#002D62", "#B2B2B2", "#F2C94C"]},
    "Seattle Sounders": {"ovr": 72, "colors": ["#5D9741", "#005C5C", "#FFFFFF"]},
    "FC Cincinnati": {"ovr": 71, "colors": ["#003087", "#F58220"]},
    "LA Galaxy": {"ovr": 71, "colors": ["#00245D", "#FFD700", "#FFFFFF"]},
    "Atlanta United": {"ovr": 70, "colors": ["#A6192E", "#000000", "#F4C300"]},
    "Orlando City": {"ovr": 69, "colors": ["#633492", "#FDE192"]},
    "Nashville SC": {"ovr": 68, "colors": ["#F4C300", "#1C2C5B"]},
    "New York City FC": {"ovr": 68, "colors": ["#6CACE4", "#FF5910", "#FFFFFF"]},
    "New York Red Bulls": {"ovr": 68, "colors": ["#ED1B2F", "#FFDB00", "#003DA5"]},
    "Portland Timbers": {"ovr": 68, "colors": ["#004812", "#E57200"]},
    "San Diego FC": {"ovr": 68, "colors": ["#FF5A1F", "#0B1F3A"]},
    "St. Louis City": {"ovr": 66, "colors": ["#D22630", "#0A2240", "#FFFFFF"]},
    "Vancouver Whitecaps": {"ovr": 66, "colors": ["#00245D", "#A5ACAF"]},
    "Charlotte FC": {"ovr": 65, "colors": ["#0085CA", "#000000"]},
    "Minnesota United": {"ovr": 65, "colors": ["#D31145", "#231F20"]},
    "Real Salt Lake": {"ovr": 65, "colors": ["#B30838", "#013A81", "#F4C300"]},
    "Sporting Kansas City": {"ovr": 65, "colors": ["#002B5C", "#91B8D1"]},
    "Chicago Fire": {"ovr": 64, "colors": ["#B31B34", "#4A90E2"]},
    "Toronto FC": {"ovr": 64, "colors": ["#E31837", "#FFFFFF"]},
    "Austin FC": {"ovr": 63, "colors": ["#00B140", "#000000"]},
    "D.C. United": {"ovr": 63, "colors": ["#000000", "#E31837"]},
    "FC Dallas": {"ovr": 63, "colors": ["#E31837", "#0B2341"]},
    "Houston Dynamo": {"ovr": 63, "colors": ["#F68712", "#003B70"]},
    "New England Revolution": {"ovr": 63, "colors": ["#0A2240", "#C8102E"]},
    "CF Montréal": {"ovr": 62, "colors": ["#00529B", "#000000", "#FFFFFF"]},
    "Colorado Rapids": {"ovr": 61, "colors": ["#862633", "#A6192E", "#FFFFFF"]},
    "San Jose Earthquakes": {"ovr": 60, "colors": ["#0066B3", "#000000"]}
}

LEAGUE_COUNTRIES = {
    "Ekstraklasa": "Polska", "1. Liga": "Polska", "2. Liga": "Polska",
    "3. Liga I": "Polska", "3. Liga II": "Polska", "3. Liga III": "Polska", "3. Liga IV": "Polska",
    "Premier League": "Anglia", "Championship": "Anglia", "League One": "Anglia",
    "Bundesliga": "Niemcy", "2. Bundesliga": "Niemcy",
    "Ligue 1": "Francja", "Ligue 2": "Francja",
    "La Liga": "Hiszpania", "La Liga 2": "Hiszpania",
    "Liga Portugal": "Portugalia", "Liga Portugal 2": "Portugalia",
    "Eredivisie": "Holandia", "Serie A": "Włochy", "Belgian Pro League": "Belgia",
    "Süper Lig": "Turcja", "Scottish Premiership": "Szkocja", "Austrian Bundesliga": "Austria",
    "Super League": "Szwajcaria", "Superliga": "Dania", "Czech First League": "Czechy",
    "Greek Super League": "Grecja", "Série A Brazil": "Brazylia", "Liga Profesional": "Argentyna",
    "Liga MX": "Meksyk", "MLS": "USA"
}

LEAGUE_WAGE_MULTIPLIERS = {
    "Premier League": 4.5, "La Liga": 4.0, "Serie A": 3.5, "Bundesliga": 3.5, "Ligue 1": 3.2,
    "Eredivisie": 2.0, "Liga Portugal": 2.0, "Championship": 2.2, "MLS": 1.8, "Süper Lig": 1.8,
    "Ekstraklasa": 1.0, "1. Liga": 0.4, "2. Liga": 0.25, "3. Liga I": 0.15, "3. Liga II": 0.15,
    "3. Liga III": 0.15, "3. Liga IV": 0.15
}

LEAGUE_DEFS = [
    ("Ekstraklasa", ["Lech Poznań", "Legia Warszawa", "Raków Częstochowa", "Jagiellonia Białystok", "Górnik Zabrze", "Pogoń Szczecin", "Cracovia", "Piast Gliwice", "Widzew Łódź", "Wisła Kraków", "Radomiak Radom", "Zagłębie Lubin", "Śląsk Wrocław", "GKS Katowice", "Korona Kielce", "Motor Lublin", "Wisła Płock", "Wieczysta Kraków"]),
    ("1. Liga", ["Chrobry Głogów", "Lechia Gdańsk", "Arka Gdynia", "Ruch Chorzów", "ŁKS Łódź", "Miedź Legnica", "Polonia Warszawa", "Bruk-Bet Termalica Nieciecza", "Puszcza Niepołomice", "Polonia Bytom", "Stal Mielec", "Odra Opole", "Pogoń Grodzisk Mazowiecki", "Stal Rzeszów", "GKS Jastrzębie", "Pogoń Siedlce", "Świt Szczecin", "Wisła Puławy"]),
    ("2. Liga", ["Resovia Rzeszów", "Chojniczanka Chojnice", "Zagłębie Sosnowiec", "Legia II Warszawa", "Kotwica Kołobrzeg", "Rekord Bielsko-Biała", "Zawisza Bydgoszcz", "Avia Świdnik", "Hutnik Kraków", "Lechia Zielona Góra", "Skra Częstochowa", "Sokół Kleczew", "Concordia Piotrków Trybunalski", "Wigry Suwałki", "Radunia Stężyca", "Unia Skierniewice", "Warta Poznań II", "Znicz Biała Piska"]),
    ("3. Liga I", ["Polonia Warszawa II", "Stomil Olsztyn", "Olimpia Elbląg", "Świt Nowy Dwór Mazowiecki", "Huragan Wołomin", "Pelikan Łowicz", "Wisła II Płock", "Mazur Karczew", "Motor II Lublin", "Mławianka Mława", "Sokół Ostróda", "Legionovia Legionowo", "Sparta Świątki", "Ursus Warszawa", "Wkra Żuromin", "Pogoń II Siedlce", "Victoria Sulejówek", "Ząbkovia Ząbki"]),
    ("3. Liga II", ["GKS Bełchatów", "Olimpia Grudziądz", "Warta Gorzów Wlkp.", "Gryf Wejherowo", "Bałtyk Gdynia", "Odra Wodzisław", "Chemik Bydgoszcz", "KKS 1925 Kalisz", "Sokół Pniewy", "Unia Swarzędz", "Elana Toruń", "Polonia Środa Wielkopolska", "Sparta Brodnica", "Włókniarz Kietrz", "Kotwica II Kołobrzeg", "Pogoń Staszów", "Sokół Aleksandrów Łódzki", "Nielba Wągrowiec"]),
    ("3. Liga III", ["Górnik Polkowice", "Lech II Poznań", "Ślęza Wrocław", "Górnik Konin", "Miedź II Legnica", "Polonia Bydgoszcz", "Stal Brzeg", "Victoria Września", "Chrobry II Głogów", "Karkonosze Jelenia Góra", "Piast II Gliwice", "Piast Żmigród", "Warta Sieradz", "Zagłębie II Lubin", "Odra II Opole", "Rakoniewice", "Kotwica Kołobrzeg II", "Unia Turza Śląska"]),
    ("3. Liga IV", ["Cracovia II", "Karpaty Krosno", "Podhale Nowy Targ", "Stal Rzeszów II", "Stal Sanok", "Wieczysta II Kraków", "Górnik II Łęczna", "Hetman Zamość", "Igloopol Dębica", "Motor Lublin II", "Resovia II Rzeszów", "Sokół Sokołów Małopolski", "Wisła Sandomierz", "Wisłoka Dębica", "Czarni Połaniec", "Orzeł Przeworsk", "Wisłok Wiśniowa", "Podlasie Biała Podlaska"]),
    ("Premier League", ["Manchester City", "Arsenal", "Liverpool", "Chelsea", "Newcastle United", "Tottenham Hotspur", "Aston Villa", "Manchester United", "Brighton & Hove Albion", "Nottingham Forest", "Crystal Palace", "Fulham", "Bournemouth", "Everton", "Brentford", "Leeds United", "Sunderland", "Coventry City", "Ipswich Town", "Hull City"]),
    ("Championship", ["West Ham United", "Wolverhampton Wanderers", "Burnley", "Sheffield United", "Southampton", "Middlesbrough", "West Bromwich Albion", "Norwich City", "Blackburn Rovers", "Millwall", "Sheffield Wednesday", "Stoke City", "Swansea City", "Watford", "Derby County", "Portsmouth", "Preston North End", "Queens Park Rangers", "Wrexham", "Oxford United", "Plymouth Argyle", "Cardiff City", "Charlton Athletic", "Bolton Wanderers", "Lincoln City", "Port Vale"]),
    ("League One", ["Birmingham City", "Wigan Athletic", "Blackpool", "Peterborough United", "Barnsley", "Bristol Rovers", "Luton Town", "Reading", "Rotherham United", "Stockport County", "Huddersfield Town", "Leicester City", "Leyton Orient", "Mansfield Town", "Exeter City", "Northampton Town", "Wycombe Wanderers", "Burton Albion", "Shrewsbury Town", "Crawley Town", "Doncaster Rovers", "Bromley", "Cambridge United", "Chesterfield", "Stevenage", "Shrewsbury Town II"]),
    ("Bundesliga", ["Bayern Monachium", "Bayer Leverkusen", "Borussia Dortmund", "RB Lipsk", "VfB Stuttgart", "Eintracht Frankfurt", "Borussia Mönchengladbach", "SC Freiburg", "1. FSV Mainz 05", "Werder Brema", "TSG Hoffenheim", "Union Berlin", "FC Augsburg", "1. FC Köln", "Hamburger SV", "Schalke 04", "SC Paderborn 07", "SV Elversberg"]),
    ("2. Bundesliga", ["VfL Wolfsburg", "1. FC Heidenheim", "VfL Bochum", "FC St. Pauli", "Hertha BSC", "Holstein Kiel", "1. FC Kaiserslautern", "Hannover 96", "1. FC Magdeburg", "Karlsruher SC", "1. FC Nürnberg", "Arminia Bielefeld", "Darmstadt 98", "SpVgg Greuther Fürth", "Dynamo Dresden", "Eintracht Braunschweig", "VfL Osnabrück", "Energie Cottbus"]),
    ("Ligue 1", ["Paris Saint-Germain", "Olympique Marsylia", "AS Monaco", "Olympique Lyon", "LOSC Lille", "OGC Nice", "RC Lens", "Stade Rennais", "RC Strasbourg", "Stade Brestois"]),
    ("Ligue 2", ["Paris FC", "Troyes", "Guingamp", "Bastia", "Clermont Foot", "Amiens", "Caen", "Grenoble", "Ajaccio", "Pau FC", "Rodez", "Annecy", "Laval", "Red Star", "Dunkerque", "Martigues", "Boulogne", "Bourg-Péronnas"]),
    ("La Liga", ["Real Madryt", "FC Barcelona", "Atlético Madryt", "Athletic Bilbao", "Villarreal", "Real Sociedad", "Real Betis", "Sevilla", "Girona", "Valencia", "Celta Vigo", "Osasuna", "Getafe", "Mallorca", "Rayo Vallecano", "Alavés", "Espanyol", "Elche", "Levante", "Real Oviedo"]),
    ("La Liga 2", ["Deportivo La Coruña", "Las Palmas", "Almería", "Racing Santander", "Sporting Gijón", "Cádiz CF"]),
    ("Liga Portugal", ["SL Benfica", "FC Porto", "Sporting CP", "Sporting Braga", "Vitória Guimarães", "Gil Vicente", "Famalicão", "Casa Pia", "Estoril", "Arouca", "Moreirense", "Rio Ave", "Santa Clara", "Estrela Amadora", "Nacional", "AVS", "Alverca", "Tondela"]),
    ("Liga Portugal 2", ["Farense", "Marítimo", "Leixões", "Penafiel"]),
    ("Eredivisie", ["PSV Eindhoven", "Ajax Amsterdam", "Feyenoord", "AZ Alkmaar", "FC Twente", "FC Utrecht", "SC Heerenveen", "NEC Nijmegen"]),
    ("Serie A", ["Inter Mediolan", "SSC Napoli", "AC Milan", "Juventus", "Atalanta", "AS Roma", "Lazio", "Bologna", "Fiorentina", "Torino", "Como", "Genoa", "Udinese", "Cagliari", "Hellas Verona", "Parma", "Lecce", "Empoli", "Cremonese", "Pisa"]),
    ("Belgian Pro League", ["Club Brugge", "Union Saint-Gilloise", "Anderlecht", "Genk", "KAA Gent", "Antwerp", "Standard Liège", "Cercle Brugge", "Charleroi", "KV Mechelen", "STVV", "Westerlo", "OH Leuven", "Kortrijk", "RWDM", "Dender"]),
    ("Süper Lig", ["Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor", "Başakşehir", "Samsunspor", "Antalyaspor", "Kasımpaşa", "Konyaspor", "Kayserispor", "Sivasspor", "Alanyaspor", "Gaziantep FK", "Rizespor", "Göztepe", "Eyüpspor", "Gençlerbirliği", "Kocaelispor"]),
    ("Scottish Premiership", ["Celtic", "Rangers", "Aberdeen", "Hearts", "Hibernian", "Dundee United", "St Mirren", "Motherwell", "Kilmarnock", "Dundee", "Ross County", "St Johnstone"]),
    ("Austrian Bundesliga", ["Red Bull Salzburg", "Sturm Graz", "Rapid Wiedeń", "Austria Wiedeń", "LASK", "Wolfsberger AC", "WSG Tirol", "Altach", "Blau-Weiß Linz", "Hartberg", "Grazer AK", "Rheindorf Altach II/Junior"]),
    ("Super League", ["Young Boys", "FC Basel", "FC Zurich", "Servette", "Lugano", "St. Gallen", "Grasshopper", "Lucerne", "Sion", "Winterthur", "Thun", "Yverdon"]),
    ("Superliga", ["FC Kopenhaga", "Midtjylland", "Brøndby", "Nordsjælland", "AGF Aarhus", "Silkeborg", "Randers", "AaB", "Viborg", "Vejle", "Sønderjyske", "Hvidovre"]),
    ("Czech First League", ["Slavia Praga", "Sparta Praga", "Viktoria Pilzno", "Banik Ostrawa", "Slovan Liberec", "Sigma Ołomuniec", "Slovácko", "Mladá Boleslav", "Sparta Praga B", "Bohemians 1905", "Jablonec", "Hradec Králové", "Teplice", "Zlín", "Karviná", "Pardubice"]),
    ("Greek Super League", ["Olympiakos", "PAOK", "AEK Ateny", "Panathinaikos", "Aris Saloniki", "Asteras Tripolis", "OFI Kreta", "Atromitos", "Panetolikos", "Volos", "Kifisia", "Lamia", "Levadiakos", "Panserraikos"]),
    ("Série A Brazil", ["Flamengo", "Palmeiras", "Atlético Mineiro", "Botafogo", "São Paulo", "Corinthians", "Grêmio", "Internacional", "Fluminense", "Cruzeiro", "Santos", "Bahia", "Fortaleza", "Vasco da Gama", "Athletico Paranaense", "Bragantino", "Vitória", "Cuiabá", "Juventude", "Criciúma"]),
    ("Liga Profesional", ["River Plate", "Boca Juniors", "Racing Club", "Talleres", "Vélez Sarsfield", "Estudiantes", "Independiente", "San Lorenzo", "Argentinos Juniors", "Rosario Central", "Lanús", "Newell's Old Boys", "Huracán", "Defensa y Justicia", "Belgrano", "Banfield", "Gimnasia La Plata", "Tigre", "Central Córdoba", "Godoy Cruz", "Instituto", "Platense", "Atlético Tucumán", "Barracas Central", "Independiente Rivadavia", "Unión", "Sarmiento", "Deportivo Riestra"]),
    ("Liga MX", ["Club América", "Monterrey", "Tigres UANL", "Chivas Guadalajara", "Cruz Azul", "Toluca", "Pumas UNAM", "Pachuca", "León", "Atlas", "Santos Laguna", "Atlético San Luis", "Necaxa", "Puebla", "Tijuana", "Juárez", "Mazatlán", "Querétaro"]),
    ("MLS", ["Inter Miami", "LAFC", "Columbus Crew", "Philadelphia Union", "Seattle Sounders", "FC Cincinnati", "LA Galaxy", "Atlanta United", "Orlando City", "Nashville SC", "New York City FC", "New York Red Bulls", "Portland Timbers", "San Diego FC", "St. Louis City", "Vancouver Whitecaps", "Charlotte FC", "Minnesota United", "Real Salt Lake", "Sporting Kansas City", "Chicago Fire", "Toronto FC", "Austin FC", "D.C. United", "FC Dallas", "Houston Dynamo", "New England Revolution", "CF Montréal", "Colorado Rapids", "San Jose Earthquakes"])
]

FORMATION = [Position.GK, Position.CB, Position.CB, Position.LB, Position.RB, Position.CDM, Position.CM, Position.CAM, Position.LW, Position.RW, Position.ST]

FIRST_NAMES = ["Jan", "Piotr", "Paweł", "Kamil", "Michał", "Jakub", "Kacper", "Mateusz", "Mikołaj", "Szymon", "Filip", "Łukasz", "Maciej", "Dawid", "Tomasz", "Bartek", "Adrian", "Sebastian"]
LAST_NAMES = ["Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski", "Zieliński", "Szymański", "Glik", "Błaszczykowski", "Grosicki", "Bednarek", "Milik", "Piątek", "Frankowski", "Skóraś"]

LUXURY_ITEMS = {
    "watch_rolex": {"name": "⌚ Zegarek Rolex", "cost": 25000, "prestige": 5, "approval": 3, "trust": 0},
    "watch_richard_mille": {"name": "💎 Zegarek Richard Mille", "cost": 300000, "prestige": 25, "approval": -5, "trust": -2},
    "chain": {"name": "⛓️ Złoty Łańcuch z Diamentami", "cost": 80000, "prestige": 12, "approval": -2, "trust": -1},
    "sunglasses": {"name": "🕶️ Designer Sunglasses", "cost": 3000, "prestige": 2, "approval": 2, "trust": 0},
    "car_sport": {"name": "🏎️ Sportowe Auto", "cost": 120000, "prestige": 15, "approval": 8, "trust": -2},
    "car_supercar": {"name": "🔥 Włoski Supercar", "cost": 350000, "prestige": 30, "approval": 5, "trust": -5},
    "yacht": {"name": "🛥️ Jacht Motorowy", "cost": 1500000, "prestige": 60, "approval": -10, "trust": -8},
    "private_jet": {"name": "✈️ Prywatny Odrzutowiec", "cost": 5000000, "prestige": 100, "approval": -20, "trust": -10},
    "apartment": {"name": "🏙️ Penthouse w stolicy", "cost": 500000, "prestige": 35, "approval": 15, "trust": 2},
    "mansion": {"name": "🏰 Rezydencja z Basenem", "cost": 2500000, "prestige": 70, "approval": 10, "trust": 0},
    "chalet": {"name": "⛷️ Luksusowy Domek w Alpejach", "cost": 1200000, "prestige": 45, "approval": 12, "trust": 5},
    "island": {"name": "🏝️ Prywatna Wyspa", "cost": 10000000, "prestige": 150, "approval": -30, "trust": -15},
    "pr_agency": {"name": "📸 Agencja PR", "cost": 80000, "prestige": 20, "approval": 20, "trust": 0},
    "chef": {"name": "👨‍🍳 Osobisty Szef Kuchni", "cost": 60000, "prestige": 10, "approval": 5, "trust": 2},
    "bodyguards": {"name": "🛡️ Prywatna Ochrona 24/7", "cost": 100000, "prestige": 15, "approval": 0, "trust": 10},
    "charity_fund": {"name": "🤝 Założenie Fundacji Charytatywnej", "cost": 200000, "prestige": 40, "approval": 50, "trust": 30}
}

SPONSORS = [
    {"id": "local_gym", "name": "🏋️‍♂️ Siłownia Lokalna", "req_prestige": 0, "pay": 1500, "desc": "Wymaga 0 pkt Prestiżu"},
    {"id": "energy_drink", "name": "⚡ Nitro Drink", "req_prestige": 5, "pay": 3000, "desc": "Wymaga 5 pkt Prestiżu"},
    {"id": "betting_app", "name": "🎰 BetWin (Bukmacher)", "req_prestige": 8, "pay": 4500, "desc": "Wymaga 8 pkt Prestiżu"},
    {"id": "nike", "name": "⚡ Nike Pro", "req_prestige": 10, "pay": 5000, "desc": "Wymaga 10 pkt Prestiżu"},
    {"id": "puma", "name": "🐆 Puma Football", "req_prestige": 15, "pay": 8000, "desc": "Wymaga 15 pkt Prestiżu"},
    {"id": "adidas", "name": "🔥 Adidas Elite", "req_prestige": 25, "pay": 18000, "desc": "Wymaga 25 pkt Prestiżu"},
    {"id": "beats", "name": "🎧 Beats by Dre", "req_prestige": 35, "pay": 25000, "desc": "Wymaga 35 pkt Prestiżu"},
    {"id": "pepsi", "name": "🥤 Pepsi Global", "req_prestige": 45, "pay": 40000, "desc": "Wymaga 45 pkt Prestiżu"},
    {"id": "redbull", "name": "🐂 Red Bull Energy", "req_prestige": 50, "pay": 50000, "desc": "Wymaga 50 pkt Prestiżu"},
    {"id": "mercedes", "name": "⭐ Mercedes-Benz", "req_prestige": 65, "pay": 80000, "desc": "Wymaga 65 pkt Prestiżu"},
    {"id": "rolex", "name": "⌚ Rolex Brand Ambassador", "req_prestige": 80, "pay": 120000, "desc": "Wymaga 80 pkt Prestiżu"},
    {"id": "apple", "name": "🍏 Apple Tech Partner", "req_prestige": 90, "pay": 200000, "desc": "Wymaga 90 pkt Prestiżu"},
    {"id": "crypto_giant", "name": "🪙 CryptoExchange Global", "req_prestige": 95, "pay": 350000, "desc": "Wymaga 95 pkt Prestiżu"}
]

SOCIAL_DATABASE = {
    "authors": {
        "journalists": ["Meczyki_PL", "FabrizioRomano_PL", "PrawdaFutbolu", "CanalPlusSport", "Weszlo_Vibe", "Insider_Sportowy"],
        "fans": ["Kibic_123", "Ultras_99", "Janusz_Klika", "Kibic_Malkontent", "StrefaKibica", "Fanatyk_Klubu"],
        "trolls": ["Troll_Futbolowy", "Krytyk_Trybun", "Futbol_Bez_Cenzury", "Złamana_Kość", "HaterNumberOne"],
        "celebrity_media": ["Paparazzi_PL", "Moda_I_Sport", "Celeb_Football", "Styl_Pilkarza"]
    },
    "hooks": ["O rany...", "Niewiarygodne!", "Słuchajcie to:", "SZOK!", "Każdy o tym mówi:", "Oficjalnie:", "Ależ info!"],
    "slangs": ["absolute banger", "masakra", "totalna patologia", "czysta poezja", "szacuneczek", "nieporozumienie", "klasa światowa", "liga okręgowa vibes"],
    "hashtags": ["#pilkanozna", "#transfery", "#mecz", "#gol", "#drama", "#sport", "#ekstraklasa", "#championsleague", "#gwiazda"],
    "categories": {
        "goal": {"cores": ["niszczy defensywę rywali w genialnym stylu!", "pakuje piłę do siatki i cały stadion szaleje!", "strzela bramkę marzenie, o której będą mówić wszyscy.", "wykańcza akcję jak profesjonalista z najwyższej półki."], "emojis": ["⚽😍", "🔥", "🚀", "💪", "🤯", "👑", "⚡"]},
        "bad_match": {"cores": ["dzisiaj totalnie bez formy i zagrał piach.", "notuje mnóstwo strat i wygląda na kompletnie zagubionego.", "chyba zapomniał butów piłkarskich na ten mecz...", "czas najwyższy na dłuższą ławkę rezerwowych."], "emojis": ["🤡", "📉", "🥱", "🤦‍♂️", "👀", "❌"]},
        "transfer": {"cores": ["oficjalnie zmienia barwy klubowe! Wielki ruch.", "pakuje walizki i podpiera nowy, gigantyczny kontrakt!", "zaskakuje wszystkich i wybiera nowy kierunek kariery."], "emojis": ["🔥", "🚨", "💼", "✈️", "🤝", "⭐"]},
        "luxury": {"cores": ["szaleje na zakupy i kupuje nową brykę za miliony!", "chwali się wakacjami w ekskluzywnym kurorcie z rajskiej wyspy.", "pokazuje swój nowy, ociekający złotem zegarek."], "emojis": ["💸", "🏎️", "🔥", "📸", "💎", "😎"]}
    },
    "reply_templates": ["Chyba Cię poniosło XD", "Przecież to drewno, o czym Ty piszesz?", "Zupełnie się nie zgadzam, w poprzednim meczu grał świetnie.", "Ty chyba oglądałeś inne spotkanie 💀", "Fakt, nie zmyślam. 100% racji.", "Haters gonna hate 😎", "Zobaczymy co powiesz w następnej kolejce...", "Może i tak, ale statystyki nie kłamią!", "Przez takich jak Ty ten futbol schodzi na psy...", "Złoty człowiek, dajcie mu spokój!"]
}

SOCIAL_REACTIONS = {
    "goal": [("Meczyki_PL", "{name} strzela kapitalną bramkę! Co za trafienie! 🔥"), ("Kibic_123", "Ale dowalił okienko! {name} to król! 👑")],
    "bad_match": [("HaterNumberOne", "{name} dzisiaj kompletnie niewidoczny. Piach 🥱"), ("Troll_Futbolowy", "Kiedy powrót do formy? {name} do zmiany.")],
    "transfer": [("FabrizioRomano_PL", "Here we go! {name} zmienia klub w spektakularnym stylu 🚨"), ("Insider_Sportowy", "Wielkie transferowe manewry wokół {name}. ✈️")],
    "luxury": [("Paparazzi_PL", "{name} szaleje w mieście nową furą za miliony! 🏎️"), ("Celeb_Football", "Styl życia {name} budzi podziw i zazdrość. 💎")]
}

def generate_npc_player(position: Position, base_ovr: int, rng: random.Random, used_numbers: set[int], is_starter: bool = True) -> Player:
    fn, ln = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
    age = rng.randint(17, 34)
    ovr = max(1, base_ovr + rng.randint(-4, 4))
    if age > 30: ovr = max(1, ovr - (age - 30) * 2)
    gk = ovr if position == Position.GK else 1
    attrs = Attributes(pace=ovr, acceleration=ovr, dribbling=ovr, ball_control=ovr, passing=ovr, vision=ovr,
        technique=ovr, positioning=ovr, strength=ovr, stamina=ovr, finishing=ovr, shot_power=ovr, heading=ovr,
        tackling=ovr, marking=ovr, reflexes=gk, handling=gk, diving=gk, kicking=gk)
    potential = max(65, min(95, ovr + (rng.randint(3, 15) if age < 23 else rng.randint(0, 3))))
    candidates = [n for n in range(1, 99) if n not in used_numbers]
    num = candidates[0] if candidates else rng.randint(1, 99)
    used_numbers.add(num)
    p = Player(fn, ln, age, "Polska", position, attrs, potential)
    p.shirt_number = num
    return p

def make_manager(name: str, rng: random.Random) -> Manager:
    return Manager(name, rng.choice(["YOUTH", "EXPERIENCE", "BALANCED"]))

class Game:
    def __init__(self):
        self.rng = random.Random()
        self._league = None
        self.reset()

    def reset(self):
        self.player = None
        self.player_club = None
        self._league = None
        self.leagues: list[League] = []
        self.league_system = None
        self.engines: dict[str, SeasonEngine] = {}
        self.calendar = None
        self.offers = []
        self.news: list[dict[str,Any]] = []
        self.social_feed: list[dict[str,Any]] = []
        self.match_history: list[dict[str,Any]] = []
        self.season_history: list[dict[str,Any]] = []
        self.career_stats = {"matches":0,"starts":0,"bench":0,"minutes":0,"goals":0,"assists":0,"yellow":0,"red":0}
        self.season_stats = copy.deepcopy(self.career_stats)
        self.training_used = False
        self.pending_season_end = False
        self.pending_transfer_offers = []
        self.cup = None
        self.cup_round = None
        self.europe = {"Liga Mistrzów":None,"Liga Europy":None,"Liga Konferencji":None}
        self.europe_cups = {}
        self.national = {t.value: {"called":False,"matches":0,"goals":0,"assists":0,"lastResult":None} for t in NationalTeamTier}
        self.world_events = []
        self.created = False
        self.is_retired = False

        self.finances = FinancialEngine()
        self.relationships = PlayerRelationship()
        self.perks = copy.deepcopy(DEFAULT_PERKS)
        self.skill_points = 5
        self.last_match_log = []
        self.match_choice_available = False
        self.match_choice_used = False
        self.lifestyle = {"prestige": 0, "owned": []}
        self.trophies = []
        self.team_chemistry = 70
        self.active_sponsor = None

    def _modify_trust(self, val: int):
        self.relationships.manager_trust = max(0, min(100, self.relationships.manager_trust + val))

    def _modify_approval(self, val: int):
        self.relationships.fan_approval = max(0, min(100, self.relationships.fan_approval + val))

    def _build_world(self):
        pol_leagues = []
        for lname, club_names in LEAGUE_DEFS:
            clubs = []
            country = LEAGUE_COUNTRIES.get(lname, "Polska")
            for name in club_names:
                c_info = CLUB_DATA.get(name, {"ovr": 60, "colors": ["#005CA9", "#FFFFFF"]})
                
                c = Club(
                    name=name, 
                    country=country, 
                    strength=c_info["ovr"], 
                    transfer_budget=4_000_000 + c_info["ovr"] * 200_000,
                    colors=c_info["colors"]
                )
                c.set_manager(make_manager("Trener " + name, self.rng))

                used_nums = set()
                for pos in FORMATION:
                    c.add_player(generate_npc_player(pos, c_info["ovr"], self.rng, used_nums, is_starter=True))
                for _ in range(6):
                    c.add_player(generate_npc_player(self.rng.choice(FORMATION), max(1, c_info["ovr"] - 6), self.rng, used_nums, is_starter=False))

                c.recalculate_strength_from_squad()
                clubs.append(c)

            lg = League(lname, country, clubs)
            self.leagues.append(lg)
            if country == "Polska":
                pol_leagues.append(lg)

        self.league_system = LeagueSystem("Polska", pol_leagues, 2, 2)
        self.engines = {league.name: SeasonEngine(league, rng=self.rng) for league in self.leagues}

    def _find_league(self, club):
        for l in self.leagues:
            if club in l.clubs: return l
        return None

    def start(self, first, last, position, age):
        self.reset(); self.created=True
        pos=Position(position); age=int(age)
        base=54 + max(0, min(10, (22-age)//2))
        attrs=Attributes(pace=base,acceleration=base,dribbling=base-2,ball_control=base-2,passing=base-3,vision=base-4,technique=base-1,positioning=base-1,strength=base-2,stamina=base,finishing=base-2,shot_power=base-2,heading=base-4,tackling=base-15,marking=base-18,reflexes=base if pos==Position.GK else 1,handling=base if pos==Position.GK else 1,diving=base if pos==Position.GK else 1,kicking=base if pos==Position.GK else 1)
        
        dyn_potential = max(68, min(88, base + self.rng.randint(10, 20)))
        self.player=Player(first,last,age,"Polska",pos,attrs,potential=dyn_potential)
        self.player.shirt_number = 10 if pos != Position.GK else 1
        self.player.perks = self.perks
        
        self._build_world(); self.calendar=GameCalendar("2026/27")
        self.generate_offers()
        self.add_news("career",f"{self.player.full_name} (#{self.player.shirt_number}) rozpoczyna karierę w wieku {age} lat.")
        self.post_social_feed("transfer")

    def _calc_wage(self, club: Club) -> int:
        league = self._find_league(club)
        league_name = league.name if league else "Ekstraklasa"
        multiplier = LEAGUE_WAGE_MULTIPLIERS.get(league_name, 1.0)
        base_wage = round((club.strength ** 2.05) * 45 / 100)
        return max(500, round(base_wage * multiplier))

    def generate_offers(self):
        target = self.player.ovr
        allclubs = [c for l in self.leagues for c in l.clubs]
        
        suitable_clubs = [c for c in allclubs if abs(c.strength - target) <= 5]
        if not suitable_clubs:
            allclubs.sort(key=lambda c: abs(c.strength - target))
            suitable_clubs = allclubs[:4]
            
        self.rng.shuffle(suitable_clubs)
        selected = suitable_clubs[:4]

        self.offers = [
            {
                "clubId": c.id,
                "club": c.name,
                "league": self._find_league(c).name,
                "ovr": c.strength,
                "wage": self._calc_wage(c)
            } for c in selected
        ]

    def accept_offer(self, club_id):
        found=next((o for o in (self.offers or self.pending_transfer_offers) if o.get("clubId")==club_id or o.get("id")==club_id), None)
        club=next((c for l in self.leagues for c in l.clubs if c.id==club_id or c.name==club_id), None)
        if not club: raise ValueError("Klub nie istnieje")
        
        if self.player_club and self.player in self.player_club.squad:
            self.player_club.remove_player(self.player.id)

        self.player_club=club
        
        used_nums = {getattr(p, 'shirt_number', 0) for p in club.squad if p is not self.player}
        if self.player.shirt_number in used_nums:
            for new_num in range(2, 99):
                if new_num not in used_nums:
                    self.player.shirt_number = new_num
                    break

        club.add_player(self.player)
        self.league=self._find_league(club)
        self.finances.weekly_salary = self._calc_wage(club)
        self.offers=[]
        self.add_news("transfer",f"{self.player.full_name} (#{self.player.shirt_number}) podpisał kontrakt z {club.name}.")
        self.post_social_feed("transfer")
        self.setup_cups()

    @property
    def league(self): return getattr(self, '_league', None)

    @league.setter
    def league(self, v): self._league = v

    def setup_cups(self):
        allclubs=[c for l in self.leagues for c in l.clubs if c.country == "Polska"]
        self.cup=CupEngine("Puchar Polski",allclubs,two_legged=False,rng=self.rng)
        eu_names=["Ajax","Benfica","Celtic","Fenerbahce","Real Sociedad","Fiorentina","PSV","Rangers","Braga","Freiburg","Anderlecht","Basel"]
        eu=[Club(n,"Europa",self.rng.randint(65,82)) for n in eu_names]
        
        for i,c in enumerate(eu):
            used_nums = set()
            for pos in FORMATION: c.add_player(generate_npc_player(pos,c.strength,self.rng,used_nums, is_starter=True))
            c.recalculate_strength_from_squad()
            
        top=sorted(build_table(self.leagues[0]),key=lambda r:r.position)
        pol=[r.club for r in top[:4]]
        pools={"Liga Mistrzów":pol[:1]+eu[:3],"Liga Europy":pol[1:2]+eu[3:7],"Liga Konferencji":pol[2:4]+eu[7:11]}
        self.europe_cups={k:CupEngine(k,v,two_legged=True,rng=self.rng) for k,v in pools.items()}
        self.cup_round=None

    def next_fixture(self):
        if not self.player_club or not self.league or self.pending_season_end: return None
        engine=self.engines.get(self.league.name)
        if not engine or engine.is_finished(): return None
        for f in engine.get_fixtures(engine.current_matchday):
            if f.home is self.player_club or f.away is self.player_club: return f
        return None

    def post_social_feed(self, category: str):
        authors = SOCIAL_DATABASE["authors"]["journalists"] + SOCIAL_DATABASE["authors"]["fans"]
        author = "@" + self.rng.choice(authors)
        
        if category in SOCIAL_DATABASE["categories"]:
            cat_data = SOCIAL_DATABASE["categories"][category]
            hook = self.rng.choice(SOCIAL_DATABASE["hooks"])
            core = self.rng.choice(cat_data["cores"])
            emoji = self.rng.choice(cat_data["emojis"])
            hashtag = self.rng.choice(SOCIAL_DATABASE["hashtags"])
            
            text = f"{hook} {self.player.full_name} {core} {emoji} {hashtag}"
            self.social_feed.insert(0, {"author": author, "text": text, "time": f"Kolejka {self.calendar.matchday if self.calendar else 1}"})
            self.social_feed = self.social_feed[:20]

    def simulate_week(self):
        if self.is_retired: raise ValueError("Kariera została oficjalnie zakończona.")
        if not self.player_club: raise ValueError("Najpierw wybierz klub")
        if self.pending_season_end: raise ValueError("Sezon zakończony — przejdź do decyzji podsumowującej!")

        fixture=self.next_fixture()

        if not fixture or self.engines[self.league.name].is_finished():
            self.pending_season_end = True
            self._prepare_season_end()
            return self.match_payload(None)

        # Migawka statystyk PRZED meczem — potrzebna do policzenia,
        # co konkretnie wydarzyło się w TYM meczu (delta), bo
        # career_stats/season_stats są licznikami narastającymi.
        pre_goals = self.season_stats["goals"]
        pre_assists = self.season_stats["assists"]
        pre_yellow = self.season_stats["yellow"]
        pre_red = self.season_stats["red"]
        match_events: list[str] = []

        self.player.advance_week()
        self.player.rest(days=5)

        # Dynamiczny, realistyczny rozwój potencjału (maks 92)
        if self.player.form > 85 and self.player.potential < 92:
            self.player.potential = min(92, self.player.potential + 1)
        elif self.player.form < 40 and self.player.potential > 65:
            self.player.potential = max(65, self.player.potential - 1)
        
        sponsor_pay = 0
        if self.active_sponsor:
            sp = next((s for s in SPONSORS if s["id"] == self.active_sponsor), None)
            if sp: sponsor_pay = sp["pay"]
            
        self.finances.receive_salary()
        self.finances.balance += sponsor_pay

        player_engine = self.engines[self.league.name]
        results = player_engine.simulate_matchday()
        player_result = next((r for r in results if r.home is self.player_club or r.away is self.player_club), None)

        self.player.perks = self.perks

        sel=select_matchday_squad(self.player_club)
        status="out"
        if any(p.id==self.player.id for p in sel.starting_xi): status="start"
        elif any(p.id==self.player.id for p in sel.bench): status="bench"
        
        # Realistyczny czas spędzony na boisku (10-25 minut z ławki)
        minutes=0
        if not self.player.is_injured:
            if status=="start": minutes=self.rng.randint(65,90)
            elif status=="bench": minutes=self.rng.randint(10,25)

        if minutes:
            self.player.play_match(minutes)
            self.player.apply_form_change(self.rng.choice([-2,0,1,2,4]))
            self.career_stats["matches"]+=1
            self.career_stats["minutes"]+=minutes
            self.season_stats["matches"]+=1
            self.season_stats["minutes"]+=minutes
            if status=="start": 
                self.career_stats["starts"]+=1; self.season_stats["starts"]+=1
            else: 
                self.career_stats["bench"]+=1; self.season_stats["bench"]+=1

            # Skalowanie statystyk meczowych względem spędzonych minut na boisku
            match_factor = minutes / 90.0
            if self.player.position in [Position.ST, Position.LW, Position.RW, Position.CAM]:
                if self.rng.random() < (0.32 * match_factor):
                    self.career_stats["goals"] += 1
                    self.season_stats["goals"] += 1
                    self._modify_trust(4)
                    self._modify_approval(6)
                    self.post_social_feed("goal")
                    match_events.append(f"⚽ GOL! {self.player.full_name} trafia do siatki!")
                elif self.rng.random() < (0.22 * match_factor):
                    self.career_stats["assists"] += 1
                    self.season_stats["assists"] += 1
                    self._modify_trust(2)
                    self._modify_approval(3)
                    match_events.append(f"🎯 ASYSTA! {self.player.full_name} zalicza podanie do gola!")

            if self.rng.random() < (0.12 * match_factor):
                self.career_stats["yellow"] += 1
                self.season_stats["yellow"] += 1
                self.add_news("match", f"🟨 Żółta kartka dla {self.player.full_name} za twardy faul.")
                match_events.append("🟨 Żółta kartka za twardy faul.")
                if self.season_stats["yellow"] % 4 == 0:
                    self.add_news("club", f"🚫 Zawieszenie! Otrzymałeś 4. żółtą kartkę w sezonie i opuścisz następny mecz.")
            elif self.rng.random() < (0.015 * match_factor):
                self.career_stats["red"] += 1
                self.season_stats["red"] += 1
                self.add_news("match", f"🟥 Czerwona kartka! {self.player.full_name} wyleciał z boiska!")
                match_events.append("🟥 Czerwona kartka — wykluczenie z boiska!")
                self._modify_trust(-5)

            if player_result:
                gf=player_result.home_goals if player_result.home is self.player_club else player_result.away_goals
                ga=player_result.away_goals if player_result.home is self.player_club else player_result.home_goals
                if gf>ga: 
                    self.add_news("match",f"Zwycięstwo {self.player_club.name} {gf}:{ga}.")
                    self._modify_approval(2)
                elif gf==ga: 
                    self.add_news("match",f"Remis {self.player_club.name} {gf}:{ga}.")
                else: 
                    self.add_news("match",f"Porażka {self.player_club.name} {gf}:{ga}.")
                    self._modify_approval(-2)
                    if self.rng.random() < 0.3: self.post_social_feed("bad_match")
        else:
            self.add_news("club",f"Nie zagrałeś w kolejce. Trener pozostawił Cię poza boiskiem.")
            match_events.append("🪑 Nie zagrałeś w tej kolejce — trener zostawił Cię poza boiskiem.")
            self._modify_trust(-2)

        if minutes:
            injury=check_for_injury(self.player.condition, rng=self.rng)
            if injury:
                self.player.set_injury(injury)
                self.add_news("injury",f"🚑 Kontuzja: {injury.name}. Przerwa: {injury.weeks_remaining} tyg.")
                match_events.append(f"🚑 Kontuzja: {injury.name} — przerwa {injury.weeks_remaining} tyg.")

        # Delta staje się dostępna dla frontendu (co dokładnie wydarzyło
        # się w TYM meczu, a nie licznik narastający od początku sezonu).
        match_player_goals = self.season_stats["goals"] - pre_goals
        match_player_assists = self.season_stats["assists"] - pre_assists
        match_player_yellow = self.season_stats["yellow"] - pre_yellow
        match_player_red = self.season_stats["red"] - pre_red

        # Jedna interaktywna akcja (/api/match/choice) dostępna na mecz,
        # tylko jeśli gracz faktycznie wystąpił.
        self.match_choice_available = bool(minutes)
        self.match_choice_used = False
        self.match_choice_minutes = minutes
        self.match_choice_status = status

        self.training_used=False
        self._simulate_world_events()
        if self.calendar:
            self.calendar.advance_matchday()
        self._check_national()

        if self.cup and self.calendar.matchday in (6,12,18,24,30,34):
            self.play_cup_round()

        if player_engine.is_finished():
            self.pending_season_end=True
            self._prepare_season_end()

        return self.match_payload(
            player_result,
            player_goals=match_player_goals,
            player_assists=match_player_assists,
            player_yellow=match_player_yellow,
            player_red=match_player_red,
            events=match_events,
            squad_status=status,
            minutes=minutes,
            can_choose=self.match_choice_available,
        )

    def _simulate_world_events(self):
        mday = self.calendar.matchday if self.calendar else 1
        is_transfer_window = (mday in [1, 2, 3, 4, 15, 16, 17, 18])

        if is_transfer_window and self.rng.random() < 0.65:
            all_clubs = [c for l in self.leagues for c in l.clubs if c is not self.player_club]
            c1, c2 = self.rng.sample(all_clubs, 2)
            if c2.squad:
                target_player = self.rng.choice(c2.squad)
                # Prawdziwy transfer botów AI
                c2.remove_player(target_player.id)
                c1.add_player(target_player)
                self.add_news("world", f"🔄 TRANSFER: {target_player.full_name} oficjalnie przeniósł się z {c2.name} do {c1.name}!")
        elif self.rng.random() < 0.25:
            table=build_table(self.league)
            if table and self.rng.random()<0.20:
                leader=table[0].club.name; last=table[-1].club.name
                self.add_news("world",f"🌍 {self.league.name}: {leader} prowadzi w tabeli, a {last} znajduje się w strefie spadkowej.")

    def train(self, focus):
        if self.player and self.player.is_injured:
            raise ValueError(f"{self.player.full_name} jest kontuzjowany i nie może trenować")
        if self.training_used:
            raise ValueError("Trening w tej kolejce został już wykorzystany")
        
        if self.finances.personal_trainer:
            self.player.apply_form_change(2)

        train(self.player, TrainingFocus(focus))
        self.training_used = True
        self.team_chemistry = min(100, self.team_chemistry + 2)
        names = {"TECHNIQUE":"Technika","PHYSICAL":"Fizyczny","SHOOTING":"Strzał","TACTICAL":"Taktyka","RECOVERY":"Regeneracja"}
        self.add_news("training", f"🏋️ Trening: {names.get(focus, focus)}. Kondycja {self.player.condition}, OVR {self.player.ovr}.")

    def play_cup_round(self):
        if not self.cup or self.cup.is_finished: return
        results=self.cup.play_next_round(); self.cup_round=self.cup.rounds_played[-1]
        for r in results:
            if r.tie.home is self.player_club or r.tie.away is self.player_club:
                if r.decided_by_bye: self.add_news("cup",f"🏆 {self.player_club.name} dostał wolny los w Pucharze Polski.")
                else:
                    score=" / ".join(f"{x.home_goals}:{x.away_goals}" for x in r.legs)
                    self.add_news("cup",f"🏆 Puchar Polski: {score}. Awans: {r.winner.name}.")
        if self.cup.is_finished: 
            if self.cup.champion is self.player_club:
                self.trophies.append({"name": "Puchar Polski", "season": self.calendar.season})
                self.add_news("cup",f"🏆 Zwycięstwo! {self.player_club.name} zdobywa Puchar Polski!")
            else:
                self.add_news("cup",f"🏆 Puchar Polski wygrał {self.cup.champion.name}.")

        for name,ec in self.europe_cups.items():
            if not ec.is_finished and self.calendar.matchday in (10,18,26):
                er=ec.play_next_round()
                for tr in er:
                    if tr.tie.home is self.player_club or tr.tie.away is self.player_club:
                        score=" / ".join(f"{x.home_goals}:{x.away_goals}" for x in tr.legs)
                        self.add_news("cup",f"🌍 {name}: {score}. Awans: {tr.winner.name}.")
                if ec.is_finished: 
                    if ec.champion is self.player_club:
                        self.trophies.append({"name": f"Trofeum {name}", "season": self.calendar.season})
                        self.add_news("cup",f"🌟 NIESAMOWITE! {self.player_club.name} wygrywa {name}!")
                    else:
                        self.add_news("cup",f"🌍 {name}: mistrzem został {ec.champion.name}.")

    def _check_national(self):
        if self.player.ovr >= 65 and self.player.form >= 60:
            tier = NationalTeamTier.SENIOR if self.player.age >= 21 else (NationalTeamTier.U21 if self.player.age >= 20 else NationalTeamTier.U19)
            if not self.national[tier.value]["called"]:
                self.national[tier.value]["called"] = True
                self.add_news("national", f"🇵🇱 POWOŁANIE! Zostałeś powołany do Reprezentacji Polski ({tier.value})!")

            if self.calendar.matchday % 4 == 0:
                opponents = ["Niemcy", "Francja", "Hiszpania", "Anglia", "Włochy", "Czechy", "Holandia"]
                opp_name = self.rng.choice(opponents)
                p_goals = self.rng.randint(0, 3)
                o_goals = self.rng.randint(0, 3)
                self.national[tier.value]["matches"] += 1
                result_str = f"Polska {p_goals}:{o_goals} {opp_name}"
                self.national[tier.value]["lastResult"] = result_str
                self.add_news("national", f"🇵🇱 Mecz Reprezentacji: {result_str}. Zagrałeś w tym spotkaniu!")

    def _prepare_season_end(self):
        if not self.league:
            return

        table = build_table(self.league)
        pos = next((i + 1 for i, r in enumerate(table) if r.club is self.player_club), 1)

        if pos == 1:
            self.trophies.append({"name": f"Mistrzostwo ({self.league.name})", "season": self.calendar.season})
            self.add_news("season", f"🥇 MISTRZOSTWO! {self.player_club.name} zdobywa tytuł w {self.league.name}!")
        else:
            self.add_news("season", f"🏁 Sezon zakończony. {self.player_club.name}: {pos}. miejsce w {self.league.name}.")

        if self.season_stats["goals"] >= 15:
            self.trophies.append({"name": "Złoty But Sezonu", "season": self.calendar.season})
            self.finances.balance += 50000
            self.add_news("season", f"👑 NAGRODA: Zdobywasz Złoty But Sezonu za {self.season_stats['goals']} goli! (+50,000 PLN)")

        # SPODEK FORMIE I FIZYCE PO 30. ROKU ŻYCIA
        if self.player.age > 30 and hasattr(self.player, 'attributes'):
            drop = min(3, self.player.age - 30)
            self.player.attributes.pace = max(1, self.player.attributes.pace - drop)
            self.player.attributes.stamina = max(1, self.player.attributes.stamina - drop)

        for l in self.leagues:
            for c in l.clubs:
                retired_count = 0
                used_nums = {getattr(p, 'shirt_number', 0) for p in c.squad}
                new_squad = []

                for p in c.squad:
                    if p is self.player:
                        new_squad.append(p)
                        continue

                    # POPRAWIONE STARZENIE AI BOTÓW (+1 ROK)
                    p.age += 1

                    if p.age > 30 and hasattr(p, 'attributes'):
                        p.attributes.pace = max(1, p.attributes.pace - 2)
                        p.attributes.stamina = max(1, p.attributes.stamina - 2)

                    if p.age >= 35 and self.rng.random() < 0.45:
                        retired_count += 1
                        self.add_news("world", f"👟 {p.full_name} z zespołu {c.name} zakończył karierę w wieku {p.age} lat.")
                    else:
                        new_squad.append(p)

                c.squad = new_squad
                for _ in range(retired_count):
                    c.add_player(generate_npc_player(self.rng.choice(FORMATION), c.strength, self.rng, used_nums, is_starter=False))

        target = self.player.ovr
        all_clubs = [c for l in self.leagues for c in l.clubs if c is not self.player_club]
        suitable = [c for c in all_clubs if abs(c.strength - target) <= 5]
        if not suitable:
            all_clubs.sort(key=lambda c: abs(c.strength - target))
            suitable = all_clubs[:4]

        self.rng.shuffle(suitable)
        selected_clubs = suitable[:4]

        self.pending_transfer_offers = [
            {
                "clubId": c.id,
                "club": c.name,
                "league": self._find_league(c).name if self._find_league(c) else "1. Liga",
                "ovr": c.strength,
                "wage": self._calc_wage(c)
            } for c in selected_clubs
        ]

    def finish_season(self, decision, club_id=None):
        if decision == "retire":
            self.is_retired = True
            self.add_news("career", f"🏁 {self.player.full_name} oficjalnie kończy piłkarską karierę w wieku {self.player.age} lat!")
            return

        old_ovr=self.player.ovr
        delta=apply_season_development(self.player,self.season_stats["minutes"])
        
        # JEDNOSTAROWE STARZENIE DLA GRACZA (+1 ROK - NAPRAWIONO BŁĄD PODWÓJNEGO WIEKU)
        self.player.age += 1

        tables={i:build_table(l) for i,l in enumerate(self.leagues)}
        news=[]
        
        # Awanse i spadki TYLKO w obrębie tego samego kraju
        for tier in range(len(self.leagues)-1):
            upper,lower=self.leagues[tier],self.leagues[tier+1]
            if upper.country == lower.country:
                ut,lt=tables[tier],tables[tier+1]
                relegated=[r.club for r in ut[-2:]]; promoted=[r.club for r in lt[:2]]
                for c in relegated: upper.clubs.remove(c); lower.clubs.append(c)
                for c in promoted: lower.clubs.remove(c); upper.clubs.append(c)
                for c in relegated: news.append(f"🔻 {c.name} spada do {lower.name}.")
                for c in promoted: news.append(f"🔺 {c.name} awansuje do {upper.name}.")

        for l in self.leagues:
            for c in l.clubs: c.recalculate_strength_from_squad(); c.reset_season_stats()
        if decision=="transfer" and club_id:
            target=next((c for l in self.leagues for c in l.clubs if c.id==club_id or c.name==club_id),None)
            if target:
                if self.player in self.player_club.squad:
                    self.player_club.remove_player(self.player.id)
                target.add_player(self.player)
                self.player_club=target
                self.finances.weekly_salary = self._calc_wage(target)

        self.league=self._find_league(self.player_club)
        self.calendar.advance_season()
        self.engines={l.name:SeasonEngine(l,rng=self.rng) for l in self.leagues}
        self.season_history.append({"season":self.calendar.season,"club":self.player_club.name,"ovrBefore":old_ovr,"ovrAfter":self.player.ovr,"minutes":self.season_stats["minutes"],"goals":self.season_stats["goals"],"assists":self.season_stats["assists"]})
        self.add_news("season",f"📈 Rozwój sezonowy: OVR {old_ovr} → {self.player.ovr} ({delta:+d}). Twój wiek: {self.player.age} lat.")
        
        self.skill_points += 2

        for n in news[:6]: self.add_news("world",n)
        self.season_stats=copy.deepcopy({k:0 for k in self.season_stats})
        self.pending_season_end=False; self.pending_transfer_offers=[]; self.training_used=False
        self.setup_cups()

    def add_news(self, typ, text):
        self.news.insert(0,{"type":typ,"text":text,"season":self.calendar.season if self.calendar else "2026/27","matchday":self.calendar.matchday if self.calendar else 1})
        self.news=self.news[:60]

    def add_social(self, author, text):
        self.social_feed.insert(0, {"author": author, "text": text, "time": "Przed chwilą"})
        self.social_feed = self.social_feed[:20]

    def match_payload(self, result, player_goals=0, player_assists=0, player_yellow=0,
                       player_red=0, events=None, squad_status=None, minutes=0, can_choose=False):
        m = None if not result else {
            "home": result.home.name,
            "away": result.away.name,
            "homeGoals": result.home_goals,
            "awayGoals": result.away_goals,
            "playerGoals": player_goals,
            "playerAssists": player_assists,
            "playerYellow": player_yellow,
            "playerRed": player_red,
            "squadStatus": squad_status,
            "minutesPlayed": minutes,
            "canChoose": can_choose,
            "events": events or [],
        }
        return {"result": m, "match": m, "state": self.state()}

    def state(self):
        if not self.created: return {"created":False}
        table=build_table(self.league) if self.league else []
        pos=next((i+1 for i,r in enumerate(table) if r.club is self.player_club),None) if table else None
        sel=select_matchday_squad(self.player_club) if self.player_club else None
        status="out"
        if sel and any(p.id==self.player.id for p in sel.starting_xi): status="start"
        elif sel and any(p.id==self.player.id for p in sel.bench): status="bench"
        fixture=self.next_fixture()
        
        return {
            "created": True,
            "isRetired": self.is_retired,
            "offers": self.offers,
            "player": {
                "name": self.player.full_name,
                "firstName": self.player.first_name,
                "lastName": self.player.last_name,
                "age": self.player.age,
                "position": self.player.position.value,
                "ovr": self.player.ovr,
                "potential": self.player.potential,
                "form": self.player.form,
                "condition": self.player.condition,
                "injured": self.player.is_injured,
                "squadStatus": status,
                "number": getattr(self.player, 'shirt_number', 10),
                "canRetire": True
            },
            "club": {
                "id": self.player_club.id if self.player_club else None,
                "name": self.player_club.name if self.player_club else None,
                "ovr": self.player_club.strength if self.player_club else None,
                "league": self.league.name if self.league else None,
                "position": pos
            },
            "calendar": {
                "season": self.calendar.season if self.calendar else None,
                "matchday": self.calendar.matchday if self.calendar else 1,
                "date": self.calendar.current_date.isoformat() if self.calendar else None,
                "totalMatchdays": self.engines[self.league.name].total_matchdays if (self.league and self.league.name in self.engines) else 30,
                "seasonFinished": self.pending_season_end
            },
            "fixture": None if not fixture else {
                "home": fixture.home.name, 
                "away": fixture.away.name, 
                "homeId": fixture.home.id, 
                "awayId": fixture.away.id,
                "homeColors": getattr(fixture.home, 'colors', ["#FFFFFF"]),
                "awayColors": getattr(fixture.away, 'colors', ["#FFFFFF"])
            },
            "nextMatch": None if not fixture else {
                "opponent": fixture.away.name if (self.player_club and fixture.home is self.player_club) else fixture.home.name
            },
            "trainingUsed": self.training_used,
            "stats": self.career_stats,
            "seasonStats": self.season_stats,
            "news": self.news[:12],
            "socialFeed": self.social_feed[:10],
            "seasonHistory": self.season_history,
            "national": self.national,
            "pendingTransferOffers": self.pending_transfer_offers,
            "cup": {
                "name": "Puchar Polski",
                "finished": bool(self.cup and self.cup.is_finished),
                "rounds": len(self.cup.rounds_played) if self.cup else 0,
                "champion": self.cup.champion.name if self.cup and self.cup.champion else None
            },
            "europe": {k: {"finished": v.is_finished, "rounds": len(v.rounds_played), "champion": v.champion.name if v.champion else None} for k, v in self.europe_cups.items()},
            "finances": {
                "balance": self.finances.balance,
                "salary": self.finances.weekly_salary,
                "hasTrainer": self.finances.personal_trainer,
                "agentTier": self.finances.agent_tier
            },
            "relationships": {
                "managerTrust": self.relationships.manager_trust,
                "fanApproval": self.relationships.fan_approval
            },
            "perks": [{"id": p.id, "name": p.name, "desc": p.description, "cost": p.cost_skill_points, "unlocked": p.unlocked} for p in self.perks],
            "skillPoints": self.skill_points,
            "lastMatchLog": getattr(self, "last_match_log", []),
            "lifestyle": getattr(self, "lifestyle", {"prestige": 0, "owned": []}),
            "lifestyleShop": [{"id": k, **v} for k, v in LUXURY_ITEMS.items()],
            "trophies": getattr(self, "trophies", []),
            "teamChemistry": getattr(self, "team_chemistry", 70),
            "sponsors": SPONSORS,
            "activeSponsor": getattr(self, "active_sponsor", None)
        }

    def table(self, league_name):
        league=next((l for l in self.leagues if l.name==league_name), None)
        if not league: return []
        return [{
            "pos": r.position,
            "club": r.club.name,
            "ovr": r.club.strength,
            "played": r.club.played,
            "w": r.club.wins,
            "d": r.club.draws,
            "l": r.club.losses,
            "gd": r.club.goal_difference,
            "pts": r.club.points,
            "colors": getattr(r.club, 'colors', ["#005CA9", "#FFFFFF"]),
            "mine": r.club is self.player_club
        } for r in build_table(league)]

    def squad(self):
        if not self.player_club: return {"starting":[],"bench":[],"out":[]}
        s=select_matchday_squad(self.player_club)
        def ser(ps): return [{"name":p.full_name,"position":p.position.value,"ovr":p.ovr,"age":getattr(p, 'age', 20),"number":getattr(p, 'shirt_number', '?'),"mine":p is self.player} for p in ps]
        return {"starting":ser(s.starting_xi),"bench":ser(s.bench),"out":ser(s.out_of_squad)}

    def save_full(self):
        attrs = {
            "pace": self.player.attributes.pace,
            "acceleration": self.player.attributes.acceleration,
            "dribbling": self.player.attributes.dribbling,
            "ball_control": self.player.attributes.ball_control,
            "passing": self.player.attributes.passing,
            "vision": self.player.attributes.vision,
            "technique": self.player.attributes.technique,
            "positioning": self.player.attributes.positioning,
            "strength": self.player.attributes.strength,
            "stamina": self.player.attributes.stamina,
            "finishing": self.player.attributes.finishing,
            "shot_power": self.player.attributes.shot_power,
            "heading": self.player.attributes.heading,
            "tackling": self.player.attributes.tackling,
            "marking": self.player.attributes.marking,
            "reflexes": self.player.attributes.reflexes,
            "handling": self.player.attributes.handling,
            "diving": self.player.attributes.diving,
            "kicking": self.player.attributes.kicking
        }
        clubs=[]
        for league in self.leagues:
            for c in league.clubs:
                clubs.append({"id":c.id,"name":c.name,"league":league.name,"strength":c.strength,"played":c.played,"wins":c.wins,"draws":c.draws,"losses":c.losses,"gf":c.goals_for,"ga":c.goals_against})
        return {
            "version": 1,
            "is_retired": self.is_retired,
            "player": {
                "firstName": self.player.first_name,
                "lastName": self.player.last_name,
                "age": self.player.age,
                "position": self.player.position.value,
                "potential": self.player.potential,
                "attributes": attrs,
                "form": self.player.form,
                "condition": self.player.condition,
                "id": self.player.id,
                "shirt_number": getattr(self.player, 'shirt_number', 10)
            },
            "clubName": self.player_club.name if self.player_club else "",
            "clubs": clubs,
            "season": self.calendar.season if self.calendar else "2026/27",
            "matchday": self.calendar.matchday if self.calendar else 1,
            "date": self.calendar.current_date.isoformat() if self.calendar else dt.date.today().isoformat(),
            "stats": self.career_stats,
            "seasonStats": self.season_stats,
            "news": self.news,
            "socialFeed": getattr(self, "social_feed", []),
            "seasonHistory": self.season_history,
            "national": self.national,
            "trainingUsed": self.training_used,
            "finances": {
                "balance": self.finances.balance,
                "weekly_salary": self.finances.weekly_salary,
                "personal_trainer": self.finances.personal_trainer,
                "agent_tier": self.finances.agent_tier
            },
            "relationships": {
                "manager_trust": self.relationships.manager_trust,
                "fan_approval": self.relationships.fan_approval
            },
            "skill_points": self.skill_points,
            "unlocked_perks": [p.id for p in self.perks if getattr(p, 'unlocked', False)],
            "lifestyle": getattr(self, "lifestyle", {"prestige": 0, "owned": []}),
            "trophies": getattr(self, "trophies", []),
            "teamChemistry": getattr(self, "team_chemistry", 70),
            "activeSponsor": getattr(self, "active_sponsor", None)
        }

    def load_full(self, snap):
        p=snap["player"]; self.start(p["firstName"],p["lastName"],p["position"],p["age"])
        self.is_retired = snap.get("is_retired", False)
        self.player.id=p.get("id",self.player.id); self.player.potential=p["potential"]; self.player.form=p["form"]; self.player.condition=p["condition"]
        self.player.shirt_number = p.get("shirt_number", 10)
        for k,v in p["attributes"].items(): setattr(self.player.attributes,k,v)
        self.player.attributes.clamp()
        membership={c["name"]:c["league"] for c in snap["clubs"]}
        by_name={c.name:c for l in self.leagues for c in l.clubs}
        for l in self.leagues:
            l.clubs[:]=[by_name[n] for n,t in membership.items() if t==l.name and n in by_name]
        for cdata in snap["clubs"]:
            if cdata["name"] in by_name:
                c=by_name[cdata["name"]]; c.id=cdata["id"]; c.strength=cdata["strength"]; c.played=cdata["played"]; c.wins=cdata["wins"]; c.draws=cdata["draws"]; c.losses=cdata["losses"]; c.goals_for=cdata["gf"]; c.goals_against=cdata["ga"]
        
        target_club = next((c for l in self.leagues for c in l.clubs if c.name==snap["clubName"]), None)
        if target_club:
            self.player_club = target_club
            self.league = self._find_league(self.player_club)
            self.player_club.add_player(self.player)
            
        self.calendar=GameCalendar(snap["season"],dt.date.fromisoformat(snap["date"]))
        self.calendar.matchday=snap["matchday"]
        self.engines={l.name:SeasonEngine(l,rng=self.rng) for l in self.leagues}
        for eng in self.engines.values(): eng._current_matchday=snap["matchday"]
        self.career_stats=snap["stats"]; self.season_stats=snap["seasonStats"]; self.news=snap["news"]; self.social_feed=snap.get("socialFeed",[]); self.season_history=snap["seasonHistory"]; self.national=snap["national"]; self.training_used=snap["trainingUsed"]
        
        if "finances" in snap:
            self.finances.balance = snap["finances"].get("balance", 5000)
            self.finances.weekly_salary = snap["finances"].get("weekly_salary", 1500)
            self.finances.personal_trainer = snap["finances"].get("personal_trainer", False)
            self.finances.agent_tier = snap["finances"].get("agent_tier", 1)

        if "relationships" in snap:
            self.relationships.manager_trust = snap["relationships"].get("manager_trust", 50)
            self.relationships.fan_approval = snap["relationships"].get("fan_approval", 50)

        self.skill_points = snap.get("skill_points", 5)
        unlocked_ids = snap.get("unlocked_perks", [])
        for p in self.perks: p.unlocked = p.id in unlocked_ids

        self.lifestyle = snap.get("lifestyle", {"prestige": 0, "owned": []})
        self.trophies = snap.get("trophies", [])
        self.team_chemistry = snap.get("teamChemistry", 70)
        self.active_sponsor = snap.get("activeSponsor", None)
        self.pending_season_end=all(e.is_finished() for e in self.engines.values())
        self.setup_cups(); self.generate_offers() if not self.pending_season_end else self._prepare_season_end()

    def save(self):
        return self.save_full()

GAMES: dict[str, Game] = {}

def current_game() -> Game:
    game_id = session.get("game_id")
    if not game_id or game_id not in GAMES:
        game_id = uuid.uuid4().hex
        session["game_id"] = game_id
        GAMES[game_id] = Game()
    return GAMES[game_id]

# --- ENDPOINTY API ---

@app.post("/api/career/create")
def create():
    d = request.get_json(force=True) or {}
    g = current_game()
    # Frontend wysyła klucze w snake_case (first_name/last_name), ale akceptujemy
    # też camelCase dla kompatybilności wstecznej z innymi wywołaniami.
    first = d.get("first_name") or d.get("firstName") or "Mateusz"
    last = d.get("last_name") or d.get("lastName") or "Kowalski"
    g.start(first, last, d.get("position","ST"), int(d.get("age",18)))
    return jsonify(g.state())

@app.get("/api/career/offers")
def career_offers():
    g = current_game()
    return jsonify(g.offers if g.created else [])

@app.post("/api/career/choose-club")
def choose_club():
    """Alias dla /api/career/accept dopasowany do nazw używanych w UI.
    offer_id może być id/clubId klubu albo indeksem na liście ofert."""
    try:
        g = current_game()
        d = request.get_json(force=True) or {}
        offer_id = d.get("offer_id")
        club_id = offer_id
        if isinstance(offer_id, int) or (isinstance(offer_id, str) and offer_id.isdigit() and int(offer_id) < len(g.offers)):
            idx = int(offer_id)
            if 0 <= idx < len(g.offers):
                club_id = g.offers[idx].get("clubId")
        g.accept_offer(club_id)
        return jsonify(g.state())
    except (ValueError, RuntimeError) as e:
        return jsonify({"error": str(e)}), 400

@app.post("/api/career/accept")
def accept():
    try:
        g=current_game(); g.accept_offer((request.get_json(force=True) or {}).get("clubId")); return jsonify(g.state())
    except (ValueError, RuntimeError) as e: return jsonify({"error":str(e)}),400

@app.get("/api/state")
def state(): return jsonify(current_game().state())

@app.post("/api/match/simulate")
def match():
    try: return jsonify(current_game().simulate_week())
    except (ValueError, RuntimeError) as e: return jsonify({"error":str(e)}),400
    except Exception as e: return jsonify({"error":str(e)}),400

@app.post("/api/match/choice")
def match_choice():
    g = current_game()
    data = request.get_json(force=True) or {}
    action_type = data.get("action")
    player = g.player
    if not player: return jsonify({"error": "Brak gracza"}), 400
    if not getattr(g, "match_choice_available", False):
        return jsonify({"error": "Ta akcja jest dostępna tylko po rozegraniu meczu, w którym wystąpiłeś."}), 400
    if getattr(g, "match_choice_used", False):
        return jsonify({"error": "W tym meczu już wykorzystałeś swoją akcję."}), 400
    if action_type not in ("shoot", "pass", "dribble"):
        return jsonify({"error": "Nieznana akcja."}), 400

    g.match_choice_used = True
    base_ovr = player.ovr
    form = player.form
    success_chance = (base_ovr * 0.7) + (form * 0.3)
    if action_type == 'shoot': success_chance += 5
    elif action_type == 'pass': success_chance += 10
    elif action_type == 'dribble': success_chance -= 10

    roll = g.rng.randint(1, 100)
    success = roll <= success_chance
    event_msg = ""
    if success:
        if action_type == 'shoot':
            g.career_stats['goals'] += 1; g.season_stats['goals'] += 1; g.skill_points += 2
            event_msg = "⚽ GOOOOL! Potężny strzał w samo okienko! (+2 pkt)"
        elif action_type == 'pass':
            g.career_stats['assists'] += 1; g.season_stats['assists'] += 1; g.skill_points += 1
            event_msg = "🎯 ASYSTA! Genialne podanie w tempo, partner wykańcza akcję!"
        else:
            g.career_stats['goals'] += 1; g.season_stats['goals'] += 1; g.skill_points += 3
            event_msg = "🔥 ALEŻ AKCJA! Mija obrońców jak tyczki i pakuje piłkę do siatki! (+3 pkt)"
        g._modify_approval(3); g._modify_trust(2)
        g.post_social_feed("goal")
    else:
        if action_type == 'shoot': event_msg = "❌ Strzał zablokowany przez obrońcę... Niepotrzebny pośpiech."
        elif action_type == 'pass': event_msg = "❌ Niecelne podanie, rywale przejęli piłkę."
        else: event_msg = "❌ Strata przy próbie dryblingu! Trener kręci głową."
        g._modify_trust(-1)

    g.last_match_log.append(event_msg)
    return jsonify({'success': success, 'message': event_msg, 'state': g.state()})

@app.post("/api/contract/negotiate")
def negotiate_contract():
    g = current_game()
    data = request.get_json(force=True) or {}
    req_wage = int(data.get('wage', 0))
    req_bonus = int(data.get('bonus', 0))
    patience = int(data.get('patience', 100))
    club_id = data.get('clubId')
    
    target_offer = next((o for o in (g.pending_transfer_offers or g.offers) if str(o.get('clubId')) == str(club_id) or str(o.get('club')) == str(club_id)), None)
    if not target_offer:
        target_club = next((c for l in g.leagues for c in l.clubs if str(c.id) == str(club_id) or c.name == club_id), None)
        if target_club: target_offer = {"clubId": target_club.id, "wage": g._calc_wage(target_club)}

    if not target_offer: return jsonify({'error': 'Nie odnaleziono oferty dla wybranego klubu'}), 400
        
    base_wage = target_offer.get('wage', 3000)
    agent_bonus = g.finances.agent_tier * 0.15
    max_acceptable_wage = base_wage * (1.5 + agent_bonus)
    greed_factor = (req_wage / max(1, base_wage)) + (req_bonus / 1000)
    
    if req_wage <= max_acceptable_wage and greed_factor <= 1.8:
        g.finances.weekly_salary = req_wage
        if g.pending_season_end: g.finish_season('transfer', club_id)
        else: g.accept_offer(club_id)
        g.add_news("contract", f"✍️ Podpisano nowy kontrakt! Pensja: {req_wage:,} PLN.")
        return jsonify({'success': True, 'message': 'Umowa została podpisana!', 'state': g.state()})
    else:
        new_patience = patience - random.randint(15, 30)
        if new_patience <= 0:
            g.pending_transfer_offers = [o for o in g.pending_transfer_offers if str(o.get('clubId')) != str(club_id)]
            g.offers = [o for o in g.offers if str(o.get('clubId')) != str(club_id)]
            return jsonify({'success': False, 'rejected': True, 'message': 'Klub zerwał negocjacje! Oferta wycofana.', 'state': g.state()})
        else:
            counter_wage = round(base_wage * 1.25)
            return jsonify({'success': False, 'rejected': False, 'patience': new_patience, 'counterWage': counter_wage, 'message': f'Klub odrzucił Twoje warunki. Cierpliwość zarządu: {new_patience}%'})

@app.post("/api/sponsor/sign")
def sign_sponsor():
    g = current_game()
    data = request.get_json(force=True) or {}
    sponsor_id = data.get("sponsorId")
    sp = next((s for s in SPONSORS if s["id"] == sponsor_id), None)
    if sp and g.lifestyle["prestige"] >= sp["req_prestige"]:
        g.active_sponsor = sponsor_id
        g.add_news("sponsor", f"🖊️ Podpisano Umowę Sponsorską z {sp['name']}! (+{sp['pay']:,} PLN tygodniowo)")
        g.add_social("Sponsor_Official", f"Dumne partnerstwo! {g.player.full_name} oficjalną twarzą marki {sp['name']}! ⚡")
        return jsonify(g.state())
    return jsonify({"error": "Brak wymaganego poziomu prestiżu!"}), 400

@app.post("/api/player/rehab")
def player_rehab():
    g = current_game()
    player = g.player
    if not player or not player.is_injured: return jsonify({'error': 'Zawodnik nie jest kontuzjowany!'}), 400
    if g.finances.balance < 15000: return jsonify({'error': 'Brak środków na zabieg rehabilitacyjny (15,000 PLN)'}), 400
    g.finances.balance -= 15000
    if player.current_injury:
        player.current_injury.weeks_remaining = max(0, player.current_injury.weeks_remaining - 2)
        if player.current_injury.weeks_remaining == 0:
            player.current_injury = None
            g.add_news("injury", f"🏥 {player.full_name} przeszedł pomyślny zabieg i wrócił do pełnej sprawności!")
        else:
            g.add_news("injury", f"🏥 Zabieg skrócił czas leczenia o 2 tygodnie (pozostało: {player.current_injury.weeks_remaining} tyg.).")
    return jsonify(g.state())

@app.post("/api/training")
def training():
    try:
        g=current_game(); g.train((request.get_json(force=True) or {}).get("focus")); return jsonify(g.state())
    except (ValueError, RuntimeError) as e: return jsonify({"error":str(e)}),400
    except Exception as e: return jsonify({"error":str(e)}),400

@app.get("/api/table")
def table():
    g=current_game(); name=request.args.get("league") or (g.league.name if g.league else "Ekstraklasa")
    return jsonify(g.table(name))

@app.get("/api/leagues")
def leagues(): return jsonify([{"name":l.name,"clubs":len(l.clubs)} for l in current_game().leagues])

@app.get("/api/squad")
def squad(): return jsonify(current_game().squad())

@app.get("/api/world")
def world():
    g=current_game(); return jsonify({"leagues":[{"name":l.name,"leader":build_table(l)[0].club.name if build_table(l) else "Brak","table":g.table(l.name)} for l in g.leagues],"events":g.news[:20]})

@app.post("/api/season/decision")
def season_decision():
    try:
        d=request.get_json(force=True) or {}; g=current_game(); g.finish_season(d.get("decision","stay"),d.get("clubId")); return jsonify(g.state())
    except (ValueError, RuntimeError) as e: return jsonify({"error":str(e)}),400

@app.post("/api/career/retire")
def retire():
    g = current_game()
    if g.player:
        g.is_retired = True
        g.add_news("career", f"🏁 {g.player.full_name} ogłasza przejście na piłkarską emeryturę w wieku {g.player.age} lat!")
        g.post_social_feed("luxury")
        return jsonify(g.state())
    return jsonify({"error": "Brak aktywnego zawodnika!"}), 400

@app.post("/api/perk/unlock")
def unlock_perk():
    g = current_game()
    data = request.get_json(force=True) or {}
    perk_id = data.get("perkId")
    perk = next((p for p in g.perks if p.id == perk_id), None)
    if perk and not perk.unlocked and g.skill_points >= perk.cost_skill_points:
        g.skill_points -= perk.cost_skill_points
        perk.unlocked = True
        return jsonify(g.state())
    return jsonify({"error": "Brak punktów lub perk już odblokowany"}), 400

@app.post("/api/finance/buy-trainer")
def buy_trainer():
    g = current_game()
    if g.finances.hire_trainer(): return jsonify(g.state())
    return jsonify({"error": "Niewystarczające środki lub trener został już zatrudniony"}), 400

@app.post("/api/finance/upgrade-agent")
def upgrade_agent():
    g = current_game()
    if g.finances.upgrade_agent(): return jsonify(g.state())
    return jsonify({"error": "Niewystarczające środki lub osiągnięto maksymalny poziom agenta"}), 400

@app.post("/api/lifestyle/buy")
def buy_lifestyle():
    g = current_game()
    data = request.get_json(force=True) or {}
    item_id = data.get('itemId')
    if item_id not in LUXURY_ITEMS: return jsonify({'error': 'Nieprawidłowy przedmiot'}), 400
    item = LUXURY_ITEMS[item_id]
    if item_id in g.lifestyle['owned']: return jsonify({'error': 'Już posiadasz ten przedmiot'}), 400
    if g.finances.balance < item['cost']: return jsonify({'error': 'Brak wystarczających środków!'}), 400
    g.finances.balance -= item['cost']
    g.lifestyle['owned'].append(item_id)
    g.lifestyle['prestige'] += item['prestige']
    g._modify_approval(item['approval'])
    g._modify_trust(item['trust'])
    g.post_social_feed("luxury")
    return jsonify(g.state())

@app.get("/api/save")
def save(): return jsonify(current_game().save())

@app.post("/api/save")
def save_to_disk():
    """Trwały zapis do pliku w filesDir telefonu (offline, bez sieci)."""
    try:
        g = current_game()
        import json as _json
        path = get_save_path()
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(g.save(), f, ensure_ascii=False)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": f"Nie udało się zapisać kariery: {e}"}), 400

@app.post("/api/load")
def load():
    try:
        g=current_game(); g.load_full(request.get_json(force=True) or {})
        return jsonify(g.state())
    except Exception as e: return jsonify({"error":f"Nie udało się wczytać zapisu: {e}"}),400

@app.get("/api/load")
def load_from_disk():
    """Wczytanie zapisu z pliku w filesDir telefonu."""
    try:
        import json as _json
        path = get_save_path()
        if not os.path.exists(path):
            return jsonify(None)
        with open(path, "r", encoding="utf-8") as f:
            snap = _json.load(f)
        g = current_game()
        g.load_full(snap)
        return jsonify(g.state())
    except Exception as e:
        return jsonify({"error": f"Nie udało się wczytać zapisu: {e}"}), 400

@app.post("/api/save/delete")
def delete_save():
    try:
        path = get_save_path()
        if os.path.exists(path):
            os.remove(path)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/health")
def health(): return jsonify({"ok":True,"version":"9.1.0-full-fixed"})

def run_server(host='127.0.0.1', port=5000, user_data_dir=None):
    """Punkt wejścia wywoływany przez natywną warstwę Android/Chaquopy.
    user_data_dir to zwykle filesDir aplikacji - tam trafiają zapisy kariery."""
    global SAVE_DIRECTORY
    if user_data_dir:
        SAVE_DIRECTORY = user_data_dir
        os.makedirs(SAVE_DIRECTORY, exist_ok=True)
    app.run(host=host, port=port, threaded=True, debug=False)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
