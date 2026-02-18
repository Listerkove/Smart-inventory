def test_create_sale_clerk(client, auth_headers_clerk, sample_product):
    response = client.post("/sales", headers=auth_headers_clerk, json={
        "transaction_number": "SALE001",
        "transaction_date": "2026-02-14T10:00:00",
        "items": [
            {"sku": sample_product, "quantity": 2, "unit_price": 75.00}
        ]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["transaction_number"] == "SALE001"
    # Compare as float or string
    assert float(data["total_amount"]) == 150.00

def test_create_sale_insufficient_stock(client, auth_headers_clerk, sample_product):
    # Try to sell 200 units (only 100 in stock)
    response = client.post("/sales", headers=auth_headers_clerk, json={
        "transaction_number": "SALE002",
        "transaction_date": "2026-02-14T10:00:00",
        "items": [
            {"sku": sample_product, "quantity": 200, "unit_price": 75.00}
        ]
    })
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]