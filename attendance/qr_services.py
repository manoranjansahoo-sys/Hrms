import time
import hmac
import hashlib
import qrcode
import io
import base64
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.db import models
from attendance.models import Attendance, Shift, AttendanceAuditLog, QRCodeScanLog
from accounts.models import CustomUser


def generate_dynamic_qr_payload(site, request=None):
    """
    Generates a secure 4-second rotating cryptographic token and QR image for an office site kiosk.
    
    Payload components:
    - Site ID
    - 4-second Slot Index
    - HMAC-SHA256 signature
    - Base64 QR code image
    - Countdown timer (seconds remaining in current 4s rotation window)
    """
    rotation = site.qr_rotation_seconds or 4
    now_ts = time.time()
    slot = int(now_ts // rotation)
    seconds_remaining = round(rotation - (now_ts % rotation), 1)

    secret = site.get_qr_secret_key()
    msg = f"{site.id}:{slot}".encode('utf-8')
    sig = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()[:16]

    # Compact token format: SITE_ID:SLOT:SIGNATURE
    token_str = f"{site.id}:{slot}:{sig}"

    # Build direct scanner URL (allows native phone camera or web scanner)
    if request:
        try:
            direct_url = request.build_absolute_uri(
                reverse('attendance:qr_punch_direct')
            ) + f"?token={token_str}&site={site.id}"
        except Exception:
            direct_url = f"/attendance/qr-punch/?token={token_str}&site={site.id}"
    else:
        direct_url = f"HRMS-QR:{token_str}"

    # Generate QR Code image (Base64 PNG)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(direct_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode('utf-8')

    return {
        'token': token_str,
        'slot': slot,
        'site_id': site.id,
        'site_name': site.name,
        'site_code': site.code,
        'city': site.city,
        'rotation_seconds': rotation,
        'countdown_seconds': seconds_remaining,
        'qr_data_url': direct_url,
        'qr_image_base64': qr_b64,
        'timestamp': timezone.now().isoformat(),
        'geofence_radius': site.geofence_radius_meters or 200,
        'has_gps': bool(site.latitude and site.longitude),
    }


def validate_dynamic_qr_token(site, token_str, max_age_slots=0):
    """
    Validates the dynamic QR token.
    Must belong to the site, have a valid cryptographic HMAC signature,
    and have been generated in the current 4-second slot. Previous QR codes expire immediately.
    
    Returns: (is_valid: bool, status_code: str, error_message: str|None, token_age_sec: float)
    """
    if not token_str:
        return False, "INVALID_TOKEN", "Empty QR token provided.", None

    parts = token_str.strip().split(':')
    if len(parts) != 3:
        return False, "INVALID_TOKEN", "Malformed QR token structure.", None

    site_id_str, slot_str, sig = parts
    try:
        token_site_id = int(site_id_str)
        slot = int(slot_str)
    except ValueError:
        return False, "INVALID_TOKEN", "Invalid QR token parameters.", None

    if token_site_id != site.id:
        return False, "INVALID_TOKEN", f"QR Code was generated for another office site (Site #{token_site_id}).", None

    # Cryptographic signature verification
    secret = site.get_qr_secret_key()
    msg = f"{site.id}:{slot}".encode('utf-8')
    expected_sig = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()[:16]

    if not hmac.compare_digest(sig, expected_sig):
        return False, "INVALID_TOKEN", "QR Code security signature verification failed (Tampered or forged QR).", None

    # Time slot verification (4-second dynamic rotation)
    rotation = site.qr_rotation_seconds or 4
    now_ts = time.time()
    current_slot = int(now_ts // rotation)
    slot_diff = current_slot - slot
    token_age_sec = (now_ts - (slot * rotation))

    if slot_diff < 0:
        return False, "INVALID_TOKEN", "Invalid time synchronization (Token is from the future).", token_age_sec

    # Strictly expires after rotation window (4 seconds, with max 0.5s network transit buffer)
    if slot_diff > max_age_slots or token_age_sec > (rotation + 0.5):
        return False, "EXPIRED_QR", (
            f"QR Code Expired ({round(token_age_sec, 1)}s old, exceeds {rotation}s dynamic limit). "
            "Please scan the live QR code currently visible on the office kiosk screen."
        ), token_age_sec

    return True, "VALID", None, token_age_sec


def process_qr_attendance_punch(request, user, site, token_str, latitude=None, longitude=None, punch_mode='AUTO'):
    """
    Executes a complete dynamic QR attendance scan:
    1. Validates 4-second dynamic token (strictly expires every 4s).
    2. Enforces Single-Use per Slot / Token (one employee per slot, no screenshot reuse).
    3. Strictly enforces device GPS location within 200m radius.
    4. Auto-detects or respects Punch In / Punch Out mode.
    5. Records Attendance and creates audit logs.
    
    Returns dictionary with detailed result status and punch data.
    """
    emp = getattr(user, 'employee_profile', None)
    if not emp:
        return {
            'success': False,
            'status': 'NO_EMPLOYEE_PROFILE',
            'title': 'Employee Profile Required',
            'message': 'Your user account does not have an active employee profile linked in HRMS.',
        }

    # Extract client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(',')[0].strip()
    else:
        client_ip = request.META.get('REMOTE_ADDR') or '127.0.0.1'

    # Step 1: Validate 4-second dynamic QR token
    is_token_valid, token_status, token_err, token_age_sec = validate_dynamic_qr_token(site, token_str)
    
    # Parse slot index from token
    slot_num = None
    if token_str and ':' in token_str:
        try:
            slot_num = int(token_str.split(':')[1])
        except (IndexError, ValueError):
            slot_num = None

    if not is_token_valid:
        QRCodeScanLog.objects.create(
            site=site,
            employee=emp,
            punch_mode=punch_mode,
            status=token_status,
            token_str=token_str or '',
            slot_index=slot_num,
            client_ip=client_ip,
            latitude=latitude,
            longitude=longitude,
            token_age_seconds=token_age_sec,
            error_message=token_err or "Invalid token"
        )
        return {
            'success': False,
            'status': token_status,
            'title': 'QR Verification Failed' if token_status != 'EXPIRED_QR' else 'QR Code Expired',
            'message': token_err,
            'token_age_seconds': token_age_sec,
        }

    # Step 1.5: Anti-Screenshot & Single-Use per Slot Enforcement
    # If this slot or exact token was already scanned by any employee, reject duplicate use
    already_scanned = QRCodeScanLog.objects.filter(
        site=site,
        status='SUCCESS'
    ).filter(
        models.Q(token_str=token_str) | (models.Q(slot_index=slot_num) if slot_num else models.Q(pk=None))
    ).exists()

    if already_scanned:
        QRCodeScanLog.objects.create(
            site=site,
            employee=emp,
            punch_mode=punch_mode,
            status='SLOT_ALREADY_USED',
            token_str=token_str,
            slot_index=slot_num,
            client_ip=client_ip,
            latitude=latitude,
            longitude=longitude,
            token_age_seconds=token_age_sec,
            error_message="This dynamic QR code slot has already been scanned by an employee."
        )
        return {
            'success': False,
            'status': 'SLOT_ALREADY_USED',
            'title': 'QR Code Already Used',
            'message': (
                "This QR code has already been scanned by an employee. Each 4-second QR code "
                "can only be scanned once. Please scan the newly generated QR code on the screen."
            ),
            'token_age_seconds': token_age_sec,
        }

    # Step 2: Location Security Verification (Strictly GPS Geofenced 200m)
    radius = site.geofence_radius_meters or 200

    if latitude is None or longitude is None:
        QRCodeScanLog.objects.create(
            site=site,
            employee=emp,
            punch_mode=punch_mode,
            status='GPS_REQUIRED',
            token_str=token_str,
            slot_index=slot_num,
            client_ip=client_ip,
            token_age_seconds=token_age_sec,
            error_message="Device GPS location turned off or permission denied."
        )
        return {
            'success': False,
            'status': 'GPS_REQUIRED',
            'title': 'Location (GPS) Required',
            'message': 'Please turn on location (GPS) and camera on your device to punch in or punch out.',
        }

    gps_verified, distance_meters, gps_msg = site.is_gps_verified(latitude, longitude)

    if not gps_verified:
        QRCodeScanLog.objects.create(
            site=site,
            employee=emp,
            punch_mode=punch_mode,
            status='LOCATION_FAILED',
            token_str=token_str,
            slot_index=slot_num,
            client_ip=client_ip,
            latitude=latitude,
            longitude=longitude,
            distance_meters=distance_meters,
            token_age_seconds=token_age_sec,
            error_message=gps_msg
        )
        dist_str = f"{distance_meters}m" if distance_meters is not None else "Unknown distance"
        return {
            'success': False,
            'status': 'LOCATION_FAILED',
            'title': 'Location Security Check Failed',
            'message': (
                f"You are {dist_str} away from '{site.name}'. "
                f"You must be physically present within {radius} meters radius of the office location."
            ),
            'distance_meters': distance_meters,
            'geofence_radius': radius,
            'gps_status': gps_msg,
        }

    method_str = "GPS_GEOFENCE"
    verification_summary = f"GPS Verified: {distance_meters}m from office (Limit: {radius}m)"

    # Step 3: Determine Punch In vs Punch Out
    today = timezone.localdate()
    now = timezone.now()
    att = Attendance.objects.filter(employee=emp, date=today).first()

    punch_mode = (punch_mode or 'AUTO').upper()
    action = None

    if not att or not att.punch_in:
        # Candidate for Punch In
        if punch_mode == 'OUT':
            return {
                'success': False,
                'status': 'PUNCH_IN_REQUIRED',
                'title': 'Punch In Required First',
                'message': 'You have not checked in yet today. Please choose Punch In.',
            }
        action = 'PUNCH_IN'
    elif att.punch_in and not att.punch_out:
        # Candidate for Punch Out
        if punch_mode == 'IN':
            return {
                'success': False,
                'status': 'ALREADY_PUNCHED_IN',
                'title': 'Already Punched In',
                'message': f"You are already punched in today at {timezone.localtime(att.punch_in).strftime('%I:%M %p')}. Choose Punch Out to check out.",
            }
        action = 'PUNCH_OUT'
    else:
        # Already has both Punch In and Punch Out
        QRCodeScanLog.objects.create(
            site=site,
            employee=emp,
            attendance=att,
            punch_mode=punch_mode,
            actual_punch_type='COMPLETED',
            status='ALREADY_COMPLETED',
            token_str=token_str,
            slot_index=slot_num,
            client_ip=client_ip,
            latitude=latitude,
            longitude=longitude,
            distance_meters=distance_meters,
            verification_details=verification_summary,
            token_age_seconds=token_age_sec,
        )
        in_time_str = timezone.localtime(att.punch_in).strftime('%I:%M %p') if att.punch_in else '-'
        out_time_str = timezone.localtime(att.punch_out).strftime('%I:%M %p') if att.punch_out else '-'
        return {
            'success': False,
            'status': 'ALREADY_COMPLETED',
            'title': 'Attendance Already Complete for Today',
            'message': (
                f"You have already completed attendance for today ({today.strftime('%d %b %Y')}). "
                f"Punch In: {in_time_str} • Punch Out: {out_time_str} • Total: {att.working_hours} hours."
            ),
            'attendance_id': att.id,
            'working_hours': float(att.working_hours),
            'punch_in_time': in_time_str,
            'punch_out_time': out_time_str,
        }

    # Step 4: Execute Punch In or Punch Out
    shift = Shift.objects.filter(is_default=True).first() or Shift.objects.first()
    if not shift:
        from datetime import time as dt_time
        shift, _ = Shift.objects.get_or_create(
            name='Office Hours',
            defaults={
                'start_time': dt_time(9, 30),
                'end_time': dt_time(18, 30),
                'grace_period_minutes': 0,
                'full_day_hours': Decimal('8.00'),
                'half_day_hours': Decimal('4.50'),
                'is_default': True,
            }
        )

    if action == 'PUNCH_IN':
        if not att:
            att = Attendance(employee=emp, date=today)
        att.shift = shift
        att.punch_in = now
        att.punch_in_ip = client_ip
        att.punch_in_latitude = latitude
        att.punch_in_longitude = longitude
        att.device_source = 'QR_KIOSK'
        att.status = 'PRESENT'
        att.location_verified = True
        att.verification_method = method_str
        att.scan_distance_meters = distance_meters

        # Late arrival check (9:30 AM)
        start_t = shift.start_time or datetime.strptime("09:30", "%H:%M").time()
        grace_min = shift.grace_period_minutes or 0
        grace_time = (datetime.combine(today, start_t) + timedelta(minutes=grace_min)).time()
        if timezone.localtime(now).time() > grace_time:
            att.is_late = True

        att.save()

        # Audit & Scan Logging
        AttendanceAuditLog.objects.create(
            attendance=att,
            action=f"QR Kiosk Punch In at {site.name}",
            changed_by=user,
            new_data=f"Punch In: {now.isoformat()}, Method: {method_str}, Dist: {distance_meters}m, IP: {client_ip}",
            reason=f"Dynamic QR Scan verification at {site.name}"
        )
        QRCodeScanLog.objects.create(
            site=site,
            employee=emp,
            attendance=att,
            punch_mode=punch_mode,
            actual_punch_type='IN',
            status='SUCCESS',
            token_str=token_str,
            slot_index=slot_num,
            client_ip=client_ip,
            latitude=latitude,
            longitude=longitude,
            distance_meters=distance_meters,
            verification_details=verification_summary,
            token_age_seconds=token_age_sec,
        )

        punch_time_display = timezone.localtime(now).strftime('%I:%M:%S %p')
        return {
            'success': True,
            'status': 'PUNCH_IN_SUCCESS',
            'action': 'PUNCH_IN',
            'title': 'Punch In Successful!',
            'message': f"Welcome, {emp.full_name}! Check-in recorded at {punch_time_display}.",
            'employee_name': emp.full_name,
            'emp_id': emp.emp_id,
            'site_name': site.name,
            'time': punch_time_display,
            'is_late': att.is_late,
            'verification_method': method_str,
            'distance_meters': distance_meters,
        }

    elif action == 'PUNCH_OUT':
        att.punch_out = now
        att.punch_out_ip = client_ip
        att.punch_out_latitude = latitude
        att.punch_out_longitude = longitude
        att.location_verified = True
        att.scan_distance_meters = distance_meters
        att.calculate_hours()
        att.save()

        # Audit & Scan Logging
        AttendanceAuditLog.objects.create(
            attendance=att,
            action=f"QR Kiosk Punch Out at {site.name}",
            changed_by=user,
            new_data=f"Punch Out: {now.isoformat()}, Hours: {att.working_hours}, Status: {att.status}",
            reason=f"Dynamic QR Scan verification at {site.name}"
        )
        QRCodeScanLog.objects.create(
            site=site,
            employee=emp,
            attendance=att,
            punch_mode=punch_mode,
            actual_punch_type='OUT',
            status='SUCCESS',
            token_str=token_str,
            slot_index=slot_num,
            client_ip=client_ip,
            latitude=latitude,
            longitude=longitude,
            distance_meters=distance_meters,
            verification_details=verification_summary,
            token_age_seconds=token_age_sec,
        )

        punch_time_display = timezone.localtime(now).strftime('%I:%M:%S %p')
        in_time_display = timezone.localtime(att.punch_in).strftime('%I:%M %p')
        return {
            'success': True,
            'status': 'PUNCH_OUT_SUCCESS',
            'action': 'PUNCH_OUT',
            'title': 'Punch Out Successful!',
            'message': (
                f"Good job, {emp.full_name}! Punch Out recorded at {punch_time_display}. "
                f"Total working time: {att.working_hours} hours (In: {in_time_display})."
            ),
            'employee_name': emp.full_name,
            'emp_id': emp.emp_id,
            'site_name': site.name,
            'time': punch_time_display,
            'punch_in_time': in_time_display,
            'working_hours': float(att.working_hours),
            'overtime_hours': float(att.overtime_hours),
            'attendance_status': att.get_status_display(),
            'verification_method': method_str,
            'distance_meters': distance_meters,
        }

