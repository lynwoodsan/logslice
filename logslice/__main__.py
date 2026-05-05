"""Allow running logslice as a module: python -m logslice."""

import sys
from logslice.cli import main

if __name__ == "__main__":
    sys.exit(main())
