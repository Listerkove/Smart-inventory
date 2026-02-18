def test_generate_suggestions_manager(client, auth_headers_manager, sample_product):
    # First, create some sales to have history
    for i in range(5):
        client.post("/sales", headers=auth_headers_manager, json={
            "transaction_number": f"SALE{i}",
            "transaction_date": "2026-02-14T10:00:00",
            "items": [{"sku": sample_product, "quantity": 1, "unit_price": 75.00}]
        })
    response = client.post("/replenishment/generate?lookback_days=30&forecast_days=7&safety_stock_factor=1.5",
                           headers=auth_headers_manager)
    assert response.status_code == 201
    assert "message" in response.json()

def test_get_suggestions_manager(client, auth_headers_manager, sample_product):
    # First generate
    client.post("/replenishment/generate", headers=auth_headers_manager)
    response = client.get("/replenishment/suggestions", headers=auth_headers_manager)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_accept_suggestion(client, auth_headers_manager, sample_product):
    # Generate and get first suggestion ID
    client.post("/replenishment/generate", headers=auth_headers_manager)
    suggestions = client.get("/replenishment/suggestions", headers=auth_headers_manager).json()
    if suggestions:
        sug_id = suggestions[0]["id"]
        response = client.post("/replenishment/actions", headers=auth_headers_manager, json={
            "suggestion_id": sug_id,
            "action": "accept"
        })
        assert response.status_code == 200