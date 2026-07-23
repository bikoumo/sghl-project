from django.core import management


def run_archive_deceased():
    """Entrypoint appelé par django-q ou par un scheduler pour exécuter l'archivage."""
    management.call_command('archive_deceased')
