#!/usr/bin/env bash
# __APP_NAME__ installer - installs the app, launcher, icon and .desktop entry.
#
#   ./install.sh              per-user install into ~/.local   (no sudo needed)
#   ./install.sh --system     system-wide install into /usr/local (run with sudo)
#   ./install.sh --link       per-user, but symlink to this checkout (for development)
#   ./install.sh --help
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="user"
LINK=0

for arg in "$@"; do
    case "$arg" in
        --system) MODE="system" ;;
        --link)   LINK=1 ;;
        -h|--help) sed -n '2,7p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Unknown option: $arg (try --help)" >&2; exit 1 ;;
    esac
done

if [[ "$MODE" == "system" ]]; then
    if [[ $EUID -ne 0 ]]; then
        echo "--system needs root: sudo $0 --system" >&2
        exit 1
    fi
    PREFIX="/usr/local"
    APP_DIR="$PREFIX/share/__APP_ID__"
    BIN_DIR="$PREFIX/bin"
    APPS_DIR="$PREFIX/share/applications"
    ICON_DIR="$PREFIX/share/icons/hicolor/scalable/apps"
else
    if [[ $EUID -eq 0 ]]; then
        echo "Running as root without --system would install into root's home. Aborting." >&2
        exit 1
    fi
    DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
    APP_DIR="$DATA_HOME/__APP_ID__"
    BIN_DIR="$HOME/.local/bin"
    APPS_DIR="$DATA_HOME/applications"
    ICON_DIR="$DATA_HOME/icons/hicolor/scalable/apps"
fi

say()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!! \033[0m %s\n' "$*" >&2; }

# ---------------------------------------------------------------- dependency checks
command -v python3 >/dev/null || { echo "python3 is required." >&2; exit 1; }

MISSING=()
python3 -c 'import PySide6.QtQuick, PySide6.QtQuickControls2' 2>/dev/null || MISSING+=("PySide6")
for mod in __PY_DEPS__; do
    python3 -c "import $mod" 2>/dev/null || MISSING+=("$mod")
done
if [[ ${#MISSING[@]} -gt 0 ]]; then
    warn "Missing Python packages for $(command -v python3): ${MISSING[*]}"
    warn "  Fedora/Nobara:  sudo dnf install python3-pyside6   (others via pip)"
    warn "  any distro:     python3 -m pip install --user ${MISSING[*]}"
fi
__TOOL_CHECKS__
[[ -f "$SRC_DIR/shaders/bg.frag.qsb" || ! -f "$SRC_DIR/shaders/bg.frag" ]] || warn "shaders/bg.frag.qsb missing - compile it first (see README)."

# ---------------------------------------------------------------- install files
say "Installing to $APP_DIR"
mkdir -p "$BIN_DIR" "$APPS_DIR" "$ICON_DIR"

if [[ $LINK -eq 1 ]]; then
    rm -rf "$APP_DIR"
    ln -s "$SRC_DIR" "$APP_DIR"
else
    rm -rf "$APP_DIR"
    mkdir -p "$APP_DIR/shaders" "$APP_DIR/packaging"
    cp -r "$SRC_DIR/__APP_ID__" "$SRC_DIR/qml" "$APP_DIR/"
    cp "$SRC_DIR/main.py" "$APP_DIR/"
    cp "$SRC_DIR/packaging/__APP_ID__.svg" "$APP_DIR/packaging/"
    cp "$SRC_DIR"/shaders/bg.frag* "$APP_DIR/shaders/" 2>/dev/null || true
    find "$APP_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} +
fi

say "Writing launcher $BIN_DIR/__APP_ID__"
cat > "$BIN_DIR/__APP_ID__" <<EOL
#!/usr/bin/env bash
exec python3 "$APP_DIR/main.py" "\$@"
EOL
chmod 755 "$BIN_DIR/__APP_ID__"

say "Installing icon"
cp "$SRC_DIR/packaging/__APP_ID__.svg" "$ICON_DIR/__APP_ID__.svg"

say "Writing desktop entry $APPS_DIR/__APP_ID__.desktop"
cat > "$APPS_DIR/__APP_ID__.desktop" <<EOL
[Desktop Entry]
Type=Application
Version=1.0
Name=__APP_NAME__
GenericName=__GENERIC_NAME__
Comment=__APP_COMMENT__
Exec=$BIN_DIR/__APP_ID__ %F
Icon=__APP_ID__
Terminal=false
Categories=__CATEGORIES__
Keywords=__KEYWORDS__
MimeType=__MIMETYPES__
StartupWMClass=__APP_ID__
StartupNotify=true
EOL
chmod 644 "$APPS_DIR/__APP_ID__.desktop"

# ---------------------------------------------------------------- refresh caches
command -v desktop-file-validate >/dev/null && desktop-file-validate "$APPS_DIR/__APP_ID__.desktop" || true
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS_DIR" 2>/dev/null || true
if command -v gtk-update-icon-cache >/dev/null; then
    gtk-update-icon-cache -q -t "$(dirname "$(dirname "$ICON_DIR")")" 2>/dev/null || true
fi
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 >/dev/null 2>&1 || true

say "Done! Launch it from your application menu, drop files on it, or run: __APP_ID__ <files>"
if [[ "$MODE" == "user" && ":$PATH:" != *":$BIN_DIR:"* ]]; then
    warn "$BIN_DIR is not in your PATH - the menu entry works, but add it to run '__APP_ID__' from a terminal."
fi
[[ ${#MISSING[@]} -eq 0 ]] || warn "Install the missing Python packages (see above) before starting the app."
