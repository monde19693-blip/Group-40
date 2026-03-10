from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Booking, User, Facility, Notification
from functools import wraps

admin = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


@admin.route('/admin/requests')
@login_required
@admin_required
def manage_requests():
    status_filter = request.args.get('status', 'pending')
    query = Booking.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    all_bookings = query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/manage_requests.html',
        bookings=all_bookings, status_filter=status_filter)


@admin.route('/admin/requests/<int:booking_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_booking(booking_id):
    booking     = Booking.query.get_or_404(booking_id)
    admin_notes = request.form.get('admin_notes', '').strip()

    # Final conflict check before approving
    conflicts = Booking.check_conflict(
        booking.facility_id, booking.booking_date,
        booking.start_time,  booking.end_time,
        exclude_id=booking.id)
    if conflicts:
        flash('Cannot approve: conflict with an existing approved booking.', 'danger')
        return redirect(url_for('admin.manage_requests'))

    booking.status      = 'approved'
    booking.admin_notes = admin_notes
    db.session.add(Notification(
        user_id    = booking.user_id,
        message    = f'Your booking "{booking.title}" for {booking.facility.name} '
                     f'on {booking.booking_date} has been APPROVED.',
        type       = 'success',
        booking_id = booking.id,
    ))
    db.session.commit()
    flash(f'Booking "{booking.title}" approved.', 'success')
    return redirect(url_for('admin.manage_requests'))


@admin.route('/admin/requests/<int:booking_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_booking(booking_id):
    booking     = Booking.query.get_or_404(booking_id)
    admin_notes = request.form.get('admin_notes', '').strip()

    booking.status      = 'rejected'
    booking.admin_notes = admin_notes or 'Request rejected by administrator.'
    db.session.add(Notification(
        user_id    = booking.user_id,
        message    = f'Your booking "{booking.title}" for {booking.facility.name} '
                     f'on {booking.booking_date} has been REJECTED. '
                     f'Reason: {booking.admin_notes}',
        type       = 'danger',
        booking_id = booking.id,
    ))
    db.session.commit()
    flash(f'Booking "{booking.title}" rejected.', 'info')
    return redirect(url_for('admin.manage_requests'))


@admin.route('/admin/users')
@login_required
@admin_required
def manage_users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/manage_users.html', users=all_users)


@admin.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.manage_users'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.full_name} {status}.', 'success')
    return redirect(url_for('admin.manage_users'))
