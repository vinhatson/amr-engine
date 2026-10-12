from .cli import main
import sys

# --- UTF-8 console (Windows cp1252 would otherwise abort on the first
#     Vietnamese or Greek character printed below) ---
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):      # non-TTY or already wrapped
        pass
sys.exit(main())
