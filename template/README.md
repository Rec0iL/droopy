# __APP_NAME__

__APP_COMMENT__

Drag & drop files (or whole folders) onto the window, the menu entry, or use "Open with".

## Install

```bash
./install.sh                 # per-user: ~/.local (menu entry + icon + `__APP_ID__` command)
./install.sh --link          # per-user, symlinked to this checkout (development)
sudo ./install.sh --system   # system-wide: /usr/local
./uninstall.sh [--system] [--purge]   # --purge also removes settings
```

Requires PySide6 (Fedora/Nobara: `sudo dnf install python3-pyside6`) plus:

```bash
pip install -r requirements.txt
python3 main.py            # or: python3 main.py file1 folder2 ...
```

__README_BODY__

- Settings live in `~/.config/__APP_NAME__/settings.json`.
- Terminal use without the GUI: `python3 -m __APP_ID__.core <files> [-o DIR]`
- Shader source: `shaders/bg.frag`. Recompile after editing:
  `qsb-qt6 --glsl "100 es,120,150" --hlsl 50 --msl 12 -o shaders/bg.frag.qsb shaders/bg.frag`
- Tests: `python3 -m unittest tests.test_core`

Generated with `/droopy`; `droopy.json` records the choices so `/droopy update .` can refresh the scaffold.
