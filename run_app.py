"""PyInstaller entry point. Not used for normal development (use `python -m sailplane_calc.app`)."""
import sys

from sailplane_calc.app import main

if __name__ == "__main__":
    sys.exit(main())
