"""
Management command: create_admin_from_env

Bootstraps a real Django superuser from the ADMIN_EMAIL / ADMIN_PASSWORD
environment variables (set in Vercel). This replaces the old hardcoded
fallback credentials that used to live in views.py.

Run at deploy time via vercel.json buildCommand:
    python manage.py create_admin_from_env --noinput

If either env var is missing in production, startup validation in
settings.py will already have failed fast; this command additionally
raises a clear CommandError so it can never silently no-op.
"""

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q


class Command(BaseCommand):
    help = "Create or update the Django superuser from ADMIN_EMAIL/ADMIN_PASSWORD env vars."

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_true",
            help="Do NOT prompt for input of any kind (always safe here).",
        )

    def handle(self, *args, **options):
        email = os.getenv("ADMIN_EMAIL", "").strip()
        password = os.getenv("ADMIN_PASSWORD", "").strip()

        if not email or not password:
            raise CommandError(
                "ADMIN_EMAIL and ADMIN_PASSWORD must be set as environment variables "
                "to create the admin superuser."
            )

        # Find existing user by email or username to avoid duplicates.
        admin = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
        created = admin is None

        if created:
            admin = User.objects.create_user(
                username=email, email=email, password=password
            )
        else:
            admin.email = email
            admin.set_password(password)

        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{action} superuser '{email}' (is_staff=True, is_superuser=True)."
        ))
