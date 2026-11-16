from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from recruitment.models import Candidate
from recruitment.views import sync_candidate_photo_to_user_avatar


class Command(BaseCommand):
    help = "Syncs onboarding candidate passport photographs to employee CustomUser avatars across all existing users."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing user avatars with candidate onboarding photos.',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        synced_count = 0
        total_candidates = Candidate.objects.count()

        self.stdout.write(f"Scanning {total_candidates} candidates for onboarding profile pictures...")

        for cand in Candidate.objects.all():
            user = CustomUser.objects.filter(email__iexact=cand.email).first()
            if user:
                synced = sync_candidate_photo_to_user_avatar(cand, user, force=force)
                if synced:
                    synced_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Synced photo for '{cand.full_name}' -> User '{user.username}' (Avatar: {user.avatar.name})"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully synced {synced_count} employee profile pictures.")
        )
