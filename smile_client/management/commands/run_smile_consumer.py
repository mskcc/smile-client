import asyncio
import datetime
import logging
from smile_client import SmileClient
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger("smile_client")


class Command(BaseCommand):
    help = 'Run Smile Consumer'

    def add_arguments(self, parser):
        parser.add_argument("--subject", type=str, required=True, help="NATS subject to consume from")
        parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format")

    def parse_start_date(self, date_str):
        """Parse date string in YYYY-MM-DD format to datetime object."""
        if not date_str:
            return None
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.replace(tzinfo=datetime.timezone.utc, hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            raise CommandError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD format.")

    def handle(self, *args, **options):
        subject = options["subject"]
        start_date = options.get("start_date")

        try:
            client = SmileClient()
            parsed_start_date = self.parse_start_date(start_date)
            
            self.stdout.write(self.style.SUCCESS(f"Starting Smile Consumer with subject: {subject}"))
            if parsed_start_date:
                self.stdout.write(self.style.SUCCESS(f"Start date: {parsed_start_date}"))
            
            asyncio.run(client.start_consuming(subject, start_date=parsed_start_date))
        except Exception as e:
            logger.error(f"Error: {e}")
            raise CommandError(f"Failed to start consumer: {e}")