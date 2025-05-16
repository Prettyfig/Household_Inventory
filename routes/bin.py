from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from models import db, StorageBin
import qrcode
import os
from utils import get_local_ip

bin_bp = Blueprint('bin', __name__)

@bin_bp.route('/bin/add', methods=['POST'])
@login_required
def add_bin():
    name = request.form['name']
    location = request.form['location']
    notes = request.form['notes']
    new_bin = StorageBin(name=name, location=location, notes=notes)
    db.session.add(new_bin)
    db.session.commit()

    # Generate QR code with local IP URL after bin has an ID
    local_ip = get_local_ip()
    url = f"http://{local_ip}:5000/bin/{new_bin.id}"
    qr_filename = f'bin_{new_bin.id}.png'
    qr_path = os.path.join(current_app.root_path, 'static', 'qrcodes', qr_filename)
    img = qrcode.make(url)
    img.save(qr_path)

    # Save filename to bin
    new_bin.qr_code_filename = qr_filename
    db.session.commit()

    flash('Bin added!', 'success')
    return redirect(url_for('main.index'))

@bin_bp.route('/bin/<int:bin_id>')
@login_required
def bin_detail(bin_id):
    bin = StorageBin.query.get_or_404(bin_id)
    page = request.args.get('page', 1, type=int)
    per_page = 10  # or whatever you want
    items_pagination = bin.items.paginate(page=page, per_page=per_page)
    items = items_pagination.items
    # If you need to show all bins for the move dropdown:
    bins = StorageBin.query.all()
    return render_template(
        'bin_detail.html',
        bin=bin,
        items=items,
        items_pagination=items_pagination,
        bins=bins
    )

@bin_bp.route('/bin/<int:bin_id>/delete', methods=['POST'])
@login_required
def delete_bin(bin_id):
    bin = StorageBin.query.get_or_404(bin_id)
    db.session.delete(bin)
    db.session.commit()
    flash("Bin deleted.", "success")
    return redirect(url_for('main.index'))

@bin_bp.route('/bin/<int:bin_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bin(bin_id):
    bin = StorageBin.query.get_or_404(bin_id)
    if request.method == 'POST':
        bin.name = request.form['name']
        bin.location = request.form['location']
        bin.notes = request.form['notes']
        db.session.commit()
        flash("Bin updated successfully!", "success")
        return redirect(url_for('bin.bin_detail', bin_id=bin.id))
    return render_template('edit_bin.html', bin=bin)

@bin_bp.route('/bins/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    bin_ids = request.form.getlist('bin_ids')
    action = request.form.get('action')
    if action == 'delete':
        for bin_id in bin_ids:
            bin = StorageBin.query.get(bin_id)
            if bin:
                db.session.delete(bin)
        db.session.commit()
        flash(f"Deleted {len(bin_ids)} bins.", "success")
    elif action == 'move':
        new_location = request.form.get('new_location')
        for bin_id in bin_ids:
            bin = StorageBin.query.get(bin_id)
            if bin and new_location:
                bin.location = new_location
        db.session.commit()
        flash(f"Moved {len(bin_ids)} bins.", "success")
    return redirect(url_for('main.index'))