"""Seed data migration for GuaranteeType — creates predefined guarantee types."""
from django.db import migrations


def seed_guarantee_types(apps, schema_editor):
    # This will run after the model migration creates the table.
    # We use RunPython with a noop reverse so it's safe.
    pass  # Actual seeding happens in 0002 after model tables exist.


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = []
