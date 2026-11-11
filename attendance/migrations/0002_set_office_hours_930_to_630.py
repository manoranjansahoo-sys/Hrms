from django.db import migrations
from datetime import time
from decimal import Decimal


def set_standard_office_hours(apps, schema_editor):
    Shift = apps.get_model('attendance', 'Shift')
    Attendance = apps.get_model('attendance', 'Attendance')

    # Update or create the universal company office schedule: 9:30 AM to 6:30 PM
    standard_shift = Shift.objects.filter(is_default=True).first() or Shift.objects.first()
    if not standard_shift:
        standard_shift = Shift.objects.create(
            name='Office Hours',
            start_time=time(9, 30),
            end_time=time(18, 30),
            grace_period_minutes=0,
            half_day_hours=Decimal('4.50'),
            full_day_hours=Decimal('8.00'),
            is_default=True,
        )
    else:
        standard_shift.name = 'Office Hours'
        standard_shift.start_time = time(9, 30)
        standard_shift.end_time = time(18, 30)
        standard_shift.grace_period_minutes = 0
        standard_shift.half_day_hours = Decimal('4.50')
        standard_shift.full_day_hours = Decimal('8.00')
        standard_shift.is_default = True
        standard_shift.save()

    # Remove any extra shift definitions (company operates exclusively on standard office hours)
    Shift.objects.exclude(id=standard_shift.id).delete()
    Attendance.objects.all().update(shift=standard_shift)


def reverse_office_hours(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_standard_office_hours, reverse_office_hours),
    ]

