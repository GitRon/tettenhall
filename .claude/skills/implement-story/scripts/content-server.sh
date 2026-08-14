#!/usr/bin/env bash
# Puts a runnable copy of the game in front of a browser for the content review: throwaway database,
# reference data loaded, a known login, and a server that answers before the script returns.
#
# Usage: bash .claude/skills/implement-story/scripts/content-server.sh <verb> <run-dir> [port]
#   start    reuse a live server, or set the database up and start one
#   fresh    delete the smoke database first, then start - a clean savegame, a clean month
#   restart  stop and start again, keeping the database. Do this after every code change: the
#            server runs with --noreload, so otherwise the browser keeps testing the old code
#   stop     kill the server, keep the database and the log
#   status   is it up, on which port, with which credentials
#
# Exit code: 0 when the verb succeeded, 1 otherwise.

set -uo pipefail

VERB="${1:?usage: content-server.sh <start|fresh|restart|stop|status> <run-dir> [port]}"
RUN_DIR="${2:?usage: content-server.sh <start|fresh|restart|stop|status> <run-dir> [port]}"
PORT_ARG="${3:-}"

REPO_ROOT="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO_ROOT" || exit 1

case "$RUN_DIR" in
  /*) ;;
  ?:/*) ;;
  *) RUN_DIR="$REPO_ROOT/$RUN_DIR" ;;
esac

CONTENT_DIR="$RUN_DIR/content"
DB_FILE="$CONTENT_DIR/smoke.sqlite3"
LOG_FILE="$CONTENT_DIR/server.log"
SETUP_LOG="$CONTENT_DIR/setup.log"
PID_FILE="$CONTENT_DIR/.pid"
PORT_FILE="$CONTENT_DIR/.port"

SMOKE_USER="smoke"
# The login form authenticates by email, not by username, and looks the user up with a plain get(),
# so this address is what goes into the form.
SMOKE_EMAIL="smoke@tettenhall.test"
# Fixed so the reviewer never has to guess: three failed logins lock this account out for 15
# minutes, and a guessed password is how a content review loses its own wall-clock.
SMOKE_PASSWORD="tettenhall-smoke-run"

DEFAULT_PORT=8765

mkdir -p "$CONTENT_DIR"

# uv creates the virtualenv inside the project. Calling its interpreter directly rather than going
# through "uv run" matters for the server: it makes the process we start the process we can kill,
# instead of a wrapper whose child outlives it and keeps the port.
PY="$REPO_ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$REPO_ROOT/.venv/Scripts/python.exe"

export DJANGO_SETTINGS_MODULE="apps.config.settings_smoke"
export SMOKE_DB_PATH="$DB_FILE"

http_code() {
  "$PY" -c "
import sys, urllib.error, urllib.request

try:
    with urllib.request.urlopen(sys.argv[1], timeout=3) as response:
        print(response.status)
except urllib.error.HTTPError as error:
    print(error.code)
except Exception:
    print(0)
" "$1" 2>/dev/null
}

free_port() {
  "$PY" -c "
import socket, sys

start = int(sys.argv[1])
for port in range(start, start + 20):
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', port))
        except OSError:
            continue
    print(port)
    break
else:
    sys.exit(1)
" "$1" 2>/dev/null
}

server_pid() {
  [ -f "$PID_FILE" ] || return 1
  local pid
  pid="$(cat "$PID_FILE" 2>/dev/null)"
  [ -n "$pid" ] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  echo "$pid"
}

base_url() {
  echo "http://127.0.0.1:$(cat "$PORT_FILE" 2>/dev/null || echo "$DEFAULT_PORT")"
}

report_ready() {
  local url
  url="$(base_url)"
  echo "server:   $url (pid $(cat "$PID_FILE"), --noreload)"
  echo "login:    $url/account/login/"
  echo "email:    $SMOKE_EMAIL   (the form asks for the email address, not the username)"
  echo "password: $SMOKE_PASSWORD"
  echo "admin:    $url/admin/  (the smoke user is a superuser)"
  echo "database: ${DB_FILE#"$REPO_ROOT/"}"
  echo "log:      ${LOG_FILE#"$REPO_ROOT/"}"
  echo
  echo "Restart after every code change - this server does not autoreload."
}

do_stop() {
  local pid
  if pid="$(server_pid)"; then
    kill "$pid" 2>/dev/null
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      kill -0 "$pid" 2>/dev/null || break
      "$PY" -c "import time; time.sleep(0.3)"
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null
    fi
    echo "stopped server (pid $pid)"
  else
    echo "no server running for this run"
  fi
  rm -f "$PID_FILE"
}

check_prerequisites() {
  if [ ! -x "$PY" ]; then
    echo "no virtualenv interpreter at .venv - run 'uv sync' first" >&2
    return 1
  fi
  if [ ! -f "$REPO_ROOT/apps/config/settings_smoke.py" ]; then
    echo "missing apps/config/settings_smoke.py - the content review cannot isolate its database" >&2
    return 1
  fi

  # STATICFILES_DIRS points at node_modules: without it htmx, UIkit and the icon font all 404, every
  # interactive element on every page goes dead, and the whole review is false negatives. Fail here
  # rather than let a reviewer file "the button does nothing" against a working feature.
  if [ ! -d "$REPO_ROOT/node_modules/htmx.org" ] || [ ! -d "$REPO_ROOT/node_modules/uikit" ]; then
    echo "node_modules is missing or incomplete, installing it" >&2
    if command -v yarn > /dev/null 2>&1; then
      yarn install --frozen-lockfile >> "$SETUP_LOG" 2>&1
    elif command -v npm > /dev/null 2>&1; then
      npm install >> "$SETUP_LOG" 2>&1
    fi
  fi
  if [ ! -d "$REPO_ROOT/node_modules/htmx.org" ] || [ ! -d "$REPO_ROOT/node_modules/uikit" ]; then
    echo "still no node_modules/htmx.org and node_modules/uikit - install the frontend dependencies" >&2
    echo "('yarn install'). Without them htmx and UIkit 404 and nothing on the page responds." >&2
    return 1
  fi
  return 0
}

prepare_database() {
  : > "$SETUP_LOG"

  "$PY" manage.py migrate --noinput >> "$SETUP_LOG" 2>&1 || {
    echo "migrate failed, see ${SETUP_LOG#"$REPO_ROOT/"}" >&2
    return 1
  }

  # The item and warrior generators query cultures and item types by name and raise without them.
  "$PY" manage.py loaddata culture itemtype >> "$SETUP_LOG" 2>&1 || {
    echo "loaddata culture itemtype failed, see ${SETUP_LOG#"$REPO_ROOT/"}" >&2
    return 1
  }

  "$PY" manage.py shell -c "
from django.contrib.auth import get_user_model

user_model = get_user_model()
user, _ = user_model.objects.get_or_create(username='$SMOKE_USER')
user.email = '$SMOKE_EMAIL'
user.is_active = True
user.is_staff = True
user.is_superuser = True
user.set_password('$SMOKE_PASSWORD')
user.save()
" >> "$SETUP_LOG" 2>&1 || {
    echo "seeding the smoke user failed, see ${SETUP_LOG#"$REPO_ROOT/"}" >&2
    return 1
  }

  # A lockout left over from an earlier round would look exactly like broken login code.
  "$PY" manage.py axes_reset >> "$SETUP_LOG" 2>&1 \
    || echo "note: axes_reset did not run - a stale lockout may still be in the smoke database" >&2

  return 0
}

do_start() {
  local pid url
  if pid="$(server_pid)"; then
    url="$(base_url)"
    if [ "$(http_code "$url/account/login/")" = "200" ]; then
      echo "reusing the server already running for this run"
      report_ready
      return 0
    fi
    echo "the recorded server is not answering, replacing it"
    do_stop > /dev/null
  fi

  check_prerequisites || return 1
  prepare_database || return 1

  local port
  port="$(free_port "${PORT_ARG:-$DEFAULT_PORT}")"
  if [ -z "$port" ]; then
    echo "no free port in the 20 above ${PORT_ARG:-$DEFAULT_PORT}" >&2
    return 1
  fi

  # --noreload keeps this one process the whole server: the autoreloader forks a child that would
  # survive killing the parent, hold the port, and serve the pre-fix code to the next round.
  : > "$LOG_FILE"
  "$PY" manage.py runserver "127.0.0.1:$port" --noreload >> "$LOG_FILE" 2>&1 &
  local server_process=$!
  echo "$server_process" > "$PID_FILE"
  echo "$port" > "$PORT_FILE"

  url="http://127.0.0.1:$port"
  for _ in $(seq 1 40); do
    if [ "$(http_code "$url/account/login/")" = "200" ]; then
      report_ready
      return 0
    fi
    kill -0 "$server_process" 2>/dev/null || break
    "$PY" -c "import time; time.sleep(0.5)"
  done

  echo "the server never answered on $url - last 40 lines of the log:" >&2
  tail -n 40 "$LOG_FILE" >&2
  do_stop > /dev/null
  return 1
}

case "$VERB" in
  start)
    do_start
    ;;
  fresh)
    do_stop > /dev/null
    rm -f "$DB_FILE"
    echo "deleted the smoke database, starting from an empty world"
    do_start
    ;;
  restart)
    do_stop
    do_start
    ;;
  stop)
    do_stop
    ;;
  status)
    if pid="$(server_pid)"; then
      url="$(base_url)"
      code="$(http_code "$url/account/login/")"
      if [ "$code" = "200" ]; then
        echo "up"
        report_ready
      else
        echo "pid $pid is alive but $url/account/login/ answered $code - restart it"
        exit 1
      fi
    else
      echo "down (no server running for this run)"
      exit 1
    fi
    ;;
  *)
    echo "unknown verb '$VERB' - use start, fresh, restart, stop or status" >&2
    exit 1
    ;;
esac
