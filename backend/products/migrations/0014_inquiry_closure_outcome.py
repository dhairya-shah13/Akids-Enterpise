from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_inquiry_inquiry_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='inquiry',
            name='closure_outcome',
            field=models.CharField(blank=True, choices=[('WON', 'Customer Won'), ('LOST', 'Customer Lost')], default='', max_length=10),
        ),
    ]
