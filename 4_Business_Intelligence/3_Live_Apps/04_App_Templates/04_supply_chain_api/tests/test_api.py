"""API endpoint tests"""
import pytest
import json
from app import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_ping(client):
    """Test ping endpoint"""
    response = client.get('/ping')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert data['message'] == 'pong'

def test_metrics(client):
    """Test metrics endpoint"""
    response = client.get('/metrics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'requests' in data

def test_auth_required(client):
    """Test authentication required"""
    response = client.get('/api/v2/inventory/status')
    assert response.status_code == 401

def test_invalid_token(client):
    """Test invalid token"""
    response = client.get(
        '/api/v2/inventory/status',
        headers={'X-API-Token': 'invalid-token'}
    )
    assert response.status_code == 403

def test_inventory_sync_valid(client):
    """Test inventory sync with valid data"""
    response = client.post(
        '/api/v2/inventory/sync',
        headers={'X-API-Token': 'demo-token-123'},
        json={
            'warehouse_id': 'WH001',
            'items': [
                {'product_id': 'P001', 'quantity': 100},
                {'product_id': 'P002', 'quantity': 50}
            ]
        }
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['items_synced'] == 2

def test_inventory_sync_missing_fields(client):
    """Test inventory sync with missing fields"""
    response = client.post(
        '/api/v2/inventory/sync',
        headers={'X-API-Token': 'demo-token-123'},
        json={'warehouse_id': 'WH001'}
    )
    assert response.status_code == 400

def test_create_po_valid(client):
    """Test create purchase order"""
    response = client.post(
        '/api/v2/purchase-orders/create',
        headers={'X-API-Token': 'demo-token-123'},
        json={
            'supplier_id': 'SUP001',
            'items': [
                {'product_id': 'P001', 'quantity': 100, 'unit_price': 50.00}
            ]
        }
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'created'
    assert 'purchase_order' in data
