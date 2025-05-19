import pytest
from app import app, db
from models import StorageBin

@pytest.fixture

def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200

def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_home_redirects_to_login(client):
    response = client.get('/')
    # Should redirect to login if not authenticated
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_add_bin(client):
    # Log in first
    client.post('/login', data={'username': 'admin', 'password': 'password'})
    # Add a bin
    response = client.post('/bin/add', data={
        'name': 'Test Bin',
        'location': 'Test Location',
        'notes': 'Test Notes'
    }, follow_redirects=True)
    assert b'Test Bin' in response.data