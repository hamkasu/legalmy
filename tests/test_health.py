def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200

    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'db' in data
    assert 'redis' in data
    assert 'version' in data
