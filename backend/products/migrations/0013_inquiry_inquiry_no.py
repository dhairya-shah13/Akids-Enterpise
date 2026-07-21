from django.db import migrations, models

def backfill_inquiry_no(apps, schema_editor):
    Inquiry = apps.get_model('products', 'Inquiry')
    # Order by created_at ascending, then id ascending as tiebreaker
    inquiries = Inquiry.objects.all().order_by('created_at', 'id')
    count = 1
    for inquiry in inquiries:
        inquiry.inquiry_no = f"INQ-{count:04d}"
        inquiry.save(update_fields=['inquiry_no'])
        count += 1

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0012_userprofile_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='inquiry',
            name='inquiry_no',
            field=models.CharField(default='', max_length=20, editable=False),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_inquiry_no, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='inquiry',
            name='inquiry_no',
            field=models.CharField(max_length=20, unique=True, editable=False),
        ),
    ]
