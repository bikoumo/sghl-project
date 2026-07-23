from django.apps import AppConfig


class ClinicalConfig(AppConfig):
    name = 'clinical'

    def ready(self):
        # Attempt to create a django-q Schedule to run the archival daily.
        try:
            from django_q.models import Schedule
            from django.utils import timezone

            # Create schedule if not present
            Schedule.objects.get_or_create(
                name='archive_deceased_daily',
                defaults={
                    'func': 'clinical.tasks.run_archive_deceased',
                    'schedule_type': Schedule.DAILY if hasattr(Schedule, 'DAILY') else 'D',
                    'next_run': timezone.now(),
                    'repeats': -1,
                }
            )
        except Exception:
            # django-q not installed or schedule creation failed; skip silently
            pass
