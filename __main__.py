"""Entry point so `python -m cpm_scheduler` runs the CLI."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
