from django.db import migrations
from decimal import Decimal


def setup_two_leave_types(apps, schema_editor):
    LeaveType = apps.get_model('leave_management', 'LeaveType')
    LeaveBalance = apps.get_model('leave_management', 'LeaveBalance')
    LeaveRequest = apps.get_model('leave_management', 'LeaveRequest')
    EmployeeProfile = apps.get_model('employees', 'EmployeeProfile')

    # 1. Ensure Sick Leave (SL) exists
    sl_type, _ = LeaveType.objects.get_or_create(
        code='SL',
        defaults={
            'name': 'Sick Leave',
            'days_per_year': Decimal('12.0'),
            'is_paid': True,
            'requires_attachment': True,
            'description': 'Medical illness or health consultations.'
        }
    )
    if sl_type.name != 'Sick Leave':
        sl_type.name = 'Sick Leave'
        sl_type.days_per_year = Decimal('12.0')
        sl_type.is_paid = True
        sl_type.save()

    # 2. Ensure Paid Leave (PL) exists
    pl_type, _ = LeaveType.objects.get_or_create(
        code='PL',
        defaults={
            'name': 'Paid Leave',
            'days_per_year': Decimal('18.0'),
            'is_paid': True,
            'requires_attachment': False,
            'description': 'Annual paid leave and planned rest days.'
        }
    )
    if pl_type.name != 'Paid Leave':
        pl_type.name = 'Paid Leave'
        pl_type.days_per_year = Decimal('18.0')
        pl_type.is_paid = True
        pl_type.save()

    # 3. Migrate any existing LeaveRequests referencing other types to PL
    LeaveRequest.objects.exclude(leave_type=sl_type).update(leave_type=pl_type)

    # 4. Migrate LeaveBalances for all employees
    for emp in EmployeeProfile.objects.all():
        for year in [2025, 2026, 2027]:
            # SL balance
            sl_bal = LeaveBalance.objects.filter(employee=emp, leave_type=sl_type, year=year).first()
            if not sl_bal:
                LeaveBalance.objects.create(
                    employee=emp,
                    leave_type=sl_type,
                    year=year,
                    allocated_days=Decimal('12.0'),
                    used_days=Decimal('0.0'),
                    pending_days=Decimal('0.0')
                )
            else:
                sl_bal.allocated_days = Decimal('12.0')
                sl_bal.save()

            # PL balance: collect used and pending from other leave types (CL, EL)
            old_other_balances = list(LeaveBalance.objects.filter(
                employee=emp,
                year=year
            ).exclude(leave_type__in=[sl_type, pl_type]))

            total_used = sum(b.used_days for b in old_other_balances)
            total_pending = sum(b.pending_days for b in old_other_balances)

            pl_bal = LeaveBalance.objects.filter(employee=emp, leave_type=pl_type, year=year).first()
            if not pl_bal:
                LeaveBalance.objects.create(
                    employee=emp,
                    leave_type=pl_type,
                    year=year,
                    allocated_days=Decimal('18.0'),
                    used_days=total_used,
                    pending_days=total_pending
                )
            else:
                pl_bal.allocated_days = Decimal('18.0')
                if total_used > 0:
                    pl_bal.used_days = max(pl_bal.used_days, total_used)
                if total_pending > 0:
                    pl_bal.pending_days = max(pl_bal.pending_days, total_pending)
                pl_bal.save()

    # 5. Remove old balances for non-SL/PL
    LeaveBalance.objects.exclude(leave_type__in=[sl_type, pl_type]).delete()

    # 6. Delete other LeaveTypes (CL, EL, LOP)
    LeaveType.objects.exclude(code__in=['SL', 'PL']).delete()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('leave_management', '0001_initial'),
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(setup_two_leave_types, reverse_func),
    ]

