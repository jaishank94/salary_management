"""Command line entry point: python -m app.seed --count 10000 --reset"""

import argparse
import os
import sys

from app.db import default_db_path, sqlite_url
from app.errors import DomainError
from app.seeding import seed_url


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed the Northstar employee directory.")
    parser.add_argument("--count", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reset", action="store_true", help="Replace existing employees.")
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args(argv)
    url = args.database_url or os.environ.get("DATABASE_URL") or sqlite_url(default_db_path())
    try:
        seed_url(url, count=args.count, seed=args.seed, reset=args.reset)
    except DomainError as exc:
        print(exc.message, file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
