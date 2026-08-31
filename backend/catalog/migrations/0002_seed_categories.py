from django.db import migrations
from django.utils.text import slugify

CATEGORIES = [
    ("Maquillaje", 0),
    ("Uñas", 1),
    ("Pestañas", 2),
]


def seed_categories(apps, schema_editor):
    ServiceCategory = apps.get_model("catalog", "ServiceCategory")
    for name, display_order in CATEGORIES:
        ServiceCategory.objects.get_or_create(
            name=name,
            defaults={"slug": slugify(name), "display_order": display_order},
        )


def remove_categories(apps, schema_editor):
    ServiceCategory = apps.get_model("catalog", "ServiceCategory")
    ServiceCategory.objects.filter(name__in=[name for name, _ in CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_categories),
    ]
