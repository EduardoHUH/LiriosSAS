from django.db import migrations


def seed_business_settings(apps, schema_editor):
    BusinessSettings = apps.get_model("core", "BusinessSettings")
    BusinessSettings.objects.get_or_create(pk=1, defaults={"business_name": "Lirios"})


def remove_business_settings(apps, schema_editor):
    BusinessSettings = apps.get_model("core", "BusinessSettings")
    BusinessSettings.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_business_settings, remove_business_settings),
    ]
