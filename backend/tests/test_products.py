def test_get_products(client, auth_headers_clerk, sample_product):
    response = client.get("/products", headers=auth_headers_clerk)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Check that the sample product is in the list
    skus = [p["sku"] for p in data]
    assert sample_product in skus

def test_create_product_manager(client, auth_headers_manager):
    response = client.post("/products", headers=auth_headers_manager, json={
        "sku": "NEW001",
        "barcode": "987654321",
        "name": "New Product",
        "cost_price": 20.00,
        "selling_price": 30.00,
        "quantity_in_stock": 50,
        "reorder_threshold": 5
    })
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "NEW001"
    assert data["name"] == "New Product"

def test_create_product_clerk_forbidden(client, auth_headers_clerk):
    response = client.post("/products", headers=auth_headers_clerk, json={
        "sku": "NEW002",
        "barcode": "111",
        "name": "Should Fail",
        "cost_price": 10,
        "selling_price": 15
    })
    assert response.status_code == 403

def test_update_product_manager(client, auth_headers_manager, sample_product):
    response = client.put(f"/products/{sample_product}", headers=auth_headers_manager, json={
        "name": "Updated Product"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Product"

def test_delete_product_manager(client, auth_headers_manager, sample_product):
    response = client.delete(f"/products/{sample_product}", headers=auth_headers_manager)
    assert response.status_code == 204
    # Verify it's soft-deleted – should still be returned but with is_active=False
    get_resp = client.get(f"/products/{sample_product}", headers=auth_headers_manager)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["is_active"] is False