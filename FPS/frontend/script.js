window.addEventListener('error', e => {
  console.error(e.error || e.message);
});

/*
 * ============================================================
 * FPS FOOTBALL PLAYER
 * FRONTEND CONTROLLER
 * ============================================================
 *
 * UWAGA:
 *
 * TEN PLIK NIE JEST SILNIKIEM GRY.
 *
 * Cała logika gry znajduje się w Pythonie:
 *
 *     football_engine
 *
 * JavaScript odpowiada wyłącznie za:
 *
 * - interfejs
 * - przyciski
 * - modale
 * - animacje
 * - dźwięki
 * - ustawienia UI
 * - wysyłanie poleceń do Pythona
 * - wyświetlanie danych otrzymanych z Pythona
 *
 * JavaScript NIE:
 *
 * - symuluje meczów
 * - tworzy lig
 * - tworzy klubów
 * - tworzy zawodników
 * - liczy OVR
 * - liczy kondycji
 * - liczy tabel
 * - generuje transferów
 * - ustala wynagrodzeń
 * - ustala wartości zawodników
 * - zarządza sezonem
 * - zarządza karierą
 *
 * ============================================================
 */


/* ============================================================
   KONFIGURACJA KOMUNIKACJI Z PYTHONEM
   ============================================================ */

/*
 * Python uruchamiany lokalnie może udostępniać API np.:
 *
 * http://127.0.0.1:8000
 *
 * ZMIEŃ TYLKO TEN ADRES, jeżeli Python będzie działał
 * na innym porcie.
 */

/*
 * Domyślnie pusty string = zapytania względne (ten sam origin, na którym
 * Flask serwuje zarówno frontend jak i /api/...). To jedyny w pełni
 * bezpieczny tryb offline na Androidzie: eliminuje problem z portem
 * i pozwala ciasteczku sesji (Flask session) wracać przy każdym żądaniu.
 * Można nadpisać przez window.APP_CONFIG.API_BASE_URL w runtime-config.js,
 * np. przy debugowaniu na komputerze z osobnym serwerem deweloperskim.
 */
const ENGINE_API_BASE = (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) || '';


/*
 * Funkcja komunikacyjna.
 *
 * Nie zawiera żadnej logiki gry.
 *
 * Jej jedynym zadaniem jest wysłanie polecenia do Pythona
 * i odebranie odpowiedzi.
 */

async function engineRequest(endpoint, options = {}) {
  const url = `${ENGINE_API_BASE}${endpoint}`;

  const config = {
    method: options.method || 'GET',
    credentials: 'include', // wysyłaj ciasteczko sesji (game_id) nawet gdy API_BASE_URL jest cross-origin
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  };

  if (options.body !== undefined) {
    config.body = JSON.stringify(options.body);
  }

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      throw new Error(
        `Python API HTTP ${response.status}: ${response.statusText}`
      );
    }

    const contentType = response.headers.get('content-type') || '';

    if (contentType.includes('application/json')) {
      return await response.json();
    }

    return await response.text();

  } catch (error) {
    console.error('ENGINE API ERROR:', error);

    toast(
      'Nie można połączyć się z football_engine.'
    );

    throw error;
  }
}


/*
 * Aktualny stan gry.
 *
 * WAŻNE:
 *
 * S nie jest już tworzony przez JavaScript.
 *
 * Jest to wyłącznie kopia danych otrzymanych z Pythona,
 * potrzebna do renderowania aktualnego ekranu.
 *
 * ŹRÓDŁEM PRAWDY JEST football_engine.
 */

let S = null;


/* ============================================================
   USTAWIENIA UI
   ============================================================ */

const SETTINGS_KEY = 'fps_ui_settings';

let currentWorldLeague = null;

function loadSettings() {
  const defaults = {
    animations: true,
    sound: true,
    music: true,
    volume: 0.7,
    theme: 'dark'
  };

  try {
    return {
      ...defaults,
      ...JSON.parse(
        localStorage.getItem(SETTINGS_KEY) || '{}'
      )
    };
  } catch (e) {
    return defaults;
  }
}

let uiSettings = loadSettings();

function applySettings() {
  document.documentElement.setAttribute(
    'data-theme',
    uiSettings.theme
  );

  document.body.classList.toggle(
    'no-animations',
    !uiSettings.animations
  );
}

function saveSettings() {
  try {
    localStorage.setItem(
      SETTINGS_KEY,
      JSON.stringify(uiSettings)
    );
  } catch (e) {}
}

applySettings();


/* ============================================================
   POMOCNICZE
   ============================================================ */

let toastTimer = null;

const $ = id => document.getElementById(id);

const esc = x =>
  String(x ?? '').replace(
    /[&<>"']/g,
    m => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[m])
  );


function toast(text) {
  const el = $('toast');

  if (!el) return;

  if (toastTimer) {
    clearTimeout(toastTimer);
  }

  el.textContent = text;

  el.classList.remove('show');

  void el.offsetWidth;

  el.classList.add('show');

  toastTimer = setTimeout(
    () => el.classList.remove('show'),
    2400
  );
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


/* ============================================================
   AUDIO
   ============================================================ */

const SFX_FILES = {
  click: 'audio/sfx_click.mp3',
  whistle: 'audio/sfx_whistle.mp3',
  goal: 'audio/sfx_goal.mp3',
  perk: 'audio/sfx_perk.mp3',
  trophy: 'audio/sfx_trophy.mp3'
};

const MUSIC_FILES = {
  menu: 'audio/menu_music.mp3',
  game: 'audio/game_ambient.mp3'
};

const sfxCache = {};

function playSfx(name) {
  if (!uiSettings.sound) return;

  const src = SFX_FILES[name];

  if (!src) return;

  try {
    const base =
      sfxCache[name] ||
      (sfxCache[name] = new Audio(src));

    const el = base.cloneNode();

    el.volume = uiSettings.volume ?? 0.7;

    el.play().catch(() => {});
  } catch (e) {}
}


const musicEls = {
  menu: null,
  game: null
};

let currentMusicKey = null;

function getMusicEl(key) {
  if (!musicEls[key]) {
    const el = new Audio(MUSIC_FILES[key]);

    el.loop = true;

    musicEls[key] = el;
  }

  return musicEls[key];
}


function applyMusicVolume() {
  const vol =
    (uiSettings.volume ?? 0.7) * 0.5;

  Object.values(musicEls).forEach(el => {
    if (el) {
      el.volume = vol;
    }
  });
}


function playMusic(key) {
  if (!uiSettings.music) {
    stopMusic();
    currentMusicKey = key;
    return;
  }

  if (
    currentMusicKey === key &&
    musicEls[key] &&
    !musicEls[key].paused
  ) {
    return;
  }

  Object.entries(musicEls).forEach(
    ([k, el]) => {
      if (el && k !== key) {
        el.pause();
      }
    }
  );

  const el = getMusicEl(key);

  applyMusicVolume();

  el.play().catch(() => {});

  currentMusicKey = key;
}


function stopMusic() {
  Object.values(musicEls).forEach(el => {
    if (el) {
      el.pause();
    }
  });
}


function updateMusicForPanel(id) {
  if (id === 'game') {
    playMusic('game');
  } else {
    playMusic('menu');
  }
}


let musicArmed = false;

function armMusicOnFirstGesture() {
  if (musicArmed) return;

  musicArmed = true;

  if (uiSettings.music) {
    playMusic(
      currentMusicKey || 'menu'
    );
  }
}


document.addEventListener('click', e => {
  armMusicOnFirstGesture();

  if (
    e.target.tagName === 'BUTTON' ||
    e.target.closest('button')
  ) {
    playSfx('click');
  }
});


/* ============================================================
   NAWIGACJA
   ============================================================ */

let currentScreenName = 'home';

function showPanel(id) {
  document
    .querySelectorAll('.panel-screen')
    .forEach(el => {
      if (el.id !== 'splash') {
        el.classList.remove(
          'show',
          'active'
        );

        el.classList.add('hidden');

        el.style.display = 'none';
      }
    });

  const el = $(id);

  if (el) {
    el.classList.remove('hidden');

    el.classList.add(
      'show',
      'active'
    );

    el.style.display = 'block';
  }

  updateMusicForPanel(id);
}


function openGame() {
  closeModal(true);

  showPanel('game');

  currentScreenName = 'home';

  renderAll();
}


function showModal(html) {
  const m = $('modal');
  const mc = $('modalContent');

  if (mc) {
    mc.innerHTML = html;
  }

  if (m) {
    m.classList.remove(
      'hidden',
      'closing'
    );

    m.style.display = 'flex';
  }
}


window.closeModal = function(
  instant = false
) {
  const m = $('modal');

  if (
    !m ||
    m.classList.contains('hidden')
  ) {
    return;
  }

  if (instant) {
    m.classList.add('hidden');

    m.classList.remove('closing');

    m.style.display = 'none';

    const mc = $('modalContent');

    if (mc) {
      mc.innerHTML = '';
    }

    return;
  }

  m.classList.add('closing');

  m.addEventListener(
    'animationend',
    function handler() {
      m.classList.add('hidden');

      m.classList.remove('closing');

      m.style.display = 'none';

      const mc = $('modalContent');

      if (mc) {
        mc.innerHTML = '';
      }

      m.removeEventListener(
        'animationend',
        handler
      );
    },
    { once: true }
  );
};


function nav(name) {
  currentScreenName = name;

  document
    .querySelectorAll('#nav button')
    .forEach(b => {
      b.classList.toggle(
        'active',
        b.dataset.screen === name
      );
    });

  document
    .querySelectorAll('.screen')
    .forEach(s => {
      s.classList.remove('active');
    });

  const newEl =
    $(`screen-${name}`);

  if (newEl) {
    newEl.classList.add('active');
  }

  renderScreen(name);

  vib(10);
}


/* ============================================================
   KARIERA
   ============================================================ */

/*
 * JavaScript NIE tworzy kariery.
 *
 * Dane formularza są wysyłane do Pythona.
 *
 * football_engine tworzy:
 *
 * - zawodnika
 * - klub
 * - sezon
 * - ligę
 * - terminarz
 * - finanse
 * - transfery
 * - tabelę
 * - itd.
 */

window.startCareer = async function(event) {
  if (event) {
    event.preventDefault();
  }

  const playerData = {
    first_name:
      $('firstName')?.value.trim() || 'Mateusz',

    last_name:
      $('lastName')?.value.trim() || 'Kowalski',

    position:
      $('position')?.value || 'ST',

    age:
      Number(
        $('age')?.value || 18
      )
  };

  try {
    toast(
      'Tworzenie kariery...'
    );

    const state =
      await engineRequest(
        '/api/career/create',
        {
          method: 'POST',
          body: playerData
        }
      );

    /*
     * Python zwraca gotowy stan.
     *
     * JavaScript go NIE modyfikuje.
     */

    S = state;

    currentWorldLeague =
      S?.club?.league || null;

    openGame();

    /*
     * NAPRAWA: po stworzeniu kariery gracz nie ma jeszcze klubu.
     * Trzeba pokazać modal z ofertami klubów (openOffers), inaczej
     * ekran startowy zostaje pusty/niekompletny (brak klubu, terminarza itd.)
     * a funkcja openOffers() nigdy wcześniej nie była wywoływana.
     */
    if (!S?.club) {
      await openOffers();
    }

  } catch (error) {
    console.error(error);

    toast(
      'Nie udało się utworzyć kariery.'
    );
  }
};


/* ============================================================
   WYBÓR KLUBU
   ============================================================ */

/*
 * Kluby nie są już zapisane w JavaScript.
 *
 * Python zwraca listę ofert.
 */

async function openOffers() {
  try {
    const data =
      await engineRequest(
        '/api/career/offers'
      );

    const offers =
      Array.isArray(data)
        ? data
        : data.offers || [];

    if (!offers.length) {
      toast(
        'Brak dostępnych ofert.'
      );
      return;
    }

    const html = `
      <div class="eyebrow">
        PIERWSZY KONTRAKT
      </div>

      <h2
        style="color:#fff; margin-bottom:8px;"
      >
        Wybierz swój pierwszy klub
      </h2>

      <div
        style="
          max-height:50vh;
          overflow-y:auto;
        "
      >
        ${offers.map((offer, index) => `
          <button
            class="ghost offer-btn"
            style="
              width:100%;
              margin-bottom:8px;
              text-align:left;
              border-radius:12px;
            "
            onclick="window.chooseClub(${index})"
          >
            <b>
              ${esc(
                offer.club ||
                offer.name ||
                'Klub'
              )}
            </b>

            <br>

            <span
              style="
                font-size:0.75rem;
                color:var(--text-muted);
              "
            >
              ${esc(
                offer.league || 'Liga'
              )}

              ${
                offer.wage != null
                  ? ` • Pensja: ${Number(
                      offer.wage
                    ).toLocaleString()} PLN/tydz.`
                  : ''
              }
            </span>
          </button>
        `).join('')}
      </div>
    `;

    showModal(html);

    /*
     * Oferty są przechowywane wyłącznie
     * na potrzeby aktualnego widoku.
     *
     * Ich logika nadal znajduje się w Pythonie.
     */

    window.__careerOffers = offers;

  } catch (error) {
    console.error(error);

    toast(
      'Nie udało się pobrać ofert.'
    );
  }
}


window.chooseClub = async function(index) {
  const offers =
    window.__careerOffers || [];

  const selected =
    offers[index];

  if (!selected) {
    toast(
      'Nie znaleziono wybranej oferty.'
    );
    return;
  }

  try {
    const state =
      await engineRequest(
        '/api/career/choose-club',
        {
          method: 'POST',
          body: {
            offer_id:
              selected.clubId ??
              selected.id ??
              selected.club_id ??
              index
          }
        }
      );

    S = state;

    currentWorldLeague =
      S?.club?.league || null;

    closeModal(true);

    playSfx('trophy');

    openGame();

  } catch (error) {
    console.error(error);

    toast(
      'Nie udało się wybrać klubu.'
    );
  }
};


/* ============================================================
   ZAPIS GRY
   ============================================================ */

/*
 * Zapis kariery NIE odbywa się przez localStorage.
 *
 * Python zapisuje stan football_engine.
 */

async function saveGame() {
  try {
    await engineRequest(
      '/api/save',
      {
        method: 'POST'
      }
    );

    toast(
      'Kariera zapisana.'
    );

    vib(20);

  } catch (error) {
    console.error(error);

    toast(
      'Nie udało się zapisać kariery.'
    );
  }
}


/* ============================================================
   WCZYTANIE STANU GRY
   ============================================================ */

async function loadGameFromEngine() {
  try {
    toast(
      'Wczytywanie kariery...'
    );

    const state =
      await engineRequest(
        '/api/load'
      );

    if (!state) {
      toast(
        'Brak zapisanej kariery.'
      );
      return;
    }

    S = state;

    currentWorldLeague =
      S?.club?.league || null;

    openGame();

    /*
     * NAPRAWA: jeśli wczytana kariera nie ma jeszcze wybranego klubu
     * (np. gracz wyszedł z gry w trakcie wyboru pierwszej oferty),
     * pokaż ponownie modal z ofertami zamiast pustego ekranu.
     */
    if (!S?.club) {
      await openOffers();
    }

    toast(
      'Wczytano karierę.'
    );

  } catch (error) {
    console.error(error);

    toast(
      'Nie udało się wczytać kariery.'
    );
  }
}


/* ============================================================
   RENDEROWANIE
   ============================================================ */

/*
 * renderAll NIE zmienia stanu gry.
 *
 * Tylko wyświetla dane otrzymane z Pythona.
 */

function renderAll() {
  if (!S) return;

  if (
    S.calendar &&
    S.club
  ) {
    const sLabel =
      $('seasonLabel');

    const cLabel =
      $('clubLabel');

    if (sLabel) {
      sLabel.textContent =
        `${S.calendar.season || '—'} • ` +
        `KOLEJKA ${S.calendar.matchday || 1}/` +
        `${S.calendar.totalMatchdays || '—'}`;
    }

    if (cLabel) {
      cLabel.textContent =
        S.club.name || '—';
    }
  }

  renderScreen(
    currentScreenName
  );
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


function initials(name) {
  return String(name || '?')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0])
    .join('')
    .toUpperCase();
}


/* ============================================================
   HOME
   ============================================================ */

function renderHome() {
  const trust =
    S.relationships?.managerTrust ??
    S.managerTrust ??
    '—';

  const condition =
    S.player?.condition ??
    '—';

  /*
   * WAŻNE:
   *
   * przeciwnik musi pochodzić
   * z football_engine.
   *
   * Nie generujemy go tutaj.
   */

  const opponent =
    S.nextMatch?.opponent ||
    S.next_match?.opponent ||
    '—';

  $('screen-home').innerHTML = `
    <div class="hero-card">

      <div class="eyebrow">
        ${esc(
          S.club?.league ||
          'Liga'
        )}

        •

        ${S.club?.position ?? '—'}.
        MIEJSCE
      </div>

      <div class="matchline">

        <div>
          <div class="name">
            ${esc(
              S.player?.name ||
              'Gracz'
            )}
          </div>

          <p>
            ${S.player?.age ?? '—'}
            lat •
            ${esc(
              S.player?.position ||
              '—'
            )}
          </p>
        </div>

        <div class="ovr">
          ${S.player?.ovr ?? '—'}

          <small>
            OVR
          </small>
        </div>

      </div>

      <div class="stat-row">

        <div class="labels">
          <span class="lbl">
            Forma fizyczna
          </span>

          <span class="val">
            ${condition}%
          </span>
        </div>

        <div class="track">
          <div
            class="home"
            style="
              width:${Number(condition) || 0}%;
            "
          ></div>
        </div>

      </div>

    </div>


    <div class="hero-card match-card">

      <div class="eyebrow live">
        <span class="dot"></span>
        NASTĘPNY MECZ
      </div>

      <div class="badge-row">

        <div class="crest">
          ${initials(
            S.club?.name
          )}
        </div>

        <div class="score-block">

          <div class="score">
            VS
          </div>

          <div class="sub">
            ${esc(
              S.calendar?.season ||
              '—'
            )}
          </div>

        </div>

        <div class="crest">
          ${initials(
            opponent
          )}
        </div>

      </div>

      <div class="team-names">

        <b>
          ${esc(
            S.club?.name ||
            '—'
          )}
        </b>

        <span>
          KOLEJKA
          ${S.calendar?.matchday ?? '—'}
        </span>

        <b>
          ${esc(opponent)}
        </b>

      </div>

      <button
        class="primary"
        style="margin-top:16px;"
        onclick="${S.calendar?.seasonFinished ? 'window.seasonEndModal()' : 'window.simulateMatch()'}"
      >
        ${S.calendar?.seasonFinished ? '📋 PODSUMOWANIE SEZONU' : '▶ ROZEGRAJ MECZ'}
      </button>

      <button
        class="ghost"
        style="margin-top:8px;"
        onclick="window.trainingModal()"
      >
        🏋️ TRENING
      </button>

    </div>


    <div class="hero-card">

      <div class="eyebrow">
        STATUS KLUBOWY
      </div>

      <div class="statgrid">

        <div class="mini">
          <span>
            Konto
          </span>

          <b>
            ${
              S.finances?.balance != null
                ? Number(
                    S.finances.balance
                  ).toLocaleString()
                : '—'
            }
            PLN
          </b>
        </div>

        <div class="mini">

          <span>
            Zaufanie trenera
          </span>

          <b>
            ${trust}/100
          </b>

          <div class="meter">
            <span
              style="
                width:${Number(trust) || 0}%;
              "
            ></span>
          </div>

        </div>

      </div>

    </div>
  `;
}


/* ============================================================
   MECZ
   ============================================================ */

/*
 * TO JEST BARDZO WAŻNE:
 *
 * NIE MA TUTAJ ŻADNEJ SYMULACJI.
 *
 * JavaScript wysyła tylko polecenie:
 *
 *     /api/match/simulate
 *
 * Python:
 *
 *     football_engine
 *
 * wykonuje całą symulację.
 */

window.simulateMatch = async function() {
  try {
    playSfx('whistle');

    toast(
      'Football Engine symuluje mecz...'
    );

    const result =
      await engineRequest(
        '/api/match/simulate',
        {
          method: 'POST'
        }
      );

    /*
     * Python może zwrócić:
     *
     * {
     *   state: {...},
     *   match: {...}
     * }
     */

    if (result.state) {
      S = result.state;
    }

    if (!result.match) {
      // Sezon się zakończył - football_engine nie rozegrał meczu,
      // trzeba podjąć decyzję o dalszej karierze.
      window.seasonEndModal();
      return;
    }

    const match =
      result.match ||
      result;

    const homeGoals =
      match.homeGoals ??
      match.home_score ??
      0;

    const awayGoals =
      match.awayGoals ??
      match.away_score ??
      0;

    const clubName =
      match.home ||
      match.home_team ||
      S?.club?.name ||
      '—';

    const opponent =
      match.away ||
      match.away_team ||
      S?.nextMatch?.opponent ||
      '—';

    const playerGoals =
      match.playerGoals ??
      match.player_goals ??
      0;

    const playerAssists =
      match.playerAssists ??
      match.player_assists ??
      0;

    const logs =
      Array.isArray(match.events)
        ? [...match.events]
        : [];

    const canChoose = !!match.canChoose;

    if (
      playerGoals > 0 ||
      homeGoals > 0 ||
      awayGoals > 0
    ) {
      playSfx('goal');
    }

    vib([
      30,
      50,
      30
    ]);

    const html = `
      <div class="eyebrow">
        KONIEC MECZU
      </div>

      <h2
        style="
          color:#fff;
          text-align:center;
          margin-bottom:12px;
        "
      >
        ${esc(clubName)}
        ${homeGoals}
        :
        ${awayGoals}
        ${esc(opponent)}
      </h2>

      <div
        id="matchContribBox"
        style="
          background:rgba(255,255,255,0.05);
          padding:10px;
          border-radius:12px;
          text-align:center;
          margin-bottom:12px;
          font-size:0.85rem;
        "
      >
        Wkład w mecz:

        <b>
          ${playerGoals} Goli,
          ${playerAssists} Asyst
        </b>
      </div>

      <div
        id="matchLogBox"
        style="
          max-height:180px;
          overflow-y:auto;
          background:rgba(0,0,0,0.3);
          padding:10px;
          border-radius:10px;
          font-size:0.75rem;
          border:1px solid var(--border-soft);
        "
      >
        ${
          logs.length
            ? logs.map(event => `
                <div
                  class="log-item"
                  style="margin-bottom:4px;"
                >
                  ${esc(
                    typeof event === 'string'
                      ? event
                      : (
                          event.text ||
                          event.description ||
                          JSON.stringify(event)
                        )
                  )}
                </div>
              `).join('')
            : `
              <div
                style="color:var(--text-muted);"
              >
                Mecz przebiegł bez
                większych wydarzeń.
              </div>
            `
        }
      </div>

      <div id="matchChoiceArea" style="margin-top:12px;">
        ${
          canChoose
            ? `
              <div style="font-size:0.75rem; color:var(--text-muted); text-align:center; margin-bottom:6px;">
                Masz jeszcze jedną akcję do rozegrania — wybierz podejście:
              </div>
              <div style="display:flex; gap:8px;">
                <button class="ghost" style="flex:1;" onclick="window.matchChoiceAction('shoot')">⚽ Strzał</button>
                <button class="ghost" style="flex:1;" onclick="window.matchChoiceAction('pass')">🎯 Podanie</button>
                <button class="ghost" style="flex:1;" onclick="window.matchChoiceAction('dribble')">🌀 Drybling</button>
              </div>
            `
            : ''
        }
      </div>

      <button
        class="primary"
        style="margin-top:14px;"
        onclick="closeModal(true); renderAll();"
      >
        KONTYNUUJ
      </button>
    `;

    showModal(html);

  } catch (error) {
    console.error(error);

    toast(
      'Nie udało się rozegrać meczu.'
    );
  }
};


/*
 * Interaktywna akcja podczas meczu (jedna na mecz).
 * Wynik i wpływ na statystyki liczy football_engine.
 */
window.matchChoiceAction = async function(action) {
  const area = $('matchChoiceArea');

  if (area) {
    area.innerHTML = `<div style="text-align:center; color:var(--text-muted); font-size:0.8rem;">Rozgrywasz akcję...</div>`;
  }

  try {
    const result = await engineRequest('/api/match/choice', {
      method: 'POST',
      body: { action }
    });

    if (result.state) {
      S = result.state;
    }

    playSfx(result.success ? 'goal' : 'whistle');
    vib(result.success ? [30, 50, 30] : 20);

    const logBox = $('matchLogBox');
    if (logBox) {
      const emptyNotice = logBox.querySelector('.log-item-empty');
      if (emptyNotice) emptyNotice.remove();

      const line = document.createElement('div');
      line.className = 'log-item';
      line.style.marginBottom = '4px';
      line.textContent = result.message || '';
      logBox.appendChild(line);
      logBox.scrollTop = logBox.scrollHeight;
    }

    if (area) {
      area.innerHTML = `<div style="text-align:center; color:var(--text-muted); font-size:0.75rem;">Akcja rozegrana — zobacz wynik w dzienniku meczu.</div>`;
    }

  } catch (error) {
    console.error(error);
    toast('Nie udało się rozegrać akcji.');
    if (area) area.innerHTML = '';
  }
};


/* ============================================================
   KONIEC SEZONU
   ============================================================ */

window.seasonEndModal = function() {
  const offers = S?.pendingTransferOffers || [];

  const html = `
    <div class="eyebrow">KONIEC SEZONU ${esc(S?.calendar?.season || '')}</div>
    <h2 style="color:#fff; margin-bottom:8px;">Co dalej z karierą?</h2>

    <button class="ghost offer-btn" style="width:100%;margin-bottom:8px;text-align:left;border-radius:12px;" onclick="window.chooseSeasonDecision('stay')">
      <b>Zostań w ${esc(S?.club?.name || 'obecnym klubie')}</b><br>
      <span style="font-size:0.75rem;color:var(--text-muted);">Kontynuuj karierę w tym samym klubie</span>
    </button>

    ${offers.map(o => `
      <div class="offer-btn" style="width:100%;margin-bottom:8px;border-radius:12px;overflow:hidden;">
        <button class="ghost" style="width:100%;text-align:left;border-radius:12px;border-bottom:none;" onclick="window.chooseSeasonDecision('transfer','${esc(o.clubId || o.club)}')">
          <b>Przenieś się do ${esc(o.club || 'nowego klubu')}</b><br>
          <span style="font-size:0.75rem;color:var(--text-muted);">${esc(o.league || '')} ${o.wage != null ? ` • Pensja: ${Number(o.wage).toLocaleString()} PLN/tydz.` : ''}</span>
        </button>
        <button class="ghost" style="width:100%;text-align:left;border-top:1px solid var(--border-soft);font-size:0.75rem;padding:6px 12px;" onclick="window.openNegotiation('${esc(o.clubId || o.club)}','${esc(o.club || '')}', ${Number(o.wage) || 0})">
          💬 Negocjuj kontrakt zamiast przyjmować od razu
        </button>
      </div>
    `).join('')}

    <button class="ghost danger offer-btn" style="width:100%;margin-top:4px;text-align:left;border-radius:12px;" onclick="window.chooseSeasonDecision('retire')">
      <b>🏁 Zakończ karierę</b><br>
      <span style="font-size:0.75rem;color:var(--text-muted);">Przejdź na piłkarską emeryturę</span>
    </button>
  `;

  showModal(html);
};

window.chooseSeasonDecision = async function(decision, clubId) {
  try {
    const state = await engineRequest('/api/season/decision', {
      method: 'POST',
      body: { decision, clubId }
    });

    S = state;

    closeModal(true);

    if (decision === 'retire') {
      toast('Kariera zakończona.');
    } else {
      toast('Nowy sezon się rozpoczyna!');
    }

    vib(20);

    renderAll();

  } catch (error) {
    console.error(error);
    toast('Nie udało się przetworzyć decyzji.');
  }
};


/* ============================================================
   NEGOCJACJE KONTRAKTU
   ============================================================ */

/*
 * JavaScript NIE decyduje, czy klub zaakceptuje warunki.
 * Cała logika (cierpliwość zarządu, kontrpropozycje, budżet
 * agenta) liczona jest przez football_engine w /api/contract/negotiate.
 */

window.__nego = null;

window.openNegotiation = function(clubId, clubName, baseWage) {
  window.__nego = {
    clubId,
    clubName,
    baseWage: baseWage || 3000,
    patience: 100
  };

  window.renderNegotiationModal(
    `Klub bazowo oferuje ${Number(baseWage || 3000).toLocaleString()} PLN/tydz. Zaproponuj własne warunki — im bardziej zachłanne, tym większe ryzyko, że zarząd straci cierpliwość i wycofa ofertę.`
  );
};

window.renderNegotiationModal = function(message) {
  const n = window.__nego;
  if (!n) return;

  const suggestedWage = Math.round(n.baseWage * 1.15);

  const html = `
    <div class="eyebrow">NEGOCJACJE KONTRAKTU</div>
    <h2 style="color:#fff; margin-bottom:8px;">${esc(n.clubName || 'Nowy klub')}</h2>

    <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:12px;">
      ${esc(message || '')}
    </div>

    <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">
      Cierpliwość zarządu: <b>${n.patience}%</b>
    </div>

    <label style="font-size:0.75rem; color:var(--text-muted);">Oczekiwana pensja tygodniowa (PLN)</label>
    <input id="negoWageInput" type="number" value="${suggestedWage}" min="0" step="100"
      style="width:100%; padding:10px; border-radius:10px; margin:6px 0 12px; background:rgba(255,255,255,0.06); border:1px solid var(--border-soft); color:#fff;">

    <div style="display:flex; gap:8px; margin-bottom:8px;">
      <button class="ghost" style="flex:1;" onclick="window.negoQuick(1.05)">Ostrożnie</button>
      <button class="ghost" style="flex:1;" onclick="window.negoQuick(1.25)">Pewnie siebie</button>
      <button class="ghost" style="flex:1;" onclick="window.negoQuick(1.6)">Zachłannie</button>
    </div>

    <button class="primary" style="width:100%; margin-top:4px;" onclick="window.submitNegotiation()">
      Zaproponuj klubowi
    </button>

    <button class="ghost" style="width:100%; margin-top:8px;" onclick="window.seasonEndModal()">
      ← Wróć do listy ofert
    </button>
  `;

  showModal(html);
};

window.negoQuick = function(multiplier) {
  const n = window.__nego;
  if (!n) return;
  const input = $('negoWageInput');
  if (input) input.value = Math.round(n.baseWage * multiplier);
};

window.submitNegotiation = async function() {
  const n = window.__nego;
  if (!n) return;

  const input = $('negoWageInput');
  const wage = Number(input?.value || n.baseWage);

  try {
    const result = await engineRequest('/api/contract/negotiate', {
      method: 'POST',
      body: {
        clubId: n.clubId,
        wage,
        bonus: 0,
        patience: n.patience
      }
    });

    if (result.success) {
      S = result.state;
      window.__nego = null;
      closeModal(true);
      toast(result.message || 'Umowa podpisana!');
      playSfx('trophy');
      renderAll();
      return;
    }

    if (result.rejected) {
      window.__nego = null;
      toast(result.message || 'Klub wycofał ofertę.');
      // Oferta mogła zniknąć z listy — odśwież stan z football_engine.
      try {
        const state = await engineRequest('/api/state');
        S = state;
      } catch (e) { /* ignorujemy — i tak wracamy do listy ofert */ }
      window.seasonEndModal();
      return;
    }

    // Kontrpropozycja klubu — pokaż nową cierpliwość i sugerowaną kwotę.
    n.patience = result.patience ?? n.patience;
    window.renderNegotiationModal(
      result.message ||
      `Klub odrzucił Twoje warunki. Możesz spróbować ponownie z kwotą bliższą ${Number(result.counterWage || n.baseWage).toLocaleString()} PLN.`
    );
    if (result.counterWage != null) {
      const inp = $('negoWageInput');
      if (inp) inp.value = result.counterWage;
    }

  } catch (error) {
    console.error(error);
    toast('Nie udało się przeprowadzić negocjacji.');
  }
};


/* ============================================================
   TRENING
   ============================================================ */

/*
 * JavaScript NIE zwiększa OVR.
 *
 * Python robi:
 *
 * football_engine.training(...)
 */

window.trainingModal = async function() {
  const focuses = [
    { id: 'TECHNIQUE', label: '⚙️ Technika', desc: 'Technika, dryblig, podania' },
    { id: 'PHYSICAL', label: '💪 Fizyczny', desc: 'Szybkość, wytrzymałość, siła' },
    { id: 'SHOOTING', label: '🎯 Strzał', desc: 'Wykończenie, siła strzału' },
    { id: 'TACTICAL', label: '🧠 Taktyka', desc: 'Pozycjonowanie, wizja gry' },
    { id: 'RECOVERY', label: '🧘 Regeneracja', desc: 'Kondycja i forma, bez zmian atrybutów' }
  ];

  const html = `
    <div class="eyebrow">TRENING</div>
    <h2 style="color:#fff; margin-bottom:8px;">Wybierz fokus treningu</h2>
    <div>
      ${focuses.map(f => `
        <button class="ghost offer-btn" style="width:100%;margin-bottom:8px;text-align:left;border-radius:12px;" onclick="window.runTraining('${f.id}')">
          <b>${f.label}</b><br>
          <span style="font-size:0.75rem;color:var(--text-muted);">${f.desc}</span>
        </button>
      `).join('')}
    </div>
  `;

  showModal(html);
};

window.runTraining = async function(focus) {
  try {
    const state =
      await engineRequest(
        '/api/training',
        {
          method: 'POST',
          body: { focus }
        }
      );

    S = state;

    playSfx('perk');

    toast(
      'Trening zakończony.'
    );

    vib(18);

    closeModal(true);

    renderAll();

  } catch (error) {
    console.error(error);

    toast(
      'Nie udało się wykonać treningu.'
    );
  }
};


/* ============================================================
   KARIERA
   ============================================================ */

function renderCareer() {
  const matches =
    S.stats?.matches ?? '—';

  const goals =
    S.stats?.goals ?? '—';

  const assists =
    S.stats?.assists ?? '—';

  const minutes =
    S.stats?.minutes ?? '—';

  $('screen-career').innerHTML = `
    <div class="topbar">
      <h2>
        Twoja kariera
      </h2>
    </div>

    <div class="hero-card">

      <div class="eyebrow">
        SEZON
        ${esc(
          S.calendar?.season ||
          '—'
        )}
      </div>

      <div class="statgrid">

        <div class="mini">
          <span>
            Mecze
          </span>
          <b>
            ${matches}
          </b>
        </div>

        <div class="mini">
          <span>
            Gole
          </span>
          <b>
            ${goals}
          </b>
        </div>

        <div class="mini">
          <span>
            Asysty
          </span>
          <b>
            ${assists}
          </b>
        </div>

        <div class="mini">
          <span>
            Minuty
          </span>
          <b>
            ${minutes}'
          </b>
        </div>

      </div>

    </div>
  `;
}


/* ============================================================
   KLUB
   ============================================================ */

async function renderClub() {
  const cName =
    S.club?.name ||
    'Klub';

  const chem =
    S.teamChemistry ??
    S.team_chemistry ??
    '—';

  let squad = { starting: [], bench: [], out: [] };
  try {
    squad = await engineRequest('/api/squad');
  } catch (error) {
    console.error(error);
  }

  const renderPlayerRow = p => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06);${p.mine ? 'color:var(--accent-neon);font-weight:900;' : ''}">
      <span style="font-size:0.85rem;">#${p.number ?? '—'} <b>${esc(p.name || '—')}</b> ${p.mine ? '⭐' : ''}</span>
      <span style="font-size:0.78rem;color:var(--text-muted);">${esc(p.position || '')} • OVR ${p.ovr ?? '—'} • ${p.age ?? '—'} lat</span>
    </div>
  `;

  $('screen-club').innerHTML = `
    <div class="hero-card">

      <div class="eyebrow">
        ${esc(
          S.club?.league ||
          'Liga'
        )}
      </div>

      <div class="badge-row">

        <div class="crest">
          ${initials(cName)}
        </div>

        <div class="score-block">

          <div class="score">
            #${S.club?.position ?? '—'}
          </div>

          <div class="sub">
            Miejsce w lidze
          </div>

        </div>

      </div>

      <h2
        style="
          text-align:center;
          margin-top:6px;
        "
      >
        ${esc(cName)}
      </h2>

      <div class="stat-row">

        <div class="labels">

          <span class="lbl">
            Chemia zespołu
          </span>

          <span class="val">
            ${chem}%
          </span>

        </div>

        <div class="track">

          <div
            class="home"
            style="
              width:${Number(chem) || 0}%;
            "
          ></div>

        </div>

      </div>

    </div>

    <div class="hero-card" style="margin-top:12px;">
      <div class="eyebrow">Skład - podstawowa jedenastka</div>
      <div style="max-height:30vh;overflow-y:auto;">
        ${squad.starting.length ? squad.starting.map(renderPlayerRow).join('') : '<div style="padding:8px 0;color:var(--text-muted);font-size:0.8rem;">Brak danych o składzie.</div>'}
      </div>
    </div>

    <div class="hero-card" style="margin-top:12px;">
      <div class="eyebrow">Ławka rezerwowych</div>
      <div style="max-height:25vh;overflow-y:auto;">
        ${squad.bench.length ? squad.bench.map(renderPlayerRow).join('') : '<div style="padding:8px 0;color:var(--text-muted);font-size:0.8rem;">Ławka pusta.</div>'}
      </div>
    </div>
  `;
}


/* ============================================================
   ŚWIAT / TABELE
   ============================================================ */

/*
 * Nie ma tutaj:
 *
 * LEAGUES_DATA
 * generateAllLeaguesState()
 * Math.random()
 * tworzenia tabel
 *
 * Tabela pochodzi z football_engine.
 */

async function renderWorld() {
  let leagues = {};
  try {
    const world = await engineRequest('/api/world');
    (world?.leagues || []).forEach(lg => {
      leagues[lg.name] = (lg.table || []).map(row => ({
        pos: row.pos,
        name: row.club,
        pts: row.pts,
        played: row.played
      }));
    });
  } catch (error) {
    console.error(error);
  }

  const leagueNames =
    Object.keys(leagues);

  if (!currentWorldLeague) {
    currentWorldLeague =
      S?.club?.league ||
      leagueNames[0] ||
      null;
  }

  let tabsHtml = `
    <div
      style="
        display:flex;
        gap:6px;
        overflow-x:auto;
        padding-bottom:10px;
        margin-bottom:10px;
      "
    >
  `;

  leagueNames.forEach(
    leagueName => {

      const active =
        leagueName ===
        currentWorldLeague;

      tabsHtml += `
        <button
          class="ghost"
          style="
            padding:6px 12px;
            font-size:0.75rem;
            border-radius:20px;
            flex-shrink:0;
            width:auto;
            ${
              active
                ? 'background:var(--grad-main);color:#fff;border:none;'
                : ''
            }
          "
          onclick="window.switchWorldLeague('${esc(
            leagueName
          )}')"
        >
          ${esc(leagueName)}
        </button>
      `;
    }
  );

  tabsHtml += `
    </div>
  `;

  const standings =
    leagues[
      currentWorldLeague
    ] || [];

  $('screen-world').innerHTML = `
    <div class="topbar">
      <h2>
        Tabela ligowa
      </h2>
    </div>

    ${tabsHtml}

    <div class="hero-card">

      <div class="eyebrow">
        ${esc(
          currentWorldLeague ||
          'Liga'
        )}
      </div>

      <div
        style="
          max-height:55vh;
          overflow-y:auto;
          padding-right:4px;
        "
      >

        ${
          standings.map(
            team => {

              const isMyClub =
                team.name ===
                S?.club?.name;

              return `
                <div
                  style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding:10px 0;
                    border-bottom:1px solid rgba(255,255,255,0.06);
                    ${
                      isMyClub
                        ? 'color:var(--accent-neon);font-weight:900;'
                        : ''
                    }
                  "
                >

                  <span
                    style="
                      font-size:0.85rem;
                    "
                  >
                    ${team.pos ?? '—'}.

                    <b>
                      ${esc(
                        team.name ||
                        '—'
                      )}
                    </b>

                    ${
                      isMyClub
                        ? '⭐'
                        : ''
                    }

                  </span>

                  <span
                    style="
                      font-size:0.8rem;
                      font-weight:700;
                    "
                  >
                    ${team.pts ?? '—'}
                    pkt

                    <small
                      style="
                        color:var(--text-muted);
                        font-weight:400;
                      "
                    >
                      (${team.played ?? '—'} M)
                    </small>

                  </span>

                </div>
              `;
            }
          ).join('')
        }

      </div>

    </div>
  `;
}


window.switchWorldLeague =
  function(leagueName) {

    currentWorldLeague =
      leagueName;

    renderWorld();
  };


/* ============================================================
   PUCHARY
   ============================================================ */

function renderCups() {
  const cup =
    S?.cup ||
    S?.cups ||
    {};

  $('screen-cups').innerHTML = `
    <div class="topbar">
      <h2>
        Puchar Polski
      </h2>
    </div>

    <div class="hero-card">

      <div class="eyebrow">
        ROZGRYWKI PUCHAROWE
      </div>

      <p>
        Status:

        <b>
          ${esc(
            cup.round ||
            cup.stage ||
            '—'
          )}
        </b>
      </p>

    </div>
  `;
}


/* ============================================================
   REPREZENTACJA
   ============================================================ */

function renderNational() {
  const national =
    S?.national ||
    {};

  $('screen-national').innerHTML = `
    <div class="topbar">
      <h2>
        Reprezentacja Polski
      </h2>
    </div>

    <div class="hero-card">

      <p class="muted">
        ${
          national.message ||
          'Informacje zostaną przekazane przez football_engine.'
        }
      </p>

    </div>
  `;
}


/* ============================================================
   PROFIL
   ============================================================ */

function renderProfile() {
  const player =
    S?.player ||
    {};

  /*
   * NIE LICZYMY wartości:
   *
   * OVR * 12000
   *
   * Python ma podać gotową wartość.
   */

  const value =
    player.value ??
    player.market_value ??
    '—';

  const finances = S?.finances || {};
  const perks = S?.perks || [];
  const skillPoints = S?.skillPoints ?? 0;
  const sponsors = S?.sponsors || [];
  const activeSponsor = S?.activeSponsor;
  const lifestyle = S?.lifestyle || { prestige: 0, owned: [] };
  const shop = S?.lifestyleShop || [];

  const perksHtml = perks.map(p => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
      <div>
        <b style="font-size:0.85rem;">${esc(p.name)}</b>
        <div style="font-size:0.72rem;color:var(--text-muted);">${esc(p.desc || '')}</div>
      </div>
      ${p.unlocked
        ? '<span style="color:var(--accent-neon);font-size:0.75rem;font-weight:700;">✓ ODBLOKOWANE</span>'
        : `<button class="ghost" style="width:auto;padding:6px 10px;font-size:0.72rem;" onclick="window.unlockPerk('${esc(p.id)}')">${p.cost} PKT</button>`
      }
    </div>
  `).join('') || '<div style="color:var(--text-muted);font-size:0.8rem;">Brak dostępnych perków.</div>';

  const sponsorsHtml = sponsors.map(s => {
    const owned = activeSponsor === s.id;
    const eligible = (lifestyle.prestige ?? 0) >= s.req_prestige;
    return `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
        <div>
          <b style="font-size:0.85rem;">${esc(s.name)}</b>
          <div style="font-size:0.72rem;color:var(--text-muted);">${esc(s.desc)} • +${Number(s.pay).toLocaleString()} PLN/tydz.</div>
        </div>
        ${owned
          ? '<span style="color:var(--accent-neon);font-size:0.75rem;font-weight:700;">AKTYWNY</span>'
          : `<button class="ghost" style="width:auto;padding:6px 10px;font-size:0.72rem;" ${eligible ? '' : 'disabled'} onclick="window.signSponsor('${esc(s.id)}')">${eligible ? 'PODPISZ' : 'ZA NISKI PRESTIŻ'}</button>`
        }
      </div>
    `;
  }).join('') || '<div style="color:var(--text-muted);font-size:0.8rem;">Brak dostępnych sponsorów.</div>';

  const shopHtml = shop.map(item => {
    const owned = (lifestyle.owned || []).includes(item.id);
    const afford = (finances.balance ?? 0) >= item.cost;
    return `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
        <div>
          <b style="font-size:0.85rem;">${esc(item.name)}</b>
          <div style="font-size:0.72rem;color:var(--text-muted);">${Number(item.cost).toLocaleString()} PLN • +${item.prestige} prestiżu</div>
        </div>
        ${owned
          ? '<span style="color:var(--accent-neon);font-size:0.75rem;font-weight:700;">POSIADANE</span>'
          : `<button class="ghost" style="width:auto;padding:6px 10px;font-size:0.72rem;" ${afford ? '' : 'disabled'} onclick="window.buyLifestyle('${esc(item.id)}')">${afford ? 'KUP' : 'BRAK ŚRODKÓW'}</button>`
        }
      </div>
    `;
  }).join('') || '<div style="color:var(--text-muted);font-size:0.8rem;">Sklep pusty.</div>';

  $('screen-profile').innerHTML = `
    <div class="hero-card">

      <div class="badge-row">

        <div class="crest">
          ${initials(
            player.name
          )}
        </div>

      </div>

      <h2
        style="
          text-align:center;
        "
      >
        ${esc(
          player.name ||
          'Gracz'
        )}
      </h2>

      <p
        style="
          text-align:center;
          color:var(--text-muted);
          margin-bottom:12px;
        "
      >
        Wartość rynkowa:

        ${
          typeof value === 'number'
            ? value.toLocaleString()
            : esc(value)
        }

        PLN
      </p>

    </div>

    <div class="hero-card">
      <div class="eyebrow">Finanse i sztab</div>
      <div class="statgrid" style="margin-bottom:10px;">
        <div class="mini"><span>Konto</span><b>${Number(finances.balance ?? 0).toLocaleString()} PLN</b></div>
        <div class="mini"><span>Pensja tyg.</span><b>${Number(finances.salary ?? 0).toLocaleString()} PLN</b></div>
      </div>
      <button class="ghost" ${finances.hasTrainer ? 'disabled' : ''} onclick="window.buyTrainer()">
        🏋️ ${finances.hasTrainer ? 'TRENER PERSONALNY ZATRUDNIONY' : 'ZATRUDNIJ TRENERA (10 000 PLN)'}
      </button>
      <button class="ghost" style="margin-top:8px;" onclick="window.upgradeAgent()">
        🕴️ ULEPSZ AGENTA (poziom ${finances.agentTier ?? 1})
      </button>
      ${player.injured ? `<button class="ghost" style="margin-top:8px;" onclick="window.rehabPlayer()">🏥 REHABILITACJA (15 000 PLN)</button>` : ''}
    </div>

    <div class="hero-card">
      <div class="eyebrow">Perki (${skillPoints} pkt. umiejętności)</div>
      ${perksHtml}
    </div>

    <div class="hero-card">
      <div class="eyebrow">Sponsorzy (prestiż: ${lifestyle.prestige ?? 0})</div>
      ${sponsorsHtml}
    </div>

    <div class="hero-card">
      <div class="eyebrow">Sklep lifestyle</div>
      <div style="max-height:35vh;overflow-y:auto;">
        ${shopHtml}
      </div>
    </div>

    <div class="hero-card">

      <button
        class="primary"
        onclick="saveGame()"
      >
        💾 ZAPISZ GRĘ
      </button>

      <button
        class="ghost"
        style="margin-top:8px;"
        onclick="window.openSettingsFromGame()"
      >
        ⚙️ USTAWIENIA
      </button>

      <button
        class="ghost"
        style="margin-top:8px;"
        onclick="window.backToMainMenu()"
      >
        🏠 MENU GŁÓWNE
      </button>

    </div>
  `;
}

window.unlockPerk = async function(perkId) {
  try {
    const state = await engineRequest('/api/perk/unlock', { method: 'POST', body: { perkId } });
    S = state;
    playSfx('perk');
    vib(15);
    renderAll();
  } catch (error) {
    console.error(error);
    toast('Nie udało się odblokować perka.');
  }
};

window.buyTrainer = async function() {
  try {
    const state = await engineRequest('/api/finance/buy-trainer', { method: 'POST' });
    S = state;
    toast('Trener zatrudniony.');
    vib(15);
    renderAll();
  } catch (error) {
    console.error(error);
    toast('Nie udało się zatrudnić trenera.');
  }
};

window.upgradeAgent = async function() {
  try {
    const state = await engineRequest('/api/finance/upgrade-agent', { method: 'POST' });
    S = state;
    toast('Agent ulepszony.');
    vib(15);
    renderAll();
  } catch (error) {
    console.error(error);
    toast('Nie udało się ulepszyć agenta.');
  }
};

window.signSponsor = async function(sponsorId) {
  try {
    const state = await engineRequest('/api/sponsor/sign', { method: 'POST', body: { sponsorId } });
    S = state;
    toast('Umowa sponsorska podpisana.');
    vib(15);
    renderAll();
  } catch (error) {
    console.error(error);
    toast('Nie udało się podpisać umowy.');
  }
};

window.buyLifestyle = async function(itemId) {
  try {
    const state = await engineRequest('/api/lifestyle/buy', { method: 'POST', body: { itemId } });
    S = state;
    toast('Zakup zrealizowany.');
    vib(15);
    renderAll();
  } catch (error) {
    console.error(error);
    toast('Nie udało się dokonać zakupu.');
  }
};

window.rehabPlayer = async function() {
  try {
    const state = await engineRequest('/api/player/rehab', { method: 'POST' });
    S = state;
    toast('Zabieg rehabilitacyjny wykonany.');
    vib(15);
    renderAll();
  } catch (error) {
    console.error(error);
    toast('Nie udało się wykonać zabiegu.');
  }
};


/* ============================================================
   POZOSTAŁE UI
   ============================================================ */

function updateCustomUI(state) {
  /*
   * Celowo puste.
   *
   * Tutaj można później dodawać wyłącznie
   * elementy prezentacyjne.
   *
   * NIE umieszczamy tutaj mechaniki gry.
   */
}


let settingsReturnTo =
  'mainmenu';

const DISCORD_INVITE_URL = '';


window.openSettingsFromGame =
  function() {

    settingsReturnTo =
      'game';

    showPanel('settings');
  };


window.backToMainMenu =
  function() {

    showPanel('mainmenu');
  };


/* ============================================================
   START APLIKACJI
   ============================================================ */

document.addEventListener(
  'DOMContentLoaded',
  () => {

    const splash =
      $('splash');

    const dismissSplash =
      () => {

        if (
          splash &&
          splash.style.display !== 'none'
        ) {

          splash.classList.add(
            'fade-out'
          );

          setTimeout(
            () => {

              splash.style.display =
                'none';

              splash.classList.remove(
                'show'
              );

              showPanel(
                'mainmenu'
              );

            },
            400
          );

        } else {

          showPanel(
            'mainmenu'
          );

        }
      };


    setTimeout(
      dismissSplash,
      1800
    );


    /*
     * Nawigacja UI.
     */

    document
      .querySelectorAll(
        '#nav button'
      )
      .forEach(button => {

        button.onclick =
          () =>
            nav(
              button.dataset.screen
            );

      });


    /*
     * NOWA GRA
     */

    $('menuNewGame')
      ?.addEventListener(
        'click',
        () =>
          showPanel(
            'onboarding'
          )
      );


    /*
     * WCZYTANIE GRY
     *
     * NIE localStorage.
     *
     * Python ładuje save.
     */

    $('menuLoadGame')
      ?.addEventListener(
        'click',
        () =>
          loadGameFromEngine()
      );


    /*
     * USTAWIENIA
     */

    $('menuSettings')
      ?.addEventListener(
        'click',
        () => {

          settingsReturnTo =
            'mainmenu';

          showPanel(
            'settings'
          );

        }
      );


    /*
     * WYJŚCIE
     */

    $('menuQuit')
      ?.addEventListener(
        'click',
        () => {

          try {

            if (
              window.Capacitor
                ?.Plugins
                ?.App
                ?.exitApp
            ) {

              window.Capacitor
                .Plugins
                .App
                .exitApp();

              return;
            }

          } catch (e) {}

          toast(
            'Zamknij aplikację przyciskiem systemowym telefonu'
          );

        }
      );


    /*
     * DISCORD
     */

    $('menuDiscord')
      ?.addEventListener(
        'click',
        () => {

          if (
            DISCORD_INVITE_URL
          ) {

            window.open(
              DISCORD_INVITE_URL,
              '_blank'
            );

          } else {

            toast(
              'Serwer Discord wkrótce!'
            );

          }

        }
      );


    /*
     * ONBOARDING
     */

    $('onboardingBack')
      ?.addEventListener(
        'click',
        () =>
          showPanel(
            'mainmenu'
          )
      );


    /*
     * SETTINGS BACK
     */

    $('settingsBack')
      ?.addEventListener(
        'click',
        () =>
          showPanel(
            settingsReturnTo
          )
      );


    /*
     * ANIMACJE
     */

    const $anim =
      $('toggleAnimations');

    if ($anim) {

      $anim.checked =
        uiSettings.animations;

      $anim.addEventListener(
        'change',
        () => {

          uiSettings.animations =
            $anim.checked;

          applySettings();

          saveSettings();

        }
      );
    }


    /*
     * TRYB JASNY
     */

    const $light =
      $('toggleLightMode');

    if ($light) {

      $light.checked =
        uiSettings.theme ===
        'light';

      $light.addEventListener(
        'change',
        () => {

          uiSettings.theme =
            $light.checked
              ? 'light'
              : 'dark';

          applySettings();

          saveSettings();

        }
      );
    }


    /*
     * DŹWIĘK
     */

    const $sound =
      $('toggleSound');

    if ($sound) {

      $sound.checked =
        uiSettings.sound;

      $sound.addEventListener(
        'change',
        () => {

          uiSettings.sound =
            $sound.checked;

          saveSettings();

        }
      );
    }


    /*
     * MUZYKA
     */

    const $music =
      $('toggleMusic');

    if ($music) {

      $music.checked =
        uiSettings.music;

      $music.addEventListener(
        'change',
        () => {

          uiSettings.music =
            $music.checked;

          saveSettings();

          if (
            uiSettings.music
          ) {

            playMusic(
              currentMusicKey ||
              'menu'
            );

          } else {

            stopMusic();

          }

        }
      );
    }


    /*
     * GŁOŚNOŚĆ
     */

    const $vol =
      $('volumeSlider');

    if ($vol) {

      $vol.value =
        Math.round(
          (uiSettings.volume ?? 0.7) *
          100
        );

      $vol.addEventListener(
        'input',
        () => {

          uiSettings.volume =
            Number(
              $vol.value
            ) / 100;

          saveSettings();

          applyMusicVolume();

        }
      );
    }


    /*
     * USUWANIE ZAPISU
     *
     * Zamiast kasowania localStorage
     * wysyłamy polecenie do Pythona.
     */

    $('clearSaves')
      ?.addEventListener(
        'click',
        async () => {

          try {

            await engineRequest(
              '/api/save/delete',
              {
                method: 'POST'
              }
            );

            toast(
              'Zapis kariery usunięty.'
            );

          } catch (error) {

            console.error(error);

            toast(
              'Nie udało się usunąć zapisu.'
            );

          }

        }
      );

  }
);