#!/usr/bin/env bash
# LAVA / Irene Voice Assistant — универсальный инсталлятор (Linux / macOS / WSL / Git Bash)
# Запускать из корня репозитория:  ./install.sh  или  bash install.sh
# Повторный запуск безопасен (идемпотентен).

set -e

# ---------- Цвета и логи ----------
if [ -t 1 ]; then
  GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; CYAN="\033[36m"; BOLD="\033[1m"; RESET="\033[0m"
else
  GREEN=""; YELLOW=""; RED=""; CYAN=""; BOLD=""; RESET=""
fi
info()  { echo -e "${CYAN}▸${RESET} $*"; }
ok()    { echo -e "${GREEN}✔${RESET} $*"; }
warn()  { echo -e "${YELLOW}⚠${RESET} $*"; }
fail()  { echo -e "${RED}✘${RESET} $*" >&2; }
die()   { fail "$*"; exit 1; }

# ---------- Параметры по умолчанию ----------
VENV_DIR="venv"
DO_FRONTEND=1
DO_PYTHON=1
DO_VOSK_CHECK=1
LITE=0
DEV=0
REINSTALL=0
YES=0
SKIP_SYSTEM_CHECK=0

usage() {
  cat <<'EOF'
Использование: ./install.sh [опции]

Опции:
  --venv DIR        Папка виртуального окружения (по умолчанию: venv)
  --no-frontend     Не собирать frontend (пропустить npm ci && build)
  --no-python       Не ставить Python-зависимости
  --lite            Лёгкая установка: пропускает torch (~800МБ) — без Silero TTS
  --dev             Поставить также requirements-ci.txt (mypy/pep8/coveralls)
  --reinstall       Пересоздать venv и переустановить всё
  --yes, -y         Не спрашивать подтверждений
  --skip-system     Не проверять системные зависимости (portaudio и т.д.)
  --help, -h        Показать справку

Примеры:
  ./install.sh                      # полная установка
  ./install.sh --lite               # без torch (быстро, мало места)
  ./install.sh --reinstall --dev    # чистая переустановка + dev-зависимости
  ./install.sh --no-frontend        # только Python

После установки запуск:
  source venv/bin/activate          # Linux/macOS/WSL
  # или source venv/Scripts/activate # Git Bash на Windows
  python -m irene                   # веб-интерфейс на https://localhost:8086
  python -m irene -T console        # консольный режим
EOF
}

# ---------- Парсинг аргументов ----------
while [ $# -gt 0 ]; do
  case "$1" in
    --venv) VENV_DIR="$2"; shift 2;;
    --no-frontend) DO_FRONTEND=0; shift;;
    --no-python) DO_PYTHON=0; shift;;
    --lite) LITE=1; shift;;
    --dev) DEV=1; shift;;
    --reinstall) REINSTALL=1; shift;;
    --yes|-y) YES=1; shift;;
    --skip-system) SKIP_SYSTEM_CHECK=1; shift;;
    --help|-h) usage; exit 0;;
    *) die "Неизвестная опция: $1 (см. --help)";;
  esac
done

# ---------- Определяем корень проекта ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
[ -f "requirements.txt" ] || die "requirements.txt не найден. Запускайте из корня репозитория."
[ -f "frontend/package.json" ] || warn "frontend/package.json не найден — сборка фронта будет пропущена."

echo -e "${BOLD}=== LAVA Installer ===${RESET}"
echo "Проект: $SCRIPT_DIR"
echo "Venv:   $VENV_DIR  | Frontend: $DO_FRONTEND  | Lite: $LITE  | Dev: $DEV  | Reinstall: $REINSTALL"
echo ""

# ---------- Поиск Python ----------
find_python() {
  for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
      if "$cmd" -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null; then
        echo "$cmd"; return 0
      else
        ver=$("$cmd" --version 2>&1 || true)
        warn "Найден $cmd ($ver) но требуется Python >=3.9 — пропускаю."
      fi
    fi
  done
  return 1
}

PYTHON_BIN="$(find_python)" || die "Python >=3.9 не найден. Установите с https://python.org (или apt/brew)."

PY_VER=$("$PYTHON_BIN" --version 2>&1)
ok "Python: $PY_VER ($PYTHON_BIN)"

# Проверка версии pip/venv
if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
  warn "pip не найден для $PYTHON_BIN — пробую ensurepip..."
  "$PYTHON_BIN" -m ensurepip --upgrade || die "Не удалось установить pip."
fi
if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
  warn "Модуль venv недоступен."
  if [ "$(uname -s)" = "Linux" ]; then
    warn "На Debian/Ubuntu: sudo apt install python3-venv"
  fi
  die "venv требуется для изоляции."
fi

# ---------- Проверка Node ----------
NODE_BIN=""; NPM_BIN=""; NODE_VER=""; NODE_MAJOR=0
if command -v node >/dev/null 2>&1; then
  NODE_BIN="node"
  NODE_VER=$(node --version 2>&1 | tr -d 'v' || true)
  NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
  if [ "$NODE_MAJOR" -ge 16 ] 2>/dev/null; then
    ok "Node: v$NODE_VER ($NODE_BIN)"
  else
    warn "Node v$NODE_VER слишком стар (нужен >=16.17). Фронт может не собраться."
  fi
  if command -v npm >/dev/null 2>&1; then
    NPM_BIN="npm"
    NPM_VER=$(npm --version 2>&1 || true)
    ok "npm: v$NPM_VER"
  else
    warn "npm не найден — сборка фронта будет пропущена."
    DO_FRONTEND=0
  fi
else
  if [ "$DO_FRONTEND" -eq 1 ]; then
    warn "Node.js не найден — сборка фронта будет пропущена."
    warn "Установите Node 16.17+ с https://nodejs.org или: apt/brew install nodejs"
    DO_FRONTEND=0
  fi
fi

# ---------- Системные зависимости (Linux) ----------
if [ "$SKIP_SYSTEM_CHECK" -eq 0 ] && [ "$(uname -s)" = "Linux" ]; then
  MISSING_SYS=""
  # portaudio (sounddevice)
  if ! ldconfig -p 2>/dev/null | grep -q libportaudio; then
    if ! dpkg -l 2>/dev/null | grep -q portaudio; then
      MISSING_SYS="$MISSING_SYS libportaudio2"
    fi
  fi
  # libsndfile
  if ! ldconfig -p 2>/dev/null | grep -q libsndfile; then
    MISSING_SYS="$MISSING_SYS libsndfile1"
  fi
  if [ -n "$MISSING_SYS" ]; then
    warn "Системные библиотеки не найдены:$MISSING_SYS"
    echo "  Рекомендуется: sudo apt update && sudo apt install -y libportaudio2 libsndfile1-dev python3-venv ffmpeg"
    if [ "$YES" -eq 0 ]; then
      echo -n "Продолжить без них? (звук может не работать) [Y/n]: "
      read -r ans; case "$ans" in [nN]*) die "Установите зависимости и запустите снова.";; esac
    fi
  fi
fi

# ---------- Подтверждение ----------
if [ "$YES" -eq 0 ] && [ "$REINSTALL" -eq 1 ]; then
  echo -n "Пересоздать $VENV_DIR и переустановить всё? [y/N]: "
  read -r ans; case "$ans" in [yY]*) ;; *) die "Отменено.";; esac
fi

# ---------- Venv ----------
# В Git Bash на Windows путь к activate другой, но venv создаётся той же командой
if [ "$REINSTALL" -eq 1 ] && [ -d "$VENV_DIR" ]; then
  info "Удаляю $VENV_DIR..."
  rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
  info "Создаю venv: $VENV_DIR ($PYTHON_BIN -m venv)..."
  "$PYTHON_BIN" -m venv "$VENV_DIR" || die "Не удалось создать venv."
  ok "venv создан."
else
  ok "venv уже существует: $VENV_DIR"
fi

# Активация venv (совместимо с bash/zsh и Git Bash)
if [ -f "$VENV_DIR/bin/activate" ]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/Scripts/activate"
else
  die "Не найден activate скрипт в $VENV_DIR"
fi
# После активации python должен указывать на venv
VENV_PYTHON="$(command -v python 2>/dev/null || command -v python3 2>/dev/null || echo "$VENV_DIR/bin/python")"
ok "Venv python: $($VENV_PYTHON --version 2>&1) ($VENV_PYTHON)"

# Обновление pip
info "Обновляю pip/setuptools/wheel..."
python -m pip install --upgrade pip setuptools wheel || warn "Не удалось обновить pip — продолжаю."

# ---------- Python зависимости ----------
if [ "$DO_PYTHON" -eq 1 ]; then
  info "Ставлю Python-зависимости..."

  # Лёгкий режим: фильтруем torch
  if [ "$LITE" -eq 1 ]; then
    warn "Лёгкий режим (--lite): пропускаю torch (Silero TTS не будет работать)."
    # Создаём временный requirements без torch
    TMP_REQ=$(mktemp)
    grep -vi "^\s*torch" requirements.txt > "$TMP_REQ" || cp requirements.txt "$TMP_REQ"
    # также убираем версии связанные с torch в docker-зависимостях (если есть)
    pip install -r "$TMP_REQ" || { rm -f "$TMP_REQ"; die "pip install упал."; }
    rm -f "$TMP_REQ"
    ok "Python-зависимости (lite) установлены."
  else
    # Полная установка — torch занимает много места/времени, показываем прогресс
    info "Это может занять 3–10 минут (torch ~200МБ + компиляция)..."
    pip install -r requirements.txt || die "pip install -r requirements.txt упал. Попробуйте: pip install --verbose -r requirements.txt для деталей."
    ok "Python-зависимости установлены."
  fi

  if [ "$DEV" -eq 1 ]; then
    if [ -f "requirements-ci.txt" ]; then
      info "Ставлю dev-зависимости (requirements-ci.txt)..."
      pip install -r requirements-ci.txt || warn "Не удалось поставить dev-зависимости."
    fi
  fi

  # Проверка ключевых импортов
  info "Проверяю импорты..."
  python -c "import fastapi, uvicorn, yaml, vosk; print('  fastapi/uvicorn/yaml/vosk — OK')" 2>&1 || warn "Некоторые пакеты не импортируются — проверьте логи выше."
  if [ "$LITE" -eq 0 ]; then
    python -c "import torch; print('  torch', torch.__version__)" 2>&1 || warn "torch не импортируется (Silero не будет работать)."
  fi
else
  warn "Пропускаю Python-зависимости (--no-python)."
fi

# ---------- Frontend ----------
if [ "$DO_FRONTEND" -eq 1 ]; then
  if [ -z "$NPM_BIN" ]; then
    warn "npm не найден — пропускаю фронт."
  elif [ ! -f "frontend/package.json" ]; then
    warn "frontend/package.json не найден — пропускаю."
  else
    info "Ставлю frontend зависимости (npm ci)..."
    # npm ci требует package-lock.json
    if [ ! -f "frontend/package-lock.json" ]; then
      warn "package-lock.json не найден — использую npm install."
      (cd frontend && npm install) || die "npm install упал."
    else
      (cd frontend && npm ci) || die "npm ci упал. Попробуйте: cd frontend && npm install"
    fi
    ok "npm зависимости установлены."

    info "Собираю frontend (npm run build)..."
    (cd frontend && npm run build) || die "npm run build упал. Проверьте: node --version (нужен >=16.17) и логи выше."
    ok "Frontend собран."

    # Проверка результата — два возможных расположения (см. irene_plugin_web_face_frontend/plugin_web_face_frontend.py)
    if [ -f "frontend/dist/index.html" ]; then
      ok "artifacts: frontend/dist/index.html"
    else
      warn "frontend/dist/index.html не найден после сборки!"
    fi
    # Также копируем в frontend-dist для прямой совместимости с Docker-ожиданием (опционально)
    if [ -d "frontend/dist" ] && [ ! -d "irene_plugin_web_face_frontend/frontend-dist" ]; then
      info "Копирую dist → irene_plugin_web_face_frontend/frontend-dist (для совместимости)..."
      mkdir -p irene_plugin_web_face_frontend/frontend-dist
      cp -r frontend/dist/* irene_plugin_web_face_frontend/frontend-dist/ 2>/dev/null || true
    fi
  fi
else
  warn "Сборка фронта пропущена (--no-frontend или нет Node)."
  if [ -f "frontend/dist/index.html" ]; then
    ok "Найден уже собранный frontend/dist — можно работать."
  else
    warn "Собранного фронта нет. Web-интерфейс не заработает до сборки."
    warn "Соберите вручную: cd frontend && npm ci && npm run build"
  fi
fi

# ---------- Ресурсы: модели ----------
if [ "$DO_VOSK_CHECK" -eq 1 ]; then
  info "Проверяю ресурсы..."
  if [ -f "resources/silero-models/c9e311e020562111e5414ff93d47e0a1-v3_1_ru.pt" ]; then
    ok "Silero модель: resources/silero-models/c9e311e020562111e5414ff93d47e0a1-v3_1_ru.pt ($(du -h resources/silero-models/c9e311e020562111e5414ff93d47e0a1-v3_1_ru.pt | cut -f1))"
  else
    warn "Silero модель не найдена (скачается при первом запуске если есть инет, или положите .pt в resources/silero-models/)."
  fi
  if ls resources/vosk-models/*.zip >/dev/null 2>&1; then
    ok "Vosk модель: $(ls -lh resources/vosk-models/*.zip | awk '{print $9, $5}')"
  else
    warn "Vosk модель не найдена в resources/vosk-models/"
    warn "Скачайте вручную: https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
    warn "Или дождитесь автозагрузки при первом запуске (требует интернет)."
  fi
  if [ -d "docker-config" ]; then ok "docker-config/ на месте."; fi
fi

# ---------- Финальная проверка ----------
info "Финальная проверка..."
if python -c "import irene; print('  import irene — OK')" 2>&1; then ok "Python-пакет irene импортируется."; else warn "import irene не удался."; fi
if [ -f "frontend/dist/index.html" ] || [ -f "irene_plugin_web_face_frontend/frontend-dist/index.html" ]; then ok "Frontend dist найден."; else warn "Frontend dist не найден."; fi

echo ""
echo -e "${GREEN}${BOLD}=== Установка завершена ===${RESET}"
echo ""
echo "Запуск (из корня репозитория):"
if [[ "$VENV_DIR" == venv ]]; then
  if [ -f "venv/bin/activate" ]; then
    echo "  source venv/bin/activate        # активировать venv (Linux/macOS/WSL)"
  fi
  if [ -f "venv/Scripts/activate" ]; then
    echo "  source venv/Scripts/activate    # активировать venv (Git Bash Windows)"
  fi
else
  echo "  source $VENV_DIR/bin/activate"
fi
echo "  python -m irene                 # веб на https://localhost:8086 (самоподписанный cert)"
echo "  python -m irene --help          # все опции"
echo "  python -m irene -T console      # консольный режим"
echo ""
echo "Frontend dev (горячая перезагрузка, прокси /api → 8086):"
echo "  cd frontend && npm run dev      # http://localhost:5173"
echo ""
echo "Полезно:"
echo "  IRENE_HOME=\"\$PWD/irene-home\" python -m irene   # кастомная папка данных"
echo "  ./install.sh --lite             # без torch (экономит ~800МБ)"
echo "  ./install.sh --reinstall        # чистая переустановка"
echo ""
warn "Если звук не работает на Linux: sudo apt install libportaudio2 libsndfile1-dev && ./install.sh --reinstall"
