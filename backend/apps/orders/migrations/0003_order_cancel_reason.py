from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="cancel_reason",
            field=models.TextField(
                blank=True, default="", verbose_name="Bekor qilish sababi"
            ),
        ),
    ]
