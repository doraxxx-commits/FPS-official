window.addEventListener('error', e => { 
  console.error(e.error || e.message); 
});

let S = null;
let league = 'Ekstraklasa';
let toastTimer = null;

const $ = id => document.getElementById(id);

const esc = x => String(x ?? '').replace(/[&<>"']/g, m => ({ 
  '&': '&amp;', 
  '<': '&lt;', 
  '>': '&gt;', 
  '"': '&quot;', 
  "'": '&#39;' 
}[m]));

function toast(t) {
  const el = $('toast');
  if (!el) return;
  
  if (toastTimer) {
    clearTimeout(toastTimer);
  }
  
  el.textContent = t;
  el.classList.remove('show');
  void el.offsetWidth;
  el.classList.add('show');
  
  toastTimer = setTimeout(() => {
    el.classList.remove('show');
  }, 2400);
}

function vib(pattern = 18) {
  try {
    if (
      typeof navigator !== 'undefined' && 
      typeof navigator.vibrate === 'function' && 
      !/iPhone|iPad|iPod/i.test(navigator.userAgent)
    ) {
      navigator.vibrate(pattern);
    }
  } catch (e) {}
}

function audio(type) {
  try {
    const C = window.AudioContext || window.webkitAudioContext;
    if (!C) return;
    const c = new C();
    if (c.state === 'suspended') {
      c.resume();
    }

    const o = c.createOscillator();
    const g = c.createGain();
    o.connect(g);
    g.connect(c.destination);
    const now = c.currentTime;

    if (type === 'click') {
      o.type = 'sine';
      o.frequency.setValueAtTime(550, now);
      o.frequency.exponentialRampToValueAtTime(180, now + 0.05);
      g.gain.setValueAtTime(0.06, now);
      g.gain.linearRampToValueAtTime(0.001, now + 0.05);
      o.start(now);
      o.stop(now + 0.06);
    } else if (type === 'perk') {
      o.type = 'triangle';
      o.frequency.setValueAtTime(400, now);
      o.frequency.exponentialRampToValueAtTime(850, now + 0.15);
      g.gain.setValueAtTime(0.1, now);
      g.gain.linearRampToValueAtTime(0.001, now + 0.18);
      o.start(now);
      o.stop(now + 0.19);
    } else if (type === 'goal' || type === 'win') {
      o.type = 'sawtooth';
      o.frequency.setValueAtTime(220, now);
      o.frequency.exponentialRampToValueAtTime(660, now + 0.3);
      g.gain.setValueAtTime(0.12, now);
      g.gain.linearRampToValueAtTime(0.001, now + 0.35);
      o.start(now);
      o.stop(now + 0.36);
    }
  } catch (e) {}
}

document.addEventListener('click', (e) => {
  if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
    audio('click');
  }
});

// BAZA DANYCH WSZYSTKICH LIG Z APP.PY DLA SILNIKA OFFLINE
const ALL_LEAGUES_DATA = {
  "Ekstraklasa": ["Lech Poznań", "Legia Warszawa", "Raków Częstochowa", "Jagiellonia Białystok", "Górnik Zabrze", "Pogoń Szczecin", "Cracovia", "Piast Gliwice", "Widzew Łódź", "Wisła Kraków", "Radomiak Radom", "Zagłębie Lubin", "Śląsk Wrocław", "GKS Katowice", "Korona Kielce", "Motor Lublin", "Wisła Płock", "Wieczysta Kraków"],
  "1. Liga": ["Chrobry Głogów", "Lechia Gdańsk", "Arka Gdynia", "Ruch Chorzów", "ŁKS Łódź", "Miedź Legnica", "Polonia Warszawa", "Bruk-Bet Termalica Nieciecza", "Puszcza Niepołomice", "Polonia Bytom", "Stal Mielec", "Odra Opole", "Pogoń Grodzisk Mazowiecki", "Stal Rzeszów", "GKS Jastrzębie", "Pogoń Siedlce", "Świt Szczecin", "Wisła Puławy"],
  "2. Liga": ["Resovia Rzeszów", "Chojniczanka Chojnice", "Zagłębie Sosnowiec", "Legia II Warszawa", "Kotwica Kołobrzeg", "Rekord Bielsko-Biała", "Zawisza Bydgoszcz", "Avia Świdnik", "Hutnik Kraków", "Lechia Zielona Góra", "Skra Częstochowa", "Sokół Kleczew", "Concordia Piotrków Trybunalski", "Wigry Suwałki", "Radunia Stężyca", "Unia Skierniewice", "Warta Poznań II", "Znicz Biała Piska"],
  "3. Liga I": ["Polonia Warszawa II", "Stomil Olsztyn", "Olimpia Elbląg", "Świt Nowy Dwór Mazowiecki", "Huragan Wołomin", "Pelikan Łowicz", "Wisła II Płock", "Mazur Karczew", "Motor II Lublin", "Mławianka Mława", "Sokół Ostróda", "Legionovia Legionowo", "Sparta Świątki", "Ursus Warszawa", "Wkra Żuromin", "Pogoń II Siedlce", "Victoria Sulejówek", "Ząbkovia Ząbki"],
  "3. Liga II": ["GKS Bełchatów", "Olimpia Grudziądz", "Warta Gorzów Wlkp.", "Gryf Wejherowo", "Bałtyk Gdynia", "Odra Wodzisław", "Chemik Bydgoszcz", "KKS 1925 Kalisz", "Sokół Pniewy", "Unia Swarzędz", "Elana Toruń", "Polonia Środa Wielkopolska", "Sparta Brodnica", "Włókniarz Kietrz", "Kotwica II Kołobrzeg", "Pogoń Staszów", "Sokół Aleksandrów Łódzki", "Nielba Wągrowiec"],
  "3. Liga III": ["Górnik Polkowice", "Lech II Poznań", "Ślęza Wrocław", "Górnik Konin", "Miedź II Legnica", "Polonia Bydgoszcz", "Stal Brzeg", "Victoria Września", "Chrobry II Głogów", "Karkonosze Jelenia Góra", "Piast II Gliwice", "Piast Żmigród", "Warta Sieradz", "Zagłębie II Lubin", "Odra II Opole", "Rakoniewice", "Kotwica Kołobrzeg II", "Unia Turza Śląska"],
  "3. Liga IV": ["Cracovia II", "Karpaty Krosno", "Podhale Nowy Targ", "Stal Rzeszów II", "Stal Sanok", "Wieczysta II Kraków", "Górnik II Łęczna", "Hetman Zamość", "Igloopol Dębica", "Motor Lublin II", "Resovia II Rzeszów", "Sokół Sokołów Małopolski", "Wisła Sandomierz", "Wisłoka Dębica", "Czarni Połaniec", "Orzeł Przeworsk", "Wisłok Wiśniowa", "Podlasie Biała Podlaska"],
  "Premier League": ["Manchester City", "Arsenal", "Liverpool", "Chelsea", "Newcastle United", "Tottenham Hotspur", "Aston Villa", "Manchester United", "Brighton & Hove Albion", "Nottingham Forest", "Crystal Palace", "Fulham", "Bournemouth", "Everton", "Brentford", "Leeds United", "Sunderland", "Coventry City", "Ipswich Town", "Hull City"],
  "Championship": ["West Ham United", "Wolverhampton Wanderers", "Burnley", "Sheffield United", "Southampton", "Middlesbrough", "West Bromwich Albion", "Norwich City", "Blackburn Rovers", "Millwall", "Sheffield Wednesday", "Stoke City", "Swansea City", "Watford", "Derby County", "Portsmouth", "Preston North End", "Queens Park Rangers", "Wrexham", "Oxford United", "Plymouth Argyle", "Cardiff City", "Charlton Athletic", "Bolton Wanderers", "Lincoln City", "Port Vale"],
  "League One": ["Birmingham City", "Wigan Athletic", "Blackpool", "Peterborough United", "Barnsley", "Bristol Rovers", "Luton Town", "Reading", "Rotherham United", "Stockport County", "Huddersfield Town", "Leicester City", "Leyton Orient", "Mansfield Town", "Exeter City", "Northampton Town", "Wycombe Wanderers", "Burton Albion", "Shrewsbury Town", "Crawley Town", "Doncaster Rovers", "Bromley", "Cambridge United", "Chesterfield", "Stevenage", "Shrewsbury Town II"],
  "Bundesliga": ["Bayern Monachium", "Bayer Leverkusen", "Borussia Dortmund", "RB Lipsk", "VfB Stuttgart", "Eintracht Frankfurt", "Borussia Mönchengladbach", "SC Freiburg", "1. FSV Mainz 05", "Werder Brema", "TSG Hoffenheim", "Union Berlin", "FC Augsburg", "1. FC Köln", "Hamburger SV", "Schalke 04", "SC Paderborn 07", "SV Elversberg"],
  "2. Bundesliga": ["VfL Wolfsburg", "1. FC Heidenheim", "VfL Bochum", "FC St. Pauli", "Hertha BSC", "Holstein Kiel", "1. FC Kaiserslautern", "Hannover 96", "1. FC Magdeburg", "Karlsruher SC", "1. FC Nürnberg", "Arminia Bielefeld", "Darmstadt 98", "SpVgg Greuther Fürth", "Dynamo Dresden", "Eintracht Braunschweig", "VfL Osnabrück", "Energie Cottbus"],
  "Ligue 1": ["Paris Saint-Germain", "Olympique Marsylia", "AS Monaco", "Olympique Lyon", "LOSC Lille", "OGC Nice", "RC Lens", "Stade Rennais", "RC Strasbourg", "Stade Brestois"],
  "Ligue 2": ["Paris FC", "Troyes", "Guingamp", "Bastia", "Clermont Foot", "Amiens", "Caen", "Grenoble", "Ajaccio", "Pau FC", "Rodez", "Annecy", "Laval", "Red Star", "Dunkerque", "Martigues", "Boulogne", "Bourg-Péronnas"],
  "La Liga": ["Real Madryt", "FC Barcelona", "Atlético Madryt", "Athletic Bilbao", "Villarreal", "Real Sociedad", "Real Betis", "Sevilla", "Girona", "Valencia", "Celta Vigo", "Osasuna", "Getafe", "Mallorca", "Rayo Vallecano", "Alavés", "Espanyol", "Elche", "Levante", "Real Oviedo"],
  "La Liga 2": ["Deportivo La Coruña", "Las Palmas", "Almería", "Racing Santander", "Sporting Gijón", "Cádiz CF"],
  "Liga Portugal": ["SL Benfica", "FC Porto", "Sporting CP", "Sporting Braga", "Vitória Guimarães", "Gil Vicente", "Famalicão", "Casa Pia", "Estoril", "Arouca", "Moreirense", "Rio Ave", "Santa Clara", "Estrela Amadora", "Nacional", "AVS", "Alverca", "Tondela"],
  "Liga Portugal 2": ["Farense", "Marítimo", "Leixões", "Penafiel"],
  "Eredivisie": ["PSV Eindhoven", "Ajax Amsterdam", "Feyenoord", "AZ Alkmaar", "FC Twente", "FC Utrecht", "SC Heerenveen", "NEC Nijmegen"],
  "Serie A": ["Inter Mediolan", "SSC Napoli", "AC Milan", "Juventus", "Atalanta", "AS Roma", "Lazio", "Bologna", "Fiorentina", "Torino", "Como", "Genoa", "Udinese", "Cagliari", "Hellas Verona", "Parma", "Lecce", "Empoli", "Cremonese", "Pisa"],
  "Belgian Pro League": ["Club Brugge", "Union Saint-Gilloise", "Anderlecht", "Genk", "KAA Gent", "Antwerp", "Standard Liège", "Cercle Brugge", "Charleroi", "KV Mechelen", "STVV", "Westerlo", "OH Leuven", "Kortrijk", "RWDM", "Dender"],
  "Süper Lig": ["Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor", "Başakşehir", "Samsunspor", "Antalyaspor", "Kasımpaşa", "Konyaspor", "Kayserispor", "Sivasspor", "Alanyaspor", "Gaziantep FK", "Rizespor", "Göztepe", "Eyüpspor", "Gençlerbirliği", "Kocaelispor"],
  "Scottish Premiership": ["Celtic", "Rangers", "Aberdeen", "Hearts", "Hibernian", "Dundee United", "St Mirren", "Motherwell", "Kilmarnock", "Dundee", "Ross County", "St Johnstone"],
  "Austrian Bundesliga": ["Red Bull Salzburg", "Sturm Graz", "Rapid Wiedeń", "Austria Wiedeń", "LASK", "Wolfsberger AC", "WSG Tirol", "Altach", "Blau-Weiß Linz", "Hartberg", "Grazer AK", "Rheindorf Altach II/Junior"],
  "Super League": ["Young Boys", "FC Basel", "FC Zurich", "Servette", "Lugano", "St. Gallen", "Grasshopper", "Lucerne", "Sion", "Winterthur", "Thun", "Yverdon"],
  "Superliga": ["FC Kopenhaga", "Midtjylland", "Brøndby", "Nordsjælland", "AGF Aarhus", "Silkeborg", "Randers", "AaB", "Viborg", "Vejle", "Sønderjyske", "Hvidovre"],
  "Czech First League": ["Slavia Praga", "Sparta Praga", "Viktoria Pilzno", "Banik Ostrawa", "Slovan Liberec", "Sigma Ołomuniec", "Slovácko", "Mladá Boleslav", "Sparta Praga B", "Bohemians 1905", "Jablonec", "Hradec Králové", "Teplice", "Zlín", "Karviná", "Pardubice"],
  "Greek Super League": ["Olympiakos", "PAOK", "AEK Ateny", "Panathinaikos", "Aris Saloniki", "Asteras Tripolis", "OFI Kreta", "Atromitos", "Panetolikos", "Volos", "Kifisia", "Lamia", "Levadiakos", "Panserraikos"],
  "Série A Brazil": ["Flamengo", "Palmeiras", "Atlético Mineiro", "Botafogo", "São Paulo", "Corinthians", "Grêmio", "Internacional", "Fluminense", "Cruzeiro", "Santos", "Bahia", "Fortaleza", "Vasco da Gama", "Athletico Paranaense", "Bragantino", "Vitória", "Cuiabá", "Juventude", "Criciúma"],
  "Liga Profesional": ["River Plate", "Boca Juniors", "Racing Club", "Talleres", "Vélez Sarsfield", "Estudiantes", "Independiente", "San Lorenzo", "Argentinos Juniors", "Rosario Central", "Lanús", "Newell's Old Boys", "Huracán", "Defensa y Justicia", "Belgrano", "Banfield", "Gimnasia La Plata", "Tigre", "Central Córdoba", "Godoy Cruz", "Instituto", "Platense", "Atlético Tucumán", "Barracas Central", "Independiente Rivadavia", "Unión", "Sarmiento", "Deportivo Riestra"],
  "Liga MX": ["Club América", "Monterrey", "Tigres UANL", "Chivas Guadalajara", "Cruz Azul", "Toluca", "Pumas UNAM", "Pachuca", "León", "Atlas", "Santos Laguna", "Atlético San Luis", "Necaxa", "Puebla", "Tijuana", "Juárez", "Mazatlán", "Querétaro"],
  "MLS": ["Inter Miami", "LAFC", "Columbus Crew", "Philadelphia Union", "Seattle Sounders", "FC Cincinnati", "LA Galaxy", "Atlanta United", "Orlando City", "Nashville SC", "New York City FC", "New York Red Bulls", "Portland Timbers", "San Diego FC", "St. Louis City", "Vancouver Whitecaps", "Charlotte FC", "Minnesota United", "Real Salt Lake", "Sporting Kansas City", "Chicago Fire", "Toronto FC", "Austin FC", "D.C. United", "FC Dallas", "Houston Dynamo", "New England Revolution", "CF Montréal", "Colorado Rapids", "San Jose Earthquakes"]
};

// Pomocniczy generator dynamicznych tabel ligowych
function getOrCreateLeagueTables(state) {
  if (!state.leagueTables) {
    state.leagueTables = {};
  }
  Object.keys(ALL_LEAGUES_DATA).forEach(lName => {
    if (!state.leagueTables[lName]) {
      const clubs = ALL_LEAGUES_DATA[lName];
      state.leagueTables[lName] = clubs.map((c, i) => ({
        pos: i + 1,
        club: c,
        played: Math.max(0, (state.calendar?.matchday || 1) - 1),
        pts: Math.max(0, (state.calendar?.matchday || 1) - 1) * (i === 0 ? 3 : i < 4 ? 2 : 1),
        mine: state.club?.name === c
      }));
    }
  });
  return state.leagueTables;
}

// LOKALNY SILNIK GRY (ZAMIAST SIECIOWEGO FETCH)
async function api(path, opt = {}) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      try {
        const body = opt.body ? JSON.parse(opt.body) : {};
        let state = JSON.parse(localStorage.getItem('fps_slot1') || 'null');

        if (path === '/state') return resolve(state || {});

        // 1. Tworzenie kariery
        if (path === '/career/create') {
          state = {
            created: true,
            player: {
              name: `${body.firstName} ${body.lastName}`,
              lastName: body.lastName,
              position: body.position,
              age: body.age,
              ovr: 65,
              potential: 85,
              number: 10,
              form: 80,
              condition: 100,
              injured: false,
              squadStatus: 'start'
            },
            club: { name: 'Legia Warszawa', league: 'Ekstraklasa', position: 1 },
            calendar: { season: '2025/2026', matchday: 1, totalMatchdays: 30, seasonFinished: false },
            fixture: { home: 'Legia Warszawa', away: 'Lech Poznań' },
            finances: { balance: 15000, wage: 3500, bonus: 300 },
            relationships: { managerTrust: 70, fanApproval: 60 },
            teamChemistry: 75,
            skillPoints: 5,
            trainingUsed: false,
            stats: { matches: 0, minutes: 0, goals: 0, assists: 0 },
            lifestyle: { prestige: 0, owned: [] },
            perks: [
              { id: 'finisher', name: 'Zimna krew', desc: '+10% szans w sytuacji sam na sam', cost: 2, unlocked: false },
              { id: 'playmaker', name: 'Wizjoner', desc: '+15% precyzji podań', cost: 3, unlocked: false }
            ],
            sponsors: [
              { id: 'local_pub', name: 'Lokalna Pizzeria', desc: 'Sponsor lokalny', pay: 1000, req_prestige: 0 },
              { id: 'tech_brand', name: 'Marka Odzieżowa', desc: 'Sponsor ogólnokrajowy', pay: 5000, req_prestige: 25 }
            ],
            activeSponsor: null,
            offers: [
              { id: 1, club: 'Legia Warszawa', league: 'Ekstraklasa', wage: 3500 },
              { id: 2, club: 'Lech Poznań', league: 'Ekstraklasa', wage: 3200 },
              { id: 3, club: 'Raków Częstochowa', league: 'Ekstraklasa', wage: 3400 }
            ],
            pendingTransferOffers: [],
            news: [{ season: '2025/2026', type: 'INFO', text: 'Rozpoczęto nową karierę!' }],
            socialFeed: [{ author: 'Ekspert_007', text: 'Młody talent oficjalnie podpisuje swój pierwszy kontrakt!' }],
            lastMatchLog: [],
            seasonHistory: [],
            trophies: [],
            cup: { rounds: 1, champion: null },
            national: { 'U-21': { called: true, matches: 0 }, 'Reprezentacja A': { called: false, matches: 0 } }
          };
          getOrCreateLeagueTables(state);
          localStorage.setItem('fps_slot1', JSON.stringify(state));
          return resolve({ success: true, state });
        }

        if (!state) return reject(new Error('Brak zapisanego stanu gry'));

        // 2. Negocjacje
        if (path === '/contract/negotiate') {
          state.finances.wage = body.wage || 3500;
          state.finances.bonus = body.bonus || 300;
          localStorage.setItem('fps_slot1', JSON.stringify(state));
          return resolve({ success: true, message: 'Kontrakt podpisany pomyślnie!', state });
        }

        // 3. Symulacja meczu i mechanika gry
        if (path === '/match/simulate') {
          const hG = Math.floor(Math.random() * 4);
          const aG = Math.floor(Math.random() * 3);
          
          let goalsScored = 0;
          if (state.player.squadStatus !== 'out' && !state.player.injured) {
            const chance = (state.player.ovr / 100) * 0.4;
            if (Math.random() < chance) goalsScored = 1;
            if (Math.random() < 0.05) state.player.injured = true; // Szansa na kontuzję
          }

          state.stats.matches++;
          state.stats.minutes += (state.player.squadStatus === 'start' ? 90 : state.player.squadStatus === 'bench' ? 30 : 0);
          state.stats.goals += goalsScored;
          state.calendar.matchday++;
          
          let earn = state.finances.wage + (goalsScored * state.finances.bonus);
          if (state.activeSponsor) {
            const sp = state.sponsors.find(s => s.id === state.activeSponsor);
            if (sp) earn += sp.pay;
          }
          state.finances.balance += earn;
          state.trainingUsed = false; // Reset treningu na nową kolejkę

          // Rotacja przeciwników w aktualnej lidze
          const curLeagueClubs = ALL_LEAGUES_DATA[state.club?.league] || ALL_LEAGUES_DATA['Ekstraklasa'];
          const availableOpponents = curLeagueClubs.filter(c => c !== state.club?.name);
          const nextOpponent = availableOpponents[Math.floor(Math.random() * availableOpponents.length)] || 'Lech Poznań';
          state.fixture = { home: state.club.name, away: nextOpponent };

          state.lastMatchLog = [
            `Wynik końcowy: ${state.fixture.home} ${hG}:${aG} ${state.fixture.away}`,
            goalsScored > 0 ? `⚽ Strzeliłeś gola w tym meczu!` : `Brak Twoich goli w tym spotkaniu.`
          ];

          if (state.calendar.matchday > state.calendar.totalMatchdays) {
            state.calendar.seasonFinished = true;
          }

          localStorage.setItem('fps_slot1', JSON.stringify(state));
          return resolve({ state, result: { home: state.fixture.home, away: state.fixture.away, homeGoals: hG, awayGoals: aG } });
        }

        // 4. Decyzje w meczu
        if (path === '/match/choice') {
          const success = Math.random() > 0.35;
          if (success) {
            state.stats.goals++;
            state.relationships.managerTrust = Math.min(100, state.relationships.managerTrust + 2);
          }
          localStorage.setItem('fps_slot1', JSON.stringify(state));
          return resolve({ 
            success, 
            message: success ? '🎯 Genialne zagranie! Zdobywasz bramkę!' : '❌ Obrońca zdołał zablokować Twoje zagranie.' 
          });
        }

        // 5. Trening
        if (path === '/training') {
          state.player.ovr += 1;
          state.skillPoints += 1;
          state.trainingUsed = true;
          localStorage.setItem('fps_slot1', JSON.stringify(state));
          return resolve(state);
        }

        // 6. Odblokowywanie umiejętności
        if (path === '/perk/unlock') {
          const perk = state.perks.find(p => p.id === body.perkId);
          if (perk && state.skillPoints >= perk.cost) {
            state.skillPoints -= perk.cost;
            perk.unlocked = true;
          }
          localStorage.setItem('fps_slot1', JSON.stringify(state));
          return resolve(state);
        }

        // 7. Kadra
        if (path === '/squad') {
          return resolve({
            starting: [
              { number: state.player.number, position: state.player.position, name: state.player.name, age: state.player.age, ovr: state.player.ovr, mine: true },
              { number: 1, position: 'GK', name: 'Kacper Tobiasz', age: 22, ovr: 72 },
              { number: 8, position: 'CM', name: 'Josue', age: 33, ovr: 75 }
            ],
            bench: [{ number: 18, position: 'ST', name: 'Maciej Rosołek', age: 22, ovr: 67 }],
            out: []
          });
        }

        // 8. Tabele i Ligi (Wszystkie 32 ligi z app.py)
        if (path === '/leagues') {
          return resolve(Object.keys(ALL_LEAGUES_DATA).map(name => ({ name })));
        }
        
        if (path.startsWith('/table')) {
          const urlParams = new URLSearchParams(path.split('?')[1] || '');
          const reqLeague = urlParams.get('league') || state.club?.league || 'Ekstraklasa';
          const tables = getOrCreateLeagueTables(state);
          const leagueClubs = ALL_LEAGUES_DATA[reqLeague] || ALL_LEAGUES_DATA['Ekstraklasa'];

          if (tables[reqLeague]) {
            return resolve(tables[reqLeague]);
          }

          const generatedTable = leagueClubs.map((c, i) => ({
            pos: i + 1,
            club: c,
            played: Math.max(0, state.calendar.matchday - 1),
            pts: Math.max(0, state.calendar.matchday - 1) * (i === 0 ? 3 : i < 4 ? 2 : 1),
            mine: c === state.club?.name
          }));
          return resolve(generatedTable);
        }

        // 9. Zapis i Wczytanie
        if (path === '/save') return resolve(state);
        if (path === '/load') {
          state = body;
          localStorage.setItem('fps_slot1', JSON.stringify(state));
          return resolve(state);
        }

        // 10. Pozostałe akcje
        if (path === '/player/rehab') {
          state.player.injured = false;
          state.finances.balance -= 15000;
        }
        if (path === '/finance/buy-trainer') {
          state.finances.balance -= 10000;
          state.player.ovr += 1;
        }
        if (path === '/finance/upgrade-agent') {
          state.finances.balance -= 20000;
        }
        if (path === '/sponsor/sign') {
          state.activeSponsor = body.sponsorId;
        }
        if (path === '/lifestyle/buy') {
          if (!state.lifestyle.owned) state.lifestyle.owned = [];
          state.lifestyle.owned.push(body.itemId);
          state.lifestyle.prestige += 10;
        }

        if (path === '/season/decision') {
          state.calendar.season = '2026/2027';
          state.calendar.matchday = 1;
          state.calendar.seasonFinished = false;
        }

        localStorage.setItem('fps_slot1', JSON.stringify(state));
        resolve(state);
      } catch (e) {
        reject(e);
      }
    }, 50);
  });
}

function openGame() {
  const onboarding = $('onboarding');
  const game = $('game');
  
  if (onboarding) { 
    onboarding.classList.add('hidden'); 
    onboarding.classList.remove('active'); 
  }
  if (game) { 
    game.classList.remove('hidden'); 
    game.classList.add('active'); 
  }
  renderAll();
}

function showModal(html) {
  const m = $('modal');
  const mc = $('modalContent');
  if (mc) mc.innerHTML = html;
  if (m) m.classList.remove('hidden');
}

window.closeModal = function() {
  $('modal')?.classList.add('hidden');
};

function nav(name) {
  document.querySelectorAll('.screen').forEach(x => x.classList.remove('active'));
  $(`screen-${name}`)?.classList.add('active');
  
  document.querySelectorAll('#nav button').forEach(b => {
    b.classList.toggle('active', b.dataset.screen === name);
  });
  
  renderScreen(name);
  vib(10);
}

window.startCareer = async function(event) {
  if (event) event.preventDefault();

  const payload = {
    firstName: $('firstName')?.value.trim() || 'Mateusz',
    lastName: $('lastName')?.value.trim() || 'Kowalski',
    position: $('position')?.value || 'ST',
    age: Number($('age')?.value || 18)
  };

  if (!payload.firstName || !payload.lastName) {
    return toast('Wpisz imię i nazwisko');
  }
  
  try {
    const response = await api('/career/create', { 
      method: 'POST', 
      body: JSON.stringify(payload) 
    });
    S = response.state || response;
    
    if (S.offers && S.offers.length > 0) {
      openOffers(S.offers);
    } else {
      openGame();
    }
  } catch (err) {
    toast(err.message || 'Nie udało się rozpocząć kariery');
  }
};

function openOffers(offersList) {
  const offers = offersList || (S ? S.offers : []);
  if (!offers || offers.length === 0) {
    openGame();
    return;
  }

  showModal(`
    <div class="eyebrow">PIERWSZY KONTRAKT</div>
    <h2 style="color:#fff; margin-bottom:8px;">Wybierz swój pierwszy klub</h2>
    <p class="muted" style="margin-bottom:16px;">Kliknij ofertę, aby przejść do negocjacji warunków.</p>
    <div style="max-height: 50vh; overflow-y: auto; padding-right: 4px;">
      ${offers.map(o => {
        const clubIdValue = o.clubId !== undefined ? o.clubId : (o.id !== undefined ? o.id : o.club);
        return `
          <button class="ghost offer-btn" data-clubid="${clubIdValue}" data-clubname="${esc(o.club)}" data-wage="${o.wage || 3000}" style="width:100%; margin-bottom:8px; text-align:left; border-radius:12px;">
            <b>${esc(o.club)}</b><br>
            <span style="font-size:0.75rem; color:var(--text-muted);">
              ${o.league ? esc(o.league) + ' • ' : ''} Oferowana pensja: ${o.wage ? Number(o.wage).toLocaleString() : 0} PLN/tydz.
            </span>
          </button>
        `;
      }).join('')}
    </div>
  `);

  document.querySelectorAll('.offer-btn').forEach(b => {
    b.onclick = () => {
      const selectedClub = b.dataset.clubid;
      const parsedId = !isNaN(selectedClub) ? Number(selectedClub) : selectedClub;
      const clubName = b.dataset.clubname;
      const baseWage = Number(b.dataset.wage);
      
      openNegotiationModal(parsedId, clubName, baseWage);
    };
  });
}

window.openNegotiationModal = function(clubId, clubName, baseWage, initialPatience = 100, alertMsg = '') {
  showModal(`
    <div class="eyebrow">NEGOCJACJE KONTRAKTU</div>
    <h2 style="color:#fff; margin-bottom:4px;">${esc(clubName)}</h2>
    <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:12px;">
      Cierpliwość zarządu: <b style="color:${initialPatience > 50 ? 'var(--accent-green)' : '#ef4444'};">${initialPatience}%</b>
    </p>

    ${alertMsg ? `<div style="background:rgba(239, 68, 68, 0.15); border:1px solid #ef4444; color:#fff; padding:8px 12px; border-radius:8px; font-size:0.75rem; margin-bottom:12px;">${alertMsg}</div>` : ''}

    <div style="margin-bottom:10px;">
      <label style="font-size:0.75rem; color:var(--text-muted);">ŻĄDANA PENSJA TYGODNIOWA (PLN):</label>
      <input type="number" id="neg-wage" value="${baseWage}" style="width:100%; padding:10px; margin-top:4px; background:rgba(0,0,0,0.3); border:1px solid var(--border-color); color:#fff; border-radius:8px; font-weight:bold;">
    </div>

    <div style="margin-bottom:12px;">
      <label style="font-size:0.75rem; color:var(--text-muted);">PREMIA ZA GOLA / ASYSTĘ (PLN):</label>
      <input type="number" id="neg-bonus" value="300" style="width:100%; padding:10px; margin-top:4px; background:rgba(0,0,0,0.3); border:1px solid var(--border-color); color:#fff; border-radius:8px; font-weight:bold;">
    </div>

    <button class="action primaryAction" style="width:100%; padding:12px; margin-top:4px;" onclick="window.submitContractOffer('${clubId}', '${esc(clubName)}', ${initialPatience})">
      📑 PRZEDSTAW WARUNKI
    </button>
    <button class="action" style="width:100%; margin-top:6px;" onclick="closeModal()">ANULUJ</button>
  `);
};

window.submitContractOffer = async function(clubId, clubName, patience) {
  const wage = Number($('neg-wage')?.value || 0);
  const bonus = Number($('neg-bonus')?.value || 0);
  const parsedId = !isNaN(clubId) ? Number(clubId) : clubId;

  try {
    const res = await api('/contract/negotiate', { 
      method: 'POST', 
      body: JSON.stringify({ 
        clubId: parsedId, 
        wage, 
        bonus, 
        patience 
      }) 
    });

    if (res.success) {
      closeModal();
      openGame();
      audio('win');
      vib([30, 50, 30]);
      toast(res.message);
      updateStateAndUI(res.state);
    } else if (res.rejected) {
      closeModal();
      vib(100);
      toast(res.message);
      updateStateAndUI(res.state);
    } else {
      vib(40);
      openNegotiationModal(clubId, clubName, res.counterWage || wage, res.patience, res.message);
    }
  } catch (e) {
    toast(e.message);
  }
};

async function saveGame() {
  try {
    const snap = await api('/save');
    localStorage.setItem('fps_slot1', JSON.stringify(snap));
    toast('Zapisano karierę');
    vib(20);
  } catch (e) { 
    toast(e.message); 
  }
}

function updateStateAndUI(newState) {
  S = newState;
  renderAll();
}

function renderAll() {
  if (!S) return;
  
  if (S.calendar && S.club) {
    const sLabel = $('seasonLabel');
    const cLabel = $('clubLabel');
    
    if (sLabel) {
      sLabel.textContent = `${S.calendar.season} • KOLEJKA ${S.calendar.matchday}/${S.calendar.totalMatchdays || 30}`;
    }
    if (cLabel) {
      cLabel.textContent = S.club.name || '—';
    }
  }
  
  const activeScreen = document.querySelector('.screen.active');
  if (activeScreen) {
    renderScreen(activeScreen.id.replace('screen-', ''));
  }
  updateCustomUI(S);
}

window.renderAll = renderAll;

function renderScreen(name) {
  if (!S) return;
  ({
    home: renderHome, 
    career: renderCareer, 
    club: renderClub,
    world: renderWorld, 
    cups: renderCups, 
    national: renderNational, 
    profile: renderProfile
  }[name] || renderHome)();
}

function renderHome() {
  const f = S.fixture;
  $('screen-home').innerHTML = `
    <div class="home-hero">
      <div class="eyebrow">${esc(S.club?.league || 'Liga')} • ${S.club?.position || 1}. MIEJSCE</div>
      <div class="matchline">
        <div>
          <div class="name">
            ${esc(S.player?.name || 'Gracz')} 
            <span style="font-size:0.85rem; color:var(--accent-neon);">#${S.player?.number || 10}</span>
          </div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">
            ${S.player?.age || 18} lat • ${S.player?.position || 'ST'} • potencjał ${S.player?.potential || 80}
          </div>
        </div>
        <div class="ovr">${S.player?.ovr || 60}<small>OVR</small></div>
      </div>
      <div class="statgrid">
        <div class="mini">
          <span>FORMA</span>
          <b>${S.player?.form || 70}</b>
          <div class="meter"><span style="width:${S.player?.form || 70}%"></span></div>
        </div>
        <div class="mini">
          <span>KONDYCJA</span>
          <b>${S.player?.condition || 100}</b>
          <div class="meter"><span style="width:${S.player?.condition || 100}%"></span></div>
        </div>
      </div>
    </div>

    ${S.player?.injured ? `
      <div class="match" style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.05);">
        <div class="eyebrow" style="color:#ef4444;">🚑 KONTUZJA</div>
        <h3 style="color:#fff; margin-top:4px;">Jesteś niedostępny do gry</h3>
        <p style="font-size:0.8rem; color:var(--text-muted); margin-top:6px;">Przechodzisz rekonwalescencję. Możesz przyspieszyć powrót na boisko lub odczekać swoje.</p>

        ${(S.finances?.balance ?? 0) >= 15000 ? `
          <button class="primaryAction big" style="width:100%; margin-top:12px; padding:12px; background: linear-gradient(135deg, #ef4444, #dc2626); color:white; border:none; border-radius:8px; cursor:pointer;" onclick="window.buyRehab()">
            🏥 Prywatna Rehabilitacja (15 000 PLN)
          </button>
        ` : `
          <button class="primaryAction big" style="width:100%; margin-top:12px; padding:12px; background: #374151; color: #9ca3af; border:none; border-radius:8px; cursor:not-allowed;" disabled>
            🔒 Brak środków na rehabilitację (Wymagane 15k PLN)
          </button>
        `}

        <button class="secondaryAction" style="width:100%; margin-top:8px; padding:10px; background: #1f2937; color: #fff; border: 1px solid #4b5563; border-radius: 8px; cursor: pointer;" onclick="window.simulate()">
          ⏭️ Odpocznij i przejdź dalej (Naturalny powrót)
        </button>
      </div>
    ` : S.calendar?.seasonFinished ? `
      <div class="match">
        <h3>🏁 KONIEC SEZONU</h3>
        <p style="font-size:0.85rem; color:var(--text-muted); margin-top:6px;">Rozgrywki zakończone. Podejmij decyzję o swojej przyszłości.</p>
        <button class="primaryAction big" style="width:100%; margin-top:12px; padding:14px;" onclick="seasonModal()">PRZEJDŹ DO OKNA DECYZJI</button>
      </div>
    ` : `
      <div class="match">
        <div class="eyebrow">NASTĘPNY MECZ</div>
        <div class="matchline" style="margin-top:12px;">
          <span style="font-weight:700;">${esc(f?.home || '—')}</span>
          <span style="color:var(--text-muted); font-size:0.8rem;">VS</span>
          <span style="font-weight:700;">${esc(f?.away || '—')}</span>
        </div>
        <div class="actions">
          <button class="action" onclick="trainingModal()">🏋️ TRENING</button>
          <button class="action primaryAction" onclick="simulate()">▶ ROZEGRAJ</button>
        </div>
        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:10px; text-align:center;">
          ${S.player?.squadStatus === 'start' ? '🟢 Startowa XI' : S.player?.squadStatus === 'bench' ? '🟡 Ławka' : '🔴 Poza kadrą'} • trening ${S.trainingUsed ? 'wykorzystany' : 'dostępny'}
        </div>
      </div>
    `}

    <div class="section">
      <div class="eyebrow">RELACJE, FINANSE & SZATNIA</div>
      <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-top:10px; flex-wrap:wrap; gap:8px;">
        <div>💰 Portfel: <strong id="fin-balance">0</strong> PLN</div>
        <div>🤝 Chemia: <strong>${S.teamChemistry || 70}%</strong></div>
        <div>👔 Trener: <strong id="trust-val">50</strong>/100</div>
        <div>📣 Kibice: <strong id="approval-val">50</strong>/100</div>
      </div>
    </div>

    <div class="section">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div class="eyebrow" style="margin:0;">DRZEWKO UMIEJĘTNOŚCI</div>
        <span style="font-size:0.75rem; color:var(--accent-neon); font-weight:700;">Punkty: <span id="skill-points">0</span></span>
      </div>
      <div id="perks-container"></div>
    </div>

    <div class="section" style="display:flex; gap:8px; flex-wrap:wrap;">
      <button class="action" onclick="buyTrainer()">🏋️ Osobisty Trener (10k)</button>
      <button class="action" onclick="upgradeAgent()">🕶️ Lepszy Agent</button>
      <button class="action" onclick="sponsorModal()">🤝 Sponsorzy</button>
      <button class="action primaryAction" onclick="lifestyleModal()">🏎️ Styl Życia</button>
    </div>

    <div class="section">
      <div class="eyebrow">FEED SOCIAL MEDIA (X/TWITTER)</div>
      <div style="margin-top:8px;">
        ${(S.socialFeed || []).map(sf => `
          <div style="padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05); font-size:0.8rem;">
            <b style="color:var(--accent-neon);">@${esc(sf.author)}:</b> ${esc(sf.text)}
          </div>
        `).join('')}
      </div>
    </div>

    <div class="section">
      <div class="eyebrow">PRZEBIEG OSTATNIEGO MECZU</div>
      <ul id="match-log-list" style="list-style:none; padding:0; font-size:0.8rem; margin-top:10px; color:var(--text-muted);">
        <li>Brak logów z ostatniego meczu.</li>
      </ul>
    </div>

    <div class="section">
      <div class="eyebrow">CENTRUM WYDARZEŃ</div>
      ${(S.news || []).slice(0, 5).map(n => `
        <div style="margin-top:10px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.05);">
          <small style="color:var(--text-muted); font-size:0.65rem;">${esc(n.season || '')} • ${esc(n.type || '')}</small>
          <p style="font-size:0.85rem; margin-top:4px;">${esc(n.text || '')}</p>
        </div>
      `).join('')}
    </div>
  `;
}

window.simulate = async function() {
  try {
    const triggerEvent = Math.random() < 0.40;
    
    if (triggerEvent && S.player?.squadStatus !== 'out' && !S.player?.injured) {
      showMatchDecisionModal();
      return;
    }

    const d = await api('/match/simulate', { method: 'POST' });
    S = d.state || d;
    const r = d.result;
    
    if (r) {
      const mineHome = r.home === S.club?.name;
      const win = mineHome ? r.homeGoals > r.awayGoals : r.awayGoals > r.homeGoals;
      audio(win ? 'goal' : 'click');
      vib(win ? [30, 50, 30] : [80, 30]);
      toast(`${r.home} ${r.homeGoals}:${r.awayGoals} ${r.away}`);
    }
    
    if (S.calendar?.seasonFinished) {
      seasonModal();
    }
    renderAll();
  } catch (e) { 
    toast(e.message); 
  }
};

const MATCH_SCENARIOS = [
  {
    type: "counterattack",
    titles: ["Wychodzisz z kontratakiem!", "Błyskawiczne natarcie!", "Szybka kontra zespołu!"],
    minRange: [20, 85],
    desc: "Masz przed sobą tylko jednego obrońcę i nadbiegającego partnera. Czas podjąć decyzję w ułamku sekundy.",
    options: [
      { id: 'shoot', text: '⚽ STRZAŁ Z DYSTANSU (Średnie ryzyko)', style: 'primaryAction' },
      { id: 'pass', text: '🎯 PODANIE DO PARTNERA (Niskie ryzyko)', style: 'ghost' },
      { id: 'dribble', text: '🔥 PRÓBA DRYBLINGU (Wysokie ryzyko)', style: 'ghost' }
    ]
  },
  {
    type: "one_on_one",
    titles: ["SAM NA SAM Z BRAMKARZEM!", "W sytuacji sam na sam!", "Okazja życia pod bramką!"],
    minRange: [10, 90],
    desc: "Bramkarz wychodzi z bramki, zmniejszając kąt. Jak wykończysz tę sytuację?",
    options: [
      { id: 'dribble', text: '🪄 LOB NAD BRAMKARZEM (Ekstremalne ryzyko)', style: 'ghost' },
      { id: 'shoot', text: '🚀 SILNY STRZAŁ W OKIENKO (Wysokie ryzyko)', style: 'primaryAction' },
      { id: 'pass', text: '🎯 PRECYZYJNY STRZAŁ PO ZIEMI (Bezpieczny)', style: 'ghost' }
    ]
  },
  {
    type: "free_kick",
    titles: ["RZUT WOLNY Z IDEALNEJ POZYCJI!", "Stały fragment gry!", "Faul tuż przed polem karnym!"],
    minRange: [15, 88],
    desc: "Piłka leży na 20 metrze od bramki. Mur rywali jest dobrze ustawiony.",
    options: [
      { id: 'shoot', text: '⚡ BEZPOŚREDNI STRZAŁ NAD MUREM (Wysokie ryzyko)', style: 'primaryAction' },
      { id: 'dribble', text: '🌀 TECHNICZNY STRZAŁ W RÓG (Średnie ryzyko)', style: 'ghost' },
      { id: 'pass', text: '🤝 KRÓTKIE ROZEGRANIE Z KOLEGĄ (Niskie ryzyko)', style: 'ghost' }
    ]
  },
  {
    type: "pressing",
    titles: ["Agresywny pressing!", "Szansa na odbiór piłki!", "Błąd obrońcy rywala!"],
    minRange: [5, 80],
    desc: "Obrońca rywali ospale przyjmuje piłkę pod własnym polem karnym. Możesz go zaatakować.",
    options: [
      { id: 'dribble', text: '💥 AGRESYWNY WTEK / ODBIÓR (Ryzyko kartki)', style: 'ghost' },
      { id: 'pass', text: '🛡️ ODCIĘCIE PODANIA I PRESSING (Taktyczne)', style: 'primaryAction' },
      { id: 'shoot', text: '👀 ASEKURACJA / ODPUSZCZENIE (Bezpieczne)', style: 'ghost' }
    ]
  },
  {
    type: "playmaking",
    titles: ["Przełomowe podanie w środku pola!", "Akcja playmaker'a!", "Przegląd pola i wizja gry."],
    minRange: [25, 75],
    desc: "Masz piłkę na 30 metrze. Widzisz lukę w defensywie przeciwnika.",
    options: [
      { id: 'dribble', text: '🎯 PRZERZUT ZA PLECY OBROŃCÓW (Ryzykowne)', style: 'ghost' },
      { id: 'pass', text: '⚡ PROSTOPADŁE PODANIE PO ZIEMI (Kluczowe)', style: 'primaryAction' },
      { id: 'shoot', text: '🔄 BEZPIECZNE ROZEGRANIE DO TYŁU (Zachowawcze)', style: 'ghost' }
    ]
  }
];

window.showMatchDecisionModal = function() {
  const scenario = MATCH_SCENARIOS[Math.floor(Math.random() * MATCH_SCENARIOS.length)];
  const min = Math.floor(Math.random() * (scenario.minRange[1] - scenario.minRange[0] + 1)) + scenario.minRange[0];
  const title = scenario.titles[Math.floor(Math.random() * scenario.titles.length)];

  const buttonsHtml = scenario.options.map(opt => `
    <button class="${opt.style === 'primaryAction' ? 'action primaryAction' : 'ghost'}" 
            style="width:100%; margin-bottom:8px; padding:12px;" 
            onclick="window.makeMatchChoice('${opt.id}')">
      ${opt.text}
    </button>
  `).join('');

  showModal(`
    <div class="eyebrow">⚡ KLUCZOWY MOMENT MECZU (${min}')</div>
    <h2 style="color:#fff; margin-bottom:8px;">${title}</h2>
    <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:16px;">
      ${scenario.desc}
    </p>
    ${buttonsHtml}
  `);
};

window.makeMatchChoice = async function(action) {
  try {
    const res = await api('/match/choice', { 
      method: 'POST', 
      body: JSON.stringify({ action }) 
    });
    closeModal();
    
    if (res.success) {
      audio('goal');
      vib([30, 50, 30]);
    } else {
      vib(50);
    }
    
    toast(res.message);
    
    const d = await api('/match/simulate', { method: 'POST' });
    S = d.state || d;
    
    if (S.calendar?.seasonFinished) {
      seasonModal();
    }
    renderAll();
  } catch (e) {
    toast(e.message);
  }
};

window.trainingModal = function() {
  if (S.trainingUsed) {
    return toast('Trening w tej kolejce już wykorzystany');
  }
  
  const trainingTypes = [
    { id: 'TECHNIQUE', title: '🎯 Indywidualne Szkolenie Techniczne', desc: '+technika, drybling, precyzja podania', badge: 'Podstawa' },
    { id: 'PHYSICAL', title: '💪 Katowanie Siłowni & Wytrzymałość', desc: '+szybkość, stamina, siła fizyczna', badge: 'Wyczerpujące' },
    { id: 'SHOOTING', title: '🚀 Intensywna Sesja Strzelecka', desc: '+wykończenie, siła strzału', badge: 'Efektowne' },
    { id: 'TACTICAL', title: '🧠 Odprawa Taktyczna i Wizja Gry', desc: '+pozycjonowanie, czytanie gry', badge: 'Mądre' },
    { id: 'RECOVERY', title: '🛌 Komnata Odnowy Biologicznej', desc: '+szybsza regeneracja kondycji', badge: 'Zdrowie' }
  ];

  const recommended = trainingTypes[Math.floor(Math.random() * trainingTypes.length)];

  const buttonsHtml = trainingTypes.map(x => {
    const isRec = x.id === recommended.id;
    const highlightStyle = isRec ? 'border: 1px solid #10b981; background: rgba(16, 185, 129, 0.08);' : '';
    const badgeHtml = isRec ? '<span style="float:right; color:#10b981; font-size:0.65rem; font-weight:bold;">🔥 POLECANE PRZEZ TRENERA (+Bonus)</span>' : '';
    
    return `
      <button class="ghost" data-focus="${x.id}" style="width:100%; margin-bottom:8px; text-align:left; border-radius:12px; ${highlightStyle}">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <b>${x.title}</b>
          <span style="font-size:0.65rem; background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:4px;">${x.badge}</span>
        </div>
        ${badgeHtml}
        <div style="font-size:0.7rem; color:var(--text-muted); margin-top:2px;">${x.desc}</div>
      </button>
    `;
  }).join('');

  showModal(`
    <div class="eyebrow">ROZWÓJ OSOBISTY</div>
    <h2>Wybierz plan treningowy</h2>
    <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:12px;">Masz jedną sesję na kolejkę. Wybierz mądrze!</p>
    <div style="max-height: 55vh; overflow-y: auto; padding-right: 4px;">
      ${buttonsHtml}
    </div>
    <button class="action" style="width:100%; margin-top:12px;" onclick="closeModal()">ANULUJ</button>
  `);

  document.querySelectorAll('[data-focus]').forEach(b => {
    b.onclick = async () => {
      try {
        const focusId = b.dataset.focus;
        S = await api('/training', { 
          method: 'POST', 
          body: JSON.stringify({ focus: focusId }) 
        });
        
        closeModal(); 
        toast('Trening wykonany pomyślnie!'); 
        vib(18); 
        renderAll();
      } catch (e) { 
        toast(e.message); 
      }
    };
  });
};

function renderCareer() {
  const d = (S.seasonHistory || []).map(h => `
    <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
      <div>
        <b>${esc(h.season)}</b><br>
        <span style="font-size:0.75rem; color:var(--text-muted);">${esc(h.club)} • ${h.minutes} min • ${h.goals} goli</span>
      </div>
      <b style="color:var(--accent-neon);">${h.ovrBefore} → ${h.ovrAfter}</b>
    </div>
  `).join('');

  $('screen-career').innerHTML = `
    <div class="section">
      <div class="eyebrow">KARIERA</div>
      <h2>Twoja historia</h2>
      <div class="statgrid">
        <div class="mini"><span>MECZE</span><b>${S.stats?.matches || 0}</b></div>
        <div class="mini"><span>MINUTY</span><b>${S.stats?.minutes || 0}</b></div>
        <div class="mini"><span>GOLE</span><b>${S.stats?.goals || 0}</b></div>
        <div class="mini"><span>ASYSTY</span><b>${S.stats?.assists || 0}</b></div>
      </div>
    </div>
    <div class="section">
      <h3>Historia sezonów</h3>
      ${d || '<div style="font-size:0.8rem; color:var(--text-muted); margin-top:10px;">Pierwszy sezon w trakcie...</div>'}
    </div>
  `;
}

async function renderClub() {
  try {
    const d = await api('/squad');
    $('screen-club').innerHTML = `
      <div class="eyebrow">${esc(S.club?.name || 'Klub')}</div>
      <h2>Kadra zespołu</h2>
      ${[['STARTOWA XI', d.starting || []], ['ŁAWKA', d.bench || []], ['POZA KADRĄ', d.out || []]].map(([t, arr]) => `
        <div class="section">
          <h3>${t}</h3>
          ${arr.map(p => `
            <div style="display:flex; align-items:center; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.03); ${p.mine ? 'color:var(--accent-green); font-weight:bold;' : ''}">
              <span style="width:32px; font-size:0.8rem; font-weight:bold; color:var(--accent-neon);">#${p.number || '?'}</span>
              <span style="width:40px; font-size:0.75rem; color:var(--text-muted);">${esc(p.position)}</span>
              <div style="flex:1;">
                ${esc(p.name)} <small style="font-size:0.65rem; color:var(--text-muted);">(${p.age || 20} l.)</small>
              </div>
              <b>${p.ovr} OVR</b>
            </div>
          `).join('')}
        </div>
      `).join('')}
    `;
  } catch (e) { 
    toast(e.message); 
  }
}

async function renderWorld() {
  try {
    const ls = await api('/leagues');
    $('screen-world').innerHTML = `
      <div class="eyebrow">ŻYWY ŚWIAT</div>
      <h2>Rozgrywki ligowe</h2>
      <div style="display:flex; gap:8px; overflow-x:auto; margin:14px 0;">
        ${ls.map(l => `<button class="action ${l.name === league ? 'primaryAction' : ''}" style="padding:8px 14px; white-space:nowrap; width:auto;" onclick="window.setLeague('${esc(l.name)}')">${esc(l.name)}</button>`).join('')}
      </div>
      <div id="worldTable"></div>
    `;
    const rows = await api('/table?league=' + encodeURIComponent(league));
    $('worldTable').innerHTML = `
      <div class="section" style="padding:10px;">
        <table style="width:100%; border-collapse:collapse; font-size:0.8rem;">
          <thead>
            <tr style="color:var(--text-muted); border-bottom:1px solid var(--border-color);">
              <th style="text-align:left; padding:8px;">#</th>
              <th style="text-align:left;">KLUB</th>
              <th>M</th>
              <th>PKT</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(r => `
              <tr style="border-bottom:1px solid rgba(255,255,255,0.03); ${r.mine ? 'color:var(--accent-green); font-weight:800;' : ''}">
                <td style="padding:8px;">${r.pos}</td>
                <td>${esc(r.club)}</td>
                <td style="text-align:center;">${r.played || 0}</td>
                <td style="text-align:center;"><b>${r.pts}</b></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) { 
    toast(e.message); 
  }
}

window.setLeague = function(lName) { 
  league = lName; 
  renderWorld(); 
};

function renderCups() {
  const europeHTML = S.europe ? Object.entries(S.europe).map(([cupName, info]) => `
    <div class="section" style="margin-top:10px;">
      <b>🌍 ${esc(cupName)}</b><br>
      <span style="font-size:0.75rem; color:var(--accent-neon); display:inline-block; margin-top:4px;">${info.rounds || 0} RUND ROZEGRANYCH</span>
      ${info.champion ? `<div style="margin-top:4px; font-weight:bold; color:var(--accent-green);">Zwycięzca: ${esc(info.champion)}</div>` : ''}
    </div>
  `).join('') : '';

  $('screen-cups').innerHTML = `
    <div class="eyebrow">TROFEA & GABLIOTA</div>
    <h2>Puchary i Osiągnięcia</h2>
    <div class="section">
      <b>🏆 Puchar Polski</b><br>
      <span style="font-size:0.75rem; color:var(--accent-neon); display:inline-block; margin-top:6px;">${S.cup?.rounds || 0} RUND ROZEGRANYCH</span>
      ${S.cup?.champion ? `<div style="margin-top:6px; font-weight:bold;">Zwycięzca: ${esc(S.cup.champion)}</div>` : ''}
    </div>
    
    ${europeHTML}

    <div class="section" style="margin-top:16px;">
      <b>🥇 Zdobyte Trofea (${S.trophies?.length || 0})</b>
      <div style="margin-top:8px;">
        ${(S.trophies || []).map(t => `<div style="font-size:0.8rem; padding:4px 0;">✨ ${esc(t.name)} (${esc(t.season)})</div>`).join('') || '<div style="font-size:0.75rem; color:var(--text-muted);">Brak trofeów w gablocie.</div>'}
      </div>
    </div>
  `;
}

function renderNational() {
  $('screen-national').innerHTML = `
    <div class="eyebrow">POLSKA</div>
    <h2>Reprezentacja</h2>
    ${Object.entries(S.national || {}).map(([tier, x]) => `
      <div class="section">
        <div class="matchline">
          <b>🇵🇱 ${esc(tier)}</b> 
          <span style="font-size:0.75rem; font-weight:bold; color:${x.called ? 'var(--accent-green)' : 'var(--text-muted)'};">${x.called ? 'POWOŁANY' : 'BRAK POWOŁANIA'}</span>
        </div>
        <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Rozegrane mecze: ${x.matches || 0}</div>
        ${x.lastResult ? `<div style="font-size:0.75rem; color:var(--accent-neon); margin-top:2px;">Ostatni wynik: ${esc(x.lastResult)}</div>` : ''}
      </div>
    `).join('')}
  `;
}

function renderProfile() {
  $('screen-profile').innerHTML = `
    <div class="eyebrow">KARTA FUT & USTAWIENIA</div>
    <h2>Mój profil</h2>
    <div style="background: linear-gradient(135deg, #f59e0b, #b45309); padding:20px; border-radius:16px; text-align:center; color:#fff; width:200px; margin:0 auto 20px auto; border:2px solid #fef08a;">
      <h1 style="font-size:2.8rem; margin:0; font-weight:900;">${S.player?.ovr || 60}</h1>
      <div style="font-weight:bold; font-size:1.1rem;">${S.player?.position || 'ST'}</div>
      <h3 style="margin:10px 0 0 0; text-transform:uppercase;">${esc(S.player?.lastName || 'Gracz')}</h3>
    </div>
    <div class="section">
      <div class="statgrid">
        <div class="mini"><span>OVR</span><b>${S.player?.ovr || 60}</b></div>
        <div class="mini"><span>POTENCJAŁ</span><b>${S.player?.potential || 80}</b></div>
        <div class="mini"><span>PRESTIŻ</span><b>${S.lifestyle?.prestige || 0} pkt</b></div>
        <div class="mini"><span>NUMER</span><b>#${S.player?.number || 10}</b></div>
      </div>
      <p style="font-size:0.85rem; color:var(--text-muted); margin-top:16px;">
        Klub: ${esc(S.club?.name || '—')}<br>
        Wiek: ${S.player?.age || 18} lat
      </p>
    </div>
    <button class="primaryAction big" style="width:100%; padding:16px; border-radius:14px;" onclick="saveGame()">💾 ZAPISZ GRĘ</button>
  `;
}

window.seasonModal = function() {
  const offers = (S.pendingTransferOffers && S.pendingTransferOffers.length > 0) ? S.pendingTransferOffers : (S.offers || []);
  
  showModal(`
    <div class="eyebrow">🏁 KONIEC SEZONU</div>
    <h2 style="color:#fff; margin-bottom:12px;">Podejmij decyzję</h2>
    
    <button class="primaryAction big" style="width:100%; margin-bottom:16px; padding:14px;" onclick="window.finishSeason('stay')">
      ZOSTAJĘ W ${esc(S.club?.name || 'KLUBIE')}
    </button>

    ${offers.length > 0 ? `
      <div class="eyebrow" style="margin-top:12px; color:var(--accent-neon);">OFERTY TRANSFEROWE:</div>
      <div style="max-height: 45vh; overflow-y: auto; padding-right: 4px;">
        ${offers.map(o => {
          const clubId = o.clubId !== undefined ? o.clubId : o.id;
          return `
            <button class="ghost season-offer-btn" data-clubid="${clubId}" data-clubname="${esc(o.club)}" data-wage="${o.wage || 3500}" style="width:100%; margin-top:8px; text-align:left; padding:12px; border-radius:12px;">
              <b>${esc(o.club)}</b> <span style="font-size:0.75rem; color:var(--text-muted);">(${esc(o.league || '')})</span><br>
              <span style="font-size:0.75rem; color:var(--accent-green);">Sugerowana pensja: ${o.wage ? Number(o.wage).toLocaleString() : 0} PLN/tydz.</span>
            </button>
          `;
        }).join('')}
      </div>
    ` : '<p style="font-size:0.8rem; color:var(--text-muted);">Brak nowych ofert transferowych w tym sezonie.</p>'}
  `);

  document.querySelectorAll('.season-offer-btn').forEach(btn => {
    btn.onclick = () => {
      const rawId = btn.dataset.clubid;
      const parsedId = !isNaN(rawId) ? Number(rawId) : rawId;
      const clubName = btn.dataset.clubname;
      const baseWage = Number(btn.dataset.wage);

      openNegotiationModal(parsedId, clubName, baseWage);
    };
  });
};

window.finishSeason = async function(decision, clubId = null) {
  try {
    const payload = { decision };
    if (decision === 'transfer' && clubId !== null) {
      payload.clubId = clubId;
    }

    const res = await api('/season/decision', { 
      method: 'POST', 
      body: JSON.stringify(payload) 
    });

    S = res.state || res;
    closeModal();
    toast(decision === 'transfer' ? 'Przeszedłeś do nowego klubu!' : 'Rozpoczęto nowy sezon!');
    vib([20, 40, 20]);
    audio('win');
    renderAll();
  } catch (e) {
    toast(e.message || 'Nie udało się przetworzyć decyzji');
  }
};

function updateCustomUI(state) {
  if (!state) return;
  if ($('fin-balance') && state.finances) {
    $('fin-balance').innerText = Number(state.finances.balance || 0).toLocaleString();
  }
  if ($('trust-val') && state.relationships) {
    $('trust-val').innerText = state.relationships.managerTrust || 50;
  }
  if ($('approval-val') && state.relationships) {
    $('approval-val').innerText = state.relationships.fanApproval || 50;
  }
  if ($('skill-points')) {
    $('skill-points').innerText = state.skillPoints || 0;
  }

  const matchLog = $('match-log-list');
  if (matchLog) {
    matchLog.innerHTML = (state.lastMatchLog && state.lastMatchLog.length > 0) 
      ? state.lastMatchLog.map(m => `<li style="padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05);">${esc(m)}</li>`).join('')
      : '<li>Brak logów z ostatniego meczu.</li>';
  }

  const perksContainer = $('perks-container');
  if (perksContainer && state.perks) {
    perksContainer.innerHTML = `
      <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:10px; margin-top:14px;">
        ${state.perks.map(p => `
          <div style="background:rgba(255,255,255,0.03); border:1px solid ${p.unlocked ? 'var(--accent-green)' : 'var(--border-color)'}; border-radius:14px; padding:12px; display:flex; flex-direction:column; justify-content:space-between;">
            <div>
              <div style="font-size:0.8rem; font-weight:800; color:#fff; margin-bottom:4px;">${esc(p.name)}</div>
              <div style="font-size:0.65rem; color:var(--text-muted); margin-bottom:10px; line-height:1.3;">${esc(p.desc)}</div>
            </div>
            ${!p.unlocked 
              ? `<button class="action primaryAction" style="padding:8px; font-size:0.7rem; border-radius:10px;" onclick="unlockPerk('${p.id}')" ${state.skillPoints < p.cost ? 'style="opacity:0.4; pointer-events:none;"' : ''}>KUP (${p.cost} pkt)</button>` 
              : `<span style="font-size:0.7rem; color:var(--accent-green); font-weight:800; text-align:center;">✓ ODBLOKOWANO</span>`}
          </div>
        `).join('')}
      </div>
    `;
  }
}

window.buyRehab = async function() {
  try {
    const res = await api('/player/rehab', { method: 'POST' });
    updateStateAndUI(res);
    audio('win');
    vib([30, 40, 30]);
    toast('Zabieg rehabilitacyjny zakończony sukcesem!');
  } catch (e) {
    toast(e.message || 'Nie udało się przeprowadzić rehabilitacji');
  }
};

window.unlockPerk = async function(perkId) {
  try {
    const data = await api('/perk/unlock', { 
      method: 'POST', 
      body: JSON.stringify({ perkId }) 
    });
    audio('perk'); 
    updateStateAndUI(data); 
    toast('Odblokowano nową cechę!');
  } catch (e) { 
    toast(e.message); 
  }
};

window.buyTrainer = async function() {
  try { 
    const data = await api('/finance/buy-trainer', { method: 'POST' }); 
    updateStateAndUI(data); 
    toast('Zatrudniono trenera!'); 
  } catch (e) { 
    toast(e.message); 
  }
};

window.upgradeAgent = async function() {
  try { 
    const data = await api('/finance/upgrade-agent', { method: 'POST' }); 
    updateStateAndUI(data); 
    toast('Agent awansował!'); 
  } catch (e) { 
    toast(e.message); 
  }
};

window.sponsorModal = function() {
  const sponsors = S.sponsors || [];
  const currentSponsor = S.activeSponsor;

  showModal(`
    <div class="eyebrow">UMOWY SPONSORSKIE</div>
    <h2 style="color:#fff; margin-bottom:8px;">KONTRAKTY REKLAMOWE</h2>
    <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:14px;">
      Twój Prestiż: <b style="color:var(--accent-neon);">${S.lifestyle?.prestige || 0} pkt</b>
    </p>
    <div style="max-height: 55vh; overflow-y: auto; padding-right: 4px;">
      ${sponsors.map(sp => {
        const isCurrent = currentSponsor === sp.id;
        const canSign = (S.lifestyle?.prestige || 0) >= sp.req_prestige;
        return `
          <div style="background:rgba(255,255,255,0.03); border:1px solid var(--border-color); border-radius:12px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <b>${sp.name}</b><br>
              <span style="font-size:0.7rem; color:var(--text-muted);">${sp.desc}</span><br>
              <b style="font-size:0.75rem; color:var(--accent-green);">+${sp.pay.toLocaleString()} PLN / tydzień</b>
            </div>
            ${isCurrent 
              ? `<span style="font-size:0.75rem; color:var(--accent-green); font-weight:bold;">✓ AKTYWNY</span>`
              : `<button class="action primaryAction" style="padding:6px 12px; font-size:0.75rem; ${!canSign ? 'opacity:0.4; pointer-events:none;' : ''}" onclick="window.signSponsor('${sp.id}')">PODPISZ</button>`
            }
          </div>
        `;
      }).join('')}
    </div>
    <button class="action" style="width:100%; margin-top:10px;" onclick="closeModal()">ZAMKNIJ</button>
  `);
};

window.signSponsor = async function(sponsorId) {
  try {
    const data = await api('/sponsor/sign', { 
      method: 'POST', 
      body: JSON.stringify({ sponsorId }) 
    });
    audio('win');
    vib([30, 30]);
    updateStateAndUI(data);
    closeModal();
    toast('Umowa sponsorska podpisana!');
  } catch (e) {
    toast(e.message);
  }
};

window.lifestyleModal = function() {
  const items = [
    { id: 'watch_rolex', name: '⌚ Zegarek Rolex', cost: 25000, desc: '+5 Prestiż, +3 Kibice' },
    { id: 'watch_richard_mille', name: '💎 Zegarek Richard Mille', cost: 300000, desc: '+25 Prestiż, -5 Kibice, -2 Trener' },
    { id: 'chain', name: '⛓️ Złoty Łańcuch z Diamentami', cost: 80000, desc: '+12 Prestiż, -2 Kibice, -1 Trener' },
    { id: 'sunglasses', name: '🕶️ Designer Sunglasses', cost: 3000, desc: '+2 Prestiż, +2 Kibice' },
    { id: 'car_sport', name: '🏎️ Sportowe Auto', cost: 120000, desc: '+15 Prestiż, +8 Kibice, -2 Trener' },
    { id: 'car_supercar', name: '🔥 Włoski Supercar', cost: 350000, desc: '+30 Prestiż, +5 Kibice, -5 Trener' },
    { id: 'yacht', name: '🛥️ Jacht Motorowy', cost: 1500000, desc: '+60 Prestiż, -10 Kibice, -8 Trener' },
    { id: 'private_jet', name: '✈️ Prywatny Odrzutowiec', cost: 5000000, desc: '+100 Prestiż, -20 Kibice, -10 Trener' },
    { id: 'apartment', name: '🏙️ Penthouse w stolicy', cost: 500000, desc: '+35 Prestiż, +15 Kibice, +2 Trener' },
    { id: 'mansion', name: '🏰 Rezydencja z Basenem', cost: 2500000, desc: '+70 Prestiż, +10 Kibice' },
    { id: 'chalet', name: '⛷️ Domek w Alpejach', cost: 1200000, desc: '+45 Prestiż, +12 Kibice, +5 Trener' },
    { id: 'island', name: '🏝️ Prywatna Wyspa', cost: 10000000, desc: '+150 Prestiż, -30 Kibice, -15 Trener' },
    { id: 'pr_agency', name: '📸 Agencja PR', cost: 80000, desc: '+20 Prestiż, +20 Kibice' },
    { id: 'chef', name: '👨‍🍳 Szef Kuchni', cost: 60000, desc: '+10 Prestiż, +5 Kibice, +2 Trener' },
    { id: 'bodyguards', name: '🛡️ Ochrona 24/7', cost: 100000, desc: '+15 Prestiż, +10 Trener' },
    { id: 'charity_fund', name: '🤝 Fundacja Charytatywna', cost: 200000, desc: '+40 Prestiż, +50 Kibice, +30 Trener' }
  ];

  const owned = S.lifestyle?.owned || [];

  showModal(`
    <div class="eyebrow">STYL ŻYCIA & LUKSUS</div>
    <h2 style="color:#fff; margin-bottom:8px;">Garaż i Majątek</h2>
    <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:14px;">
      Prestiż: <b style="color:var(--accent-neon);">${S.lifestyle?.prestige || 0} pkt</b>
    </p>
    <div style="max-height: 55vh; overflow-y: auto; padding-right: 4px;">
      ${items.map(item => {
        const isOwned = owned.includes(item.id);
        return `
          <div style="background:rgba(255,255,255,0.03); border:1px solid var(--border-color); border-radius:12px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <b>${item.name}</b><br>
              <span style="font-size:0.7rem; color:var(--text-muted);">${item.desc}</span><br>
              <b style="font-size:0.75rem; color:var(--accent-green);">${item.cost.toLocaleString()} PLN</b>
            </div>
            ${isOwned 
              ? `<span style="font-size:0.75rem; color:var(--accent-green); font-weight:bold;">✓ POSIADASZ</span>`
              : `<button class="action primaryAction" style="padding:6px 12px; font-size:0.75rem;" onclick="window.buyLifestyleItem('${item.id}')">KUP</button>`
            }
          </div>
        `;
      }).join('')}
    </div>
    <button class="action" style="width:100%; margin-top:10px;" onclick="closeModal()">ZAMKNIJ</button>
  `);
};

window.buyLifestyleItem = async function(itemId) {
  try {
    const data = await api('/lifestyle/buy', { 
      method: 'POST', 
      body: JSON.stringify({ itemId }) 
    });
    audio('win');
    vib([30, 30]);
    updateStateAndUI(data);
    lifestyleModal();
    toast('Zakup zrealizowany!');
  } catch (e) {
    toast(e.message);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('#nav button').forEach(b => {
    b.onclick = () => nav(b.dataset.screen);
  });
  
  $('loadSlot')?.addEventListener('click', async e => {
    e.preventDefault();
    const raw = localStorage.getItem('fps_slot1');
    if (!raw) return toast('Brak zapisu');
    try { 
      S = await api('/load', { method: 'POST', body: raw }); 
      openGame(); 
      toast('Wczytano zapis'); 
    } catch (err) { 
      toast(err.message); 
    }
  });

  $('clearSaves')?.addEventListener('click', () => { 
    localStorage.removeItem('fps_slot1'); 
    toast('Zapis usunięty'); 
  });

  $('modal')?.addEventListener('click', e => { 
    if (e.target.id === 'modal') closeModal(); 
  });
  
  (async () => {
    try {
      S = await api('/state');
      if (S && S.created && S.club?.name) {
        openGame();
      }
    } catch (e) {}
  })();
});

# Dodawane na końcu pliku backend/app.py
def run_server(port=5000):
    app.run(host='127.0.0.1', port=port, threaded=True, debug=False)
