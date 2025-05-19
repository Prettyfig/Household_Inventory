import logging
import tracemalloc
from logging.handlers import RotatingFileHandler
# Start tracemalloc for memory tracking
tracemalloc.start()

# Set up logging to file and console
handler = RotatingFileHandler('app_debug.log', maxBytes=10000, backupCount=1)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[handler, logging.StreamHandler()]
)

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, Response
from models import db, StorageBin, InventoryItem
import qrcode
import os
import shutil
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_socketio import SocketIO, emit
import socket
from PIL import Image
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import csv
from io import StringIO
from routes.main import main_bp
from routes.auth import auth_bp
from routes.bin import bin_bp
from routes.item import item_bp
from user_model import User
from utils import get_local_ip
from routes.main import main_bp
from dotenv import load_dotenv

load_dotenv()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'changeme')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///inventory.db')
app.config['UPLOAD_FOLDER'] = 'static/qrcodes'
db.init_app(app)

login_manager.init_app(app)
socketio = SocketIO(app)

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def export_to_google_sheets():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open('Household Inventory').sheet1
        sheet.clear()
        sheet.append_row(['Bin Name', 'Location', 'Notes', 'Item Name', 'Quantity'])
        bins = StorageBin.query.all()
        for bin in bins:
            for item in bin.items:
                sheet.append_row([bin.name, bin.location, bin.notes, item.name, item.quantity])
            if not bin.items:
                sheet.append_row([bin.name, bin.location, bin.notes, '', ''])
        flash("Exported to Google Sheets successfully!", "success")
        logging.info("Exported to Google Sheets successfully!")
    except Exception as e:
        flash("Failed to export, Please try again.", "error")
        logging.error(f"Export error: {e}")
        print("Export error:", e)

with app.app_context():
    db.create_all()

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(bin_bp)
app.register_blueprint(item_bp)

# Periodically log memory usage
import threading
import time

def log_memory_usage():
    while True:
        current, peak = tracemalloc.get_traced_memory()
        logging.info(f"Current memory usage: {current / 1024 / 1024:.2f} MB; Peak: {peak / 1024 / 1024:.2f} MB")
        time.sleep(60)  # Log every 60 seconds

memory_thread = threading.Thread(target=log_memory_usage, daemon=True)
memory_thread.start()

if __name__ == '__main__':
    logging.info("Starting Household Inventory app...")
    socketio.run(app, debug=True, host='0.0.0.0')