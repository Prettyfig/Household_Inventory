from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, InventoryItem
from werkzeug.utils import secure_filename
from PIL import Image
import os

item_bp = Blueprint('item', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@item_bp.route('/bin/<int:bin_id>/add_item', methods=['POST'])
@login_required
def add_item(bin_id):
    name = request.form['name']
    quantity = int(request.form['quantity'])
    notes = request.form.get('notes', '')
    photo = request.files.get('photo')
    photo_filename = None
    if photo and allowed_file(photo.filename):
        filename = secure_filename(photo.filename)
        photo_filename = f'item_{bin_id}_{filename}'
        photo_path = os.path.join('static/item_photos', photo_filename)
        img = Image.open(photo)
        img.thumbnail((400, 400))
        img.save(photo_path)
    elif photo and photo.filename:
        flash("Invalid file type. Only PNG and JPEG are allowed.", "danger")
        return redirect(url_for('bin.bin_detail', bin_id=bin_id))
    item = InventoryItem(name=name, quantity=quantity, notes=notes, photo_filename=photo_filename, bin_id=bin_id)
    db.session.add(item)
    db.session.commit()
    flash("Item added successfully!", "success")
    return redirect(url_for('bin.bin_detail', bin_id=bin_id))

@item_bp.route('/item/<int:item_id>/move', methods=['POST'])
@login_required
def move_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    new_bin_id = int(request.form['new_bin_id'])
    item.bin_id = new_bin_id
    db.session.commit()
    flash("Item moved.", "success")
    return redirect(url_for('bin.bin_detail', bin_id=new_bin_id))

@item_bp.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    bin_id = item.bin_id
    db.session.delete(item)
    db.session.commit()
    flash("Item deleted.", "success")
    return redirect(url_for('bin.bin_detail', bin_id=bin_id))

@item_bp.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    if request.method == 'POST':
        item.name = request.form['name']
        item.quantity = int(request.form['quantity'])
        item.notes = request.form['notes']
        db.session.commit()
        flash("Item updated successfully!", "success")
        return redirect(url_for('bin.bin_detail', bin_id=item.bin_id))
    return render_template('edit_item.html', item=item)

@item_bp.route('/items/bulk_action/<int:bin_id>', methods=['POST'])
@login_required
def bulk_action(bin_id):
    item_ids = request.form.getlist('item_ids')
    action = request.form.get('action')
    if action == 'delete':
        for item_id in item_ids:
            item = InventoryItem.query.get(item_id)
            if item:
                db.session.delete(item)
        db.session.commit()
        flash(f"Deleted {len(item_ids)} items.", "success")
    elif action == 'move':
        new_bin_id = request.form.get('new_bin_id')
        for item_id in item_ids:
            item = InventoryItem.query.get(item_id)
            if item and new_bin_id:
                item.bin_id = new_bin_id
        db.session.commit()
        flash(f"Moved {len(item_ids)} items.", "success")
    return redirect(url_for('bin.bin_detail', bin_id=bin_id))