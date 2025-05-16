from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required
from models import StorageBin, InventoryItem, db
import csv
import io

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # or whatever number you want per page
    pagination = StorageBin.query.paginate(page=page, per_page=per_page)
    bins = pagination.items
    return render_template('index.html', bins=bins, pagination=pagination)

@main_bp.route('/export_sheets')
@login_required
def export_sheets():
    # Call your export_to_google_sheets function from app.py
    from app import export_to_google_sheets
    export_to_google_sheets()
    return redirect(url_for('main.index'))

@main_bp.route('/export_csv')
@login_required
def export_csv():
    # Export all bins/items as CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Bin Name', 'Location', 'Notes', 'Item Name', 'Quantity'])
    bins = StorageBin.query.all()
    for bin in bins:
        for item in bin.items:
            writer.writerow([bin.name, bin.location, bin.notes, item.name, item.quantity])
        if not bin.items:
            writer.writerow([bin.name, bin.location, bin.notes, '', ''])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='inventory.csv'
    )

@main_bp.route('/import_csv', methods=['GET', 'POST'])
@login_required
def import_csv():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file:
            flash("No file selected.", "error")
            return redirect(request.url)
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        for row in reader:
            # Add or update bins/items as needed
            bin = StorageBin.query.filter_by(name=row['Bin Name'], location=row['Location']).first()
            if not bin:
                bin = StorageBin(name=row['Bin Name'], location=row['Location'], notes=row['Notes'])
                db.session.add(bin)
                db.session.commit()
            if row['Item Name']:
                item = InventoryItem.query.filter_by(name=row['Item Name'], bin_id=bin.id).first()
                if not item:
                    item = InventoryItem(name=row['Item Name'], quantity=row['Quantity'], bin_id=bin.id)
                    db.session.add(item)
        db.session.commit()
        flash("CSV imported successfully!", "success")
        return redirect(url_for('main.index'))
    return render_template('import_csv.html')