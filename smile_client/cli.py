"""Smile Client

Usage:
  cli.py start_listener --config=<config_file> --subject=<subject> [--start-date=<date>] [--debug]
  cli.py (-h | --help)
  cli.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --config=<config_file>    Configuration file path [required].
  --subject=<subject>       NATS subject to consume from [required].
  --start-date=<date>       Start date in YYYY-MM-DD format [optional].
  --debug                   Set logging level to DEBUG [optional].

"""
import json
import logging
import asyncio
import datetime
from docopt import docopt
from .smile_client import SmileClient


def load_config(config_file):
    """Load configuration from JSON file."""
    with open(config_file, 'r') as f:
        return json.load(f)


def parse_start_date(date_str):
    """Parse date string in YYYY-MM-DD format to datetime object."""
    if not date_str:
        return None
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.replace(tzinfo=datetime.timezone.utc, hour=0, minute=0, second=0, microsecond=0)
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD format.")


def start_listener(config_file, subject, start_date=None):
    """Start the listener with the given config file, subject and optional start date."""
    config = load_config(config_file)
    client = SmileClient(config)
    parsed_start_date = parse_start_date(start_date)
    asyncio.run(client.start_consuming(subject, start_date=parsed_start_date))


def main():
    arguments = docopt(__doc__, version='Smile Client 1.0')

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if arguments["--debug"]:
        logging.getLogger().setLevel(logging.DEBUG)

    if arguments['start_listener']:
        config_file = arguments['--config']
        subject = arguments['--subject']
        start_date = arguments['--start-date']
        start_listener(config_file, subject, start_date)


if __name__ == "__main__":
    main()
