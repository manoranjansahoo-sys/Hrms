import datetime
from django.db import migrations


def seed_holidays_and_schedules(apps, schema_editor):
    Holiday = apps.get_model('organization', 'Holiday')
    OperatingSchedule = apps.get_model('organization', 'OperatingSchedule')
    MasterDataPermission = apps.get_model('organization', 'MasterDataPermission')

    # 1. 14 Official Company Holidays for 2026
    official_2026_holidays = [
        ('2026-01-14', 'Makar Sankranti', 'FESTIVAL', 'Harvest and solar festival celebration.'),
        ('2026-01-26', 'Republic Day', 'PUBLIC', 'National holiday honouring the Constitution of India.'),
        ('2026-02-15', 'Maha Shivratri', 'FESTIVAL', 'Auspicious Hindu festival honoring Lord Shiva.'),
        ('2026-03-04', 'Holi', 'FESTIVAL', 'Festival of colors and spring celebration.'),
        ('2026-05-01', 'May Day', 'PUBLIC', 'International Workers Day celebration.'),
        ('2026-06-14', 'Raja', 'FESTIVAL', 'Celebration of earth and festivities.'),
        ('2026-07-16', 'Rath Yatra', 'FESTIVAL', 'Annual chariot procession and sacred celebration.'),
        ('2026-08-15', 'Independence Day', 'PUBLIC', 'National holiday commemorating Indian independence.'),
        ('2026-08-28', 'Raksha Bandhan', 'FESTIVAL', 'Traditional festival celebrating bonds of protection.'),
        ('2026-09-14', 'Ganesh Chaturthi', 'FESTIVAL', 'Grand festival celebrating the birth of Lord Ganesha.'),
        ('2026-10-19', 'Dussehra (Maha Navami)', 'FESTIVAL', 'Dussehra festival - Day 1 celebrations.'),
        ('2026-10-20', 'Dussehra (Vijaya Dashami)', 'FESTIVAL', 'Dussehra festival - Day 2 celebrations.'),
        ('2026-11-08', 'Diwali', 'FESTIVAL', 'Festival of lights and festivities.'),
        ('2026-11-24', 'Kartik Poornima', 'FESTIVAL', 'Full moon festival and sacred holy day.')
    ]

    for date_str, title, h_type, desc in official_2026_holidays:
        h_date = datetime.date.fromisoformat(date_str)
        Holiday.objects.update_or_create(
            date=h_date,
            defaults={
                'title': title,
                'holiday_type': h_type,
                'description': desc,
                'is_optional': False
            }
        )

    # 2. Operating Schedules for Monday - Sunday (Sunday = Weekly Off)
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for d_idx, d_name in enumerate(day_names):
        is_work = (d_idx != 6)  # Sunday (6) is weekly off
        OperatingSchedule.objects.get_or_create(
            day_of_week=d_idx,
            defaults={
                'day_name': d_name,
                'is_working_day': is_work,
                'opening_time': '09:30:00',
                'closing_time': '18:30:00',
                'grace_period_minutes': 15,
                'notes': 'Company standard business hours' if is_work else 'Sunday Company Weekly Off'
            }
        )

    # 3. MasterDataPermission singleton
    MasterDataPermission.objects.get_or_create(
        singleton_id=1,
        defaults={
            'allow_all_hr': False,
            'can_manage_holidays': True,
            'can_manage_timings': True,
            'can_manage_locations': True,
            'can_manage_leave_policy': True
        }
    )


class Migration(migrations.Migration):
    dependencies = [
        ('organization', '0003_operatingschedule_masterdatapermission'),
    ]

    operations = [
        migrations.RunPython(seed_holidays_and_schedules, reverse_code=migrations.RunPython.noop),
    ]

