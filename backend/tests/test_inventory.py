def test_receive_stock_manager(client, auth_headers_manager, sample_product):
    response = client.post("/inventory/receipt", headers=auth_headers_manager, json={
        "product_sku": sample_product,
        "quantity": 50,
        "reference_id": "PO-123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["new_quantity"] == 150  # 100 + 50

def test_receive_stock_clerk_forbidden(client, auth_headers_clerk, sample_product):
    response = client.post("/inventory/receipt", headers=auth_headers_clerk, json={
        "product_sku": sample_product,
        "quantity": 10
    })
    assert response.status_code == 403

def test_adjust_stock_manager(client, auth_headers_manager, sample_product):
    response = client.post("/inventory/adjust", headers=auth_headers_manager, json={
        "product_sku": sample_product,
        "movement_type": "damage",
        "quantity": 5,
        "reason": "Broken"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["new_quantity"] == 95

def test_get_movements(client, auth_headers_manager, auth_headers_clerk, sample_product):
    # First create a movement using manager
    client.post("/inventory/receipt", headers=auth_headers_manager, json={
        "product_sku": sample_product, "quantity": 20
    })
    # Then get movements as clerk
    response = client.get("/inventory/movements", headers=auth_headers_clerk)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1