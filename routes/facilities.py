from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Facility
from functools import wraps

facilities = Blueprint('facilities', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


@facilities.route('/facilities')
@login_required
def list_facilities():
    type_filter = request.args.get('type', 'all')
    query = Facility.query
    if type_filter != 'all':
        query = query.filter_by(facility_type=type_filter)
    all_facilities = query.order_by(Facility.name).all()
    return render_template('facilities/list.html',
        facilities=all_facilities, type_filter=type_filter)


@facilities.route('/admin/facilities/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_facility():
    if request.method == 'POST':
        name          = request.form.get('name', '').strip()
        facility_type = request.form.get('facility_type', '').strip()
        location      = request.form.get('location', '').strip()
        capacity      = request.form.get('capacity', 0)
        description   = request.form.get('description', '').strip()
        equipment     = request.form.get('equipment', '').strip()

        if not all([name, facility_type, location, capacity]):
            flash('Name, type, location and capacity are required.', 'danger')
            return render_template('admin/facility_form.html', facility=None)

        f = Facility(name=name, facility_type=facility_type,
                     location=location, capacity=int(capacity),
                     description=description, equipment=equipment)
        db.session.add(f)
        db.session.commit()
        flash(f'Facility "{name}" added.', 'success')
        return redirect(url_for('facilities.list_facilities'))

    return render_template('admin/facility_form.html', facility=None)


@facilities.route('/admin/facilities/<int:facility_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_facility(facility_id):
    facility = Facility.query.get_or_404(facility_id)

    if request.method == 'POST':
        facility.name          = request.form.get('name', '').strip()
        facility.facility_type = request.form.get('facility_type', '').strip()
        facility.location      = request.form.get('location', '').strip()
        facility.capacity      = int(request.form.get('capacity', facility.capacity))
        facility.description   = request.form.get('description', '').strip()
        facility.equipment     = request.form.get('equipment', '').strip()
        facility.is_available  = request.form.get('is_available') == 'on'
        db.session.commit()
        flash(f'Facility "{facility.name}" updated.', 'success')
        return redirect(url_for('facilities.list_facilities'))

    return render_template('admin/facility_form.html', facility=facility)


@facilities.route('/admin/facilities/<int:facility_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_facility(facility_id):
    facility = Facility.query.get_or_404(facility_id)
    db.session.delete(facility)
    db.session.commit()
    flash(f'Facility "{facility.name}" deleted.', 'info')
    return redirect(url_for('facilities.list_facilities'))
