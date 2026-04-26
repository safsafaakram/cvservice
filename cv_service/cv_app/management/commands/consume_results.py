from django.core.management.base import BaseCommand

from cv_app.consumers.result_consumer import start_result_consumer


class Command(BaseCommand):
    help = "Consume CV scoring results from RabbitMQ and update stored CV scores."

    def handle(self, *args, **options):
        start_result_consumer()
