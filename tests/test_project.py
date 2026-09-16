
from fastapi.testclient import TestClient

from api.app import app
from src.pricing_engine import (
    get_elasticity,
    optimize_price
)

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_known_product_elasticity():
    result = get_elasticity("HOBBIES_1_295")

    assert result is not None
    assert "elasticity" in result
    assert "classification" in result
    assert result["classification"] == "Inelastic"
    assert result["elasticity"] < 0


def test_unknown_product_elasticity():
    result = get_elasticity("PRODUCT_DOES_NOT_EXIST")

    assert result is None


def test_price_optimizer():
    elasticity_info = get_elasticity("HOBBIES_1_295")

    result = optimize_price(
        base_price=0.48,
        base_demand=9.202,
        elasticity=elasticity_info["elasticity"],
        candidate_prices=[0.42, 0.46, 0.48, 0.50]
    )

    assert "recommended_price" in result
    assert "forecast_demand" in result
    assert "expected_revenue" in result
    assert "scenarios" in result

    assert result["recommended_price"] == 0.50
    assert len(result["scenarios"]) == 4


def test_recommend_price_endpoint():
    payload = {
        "item_id": "HOBBIES_1_295",
        "base_price": 0.48,
        "base_demand": 9.202,
        "candidate_prices": [
            0.42,
            0.46,
            0.48,
            0.50
        ]
    }

    response = client.post(
        "/recommend-price",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "AUTO_RECOMMEND"
    assert data["classification"] == "Inelastic"
    assert data["recommended_price"] == 0.50


def test_unknown_product_endpoint():
    payload = {
        "item_id": "PRODUCT_DOES_NOT_EXIST",
        "base_price": 1.0,
        "base_demand": 10.0,
        "candidate_prices": [
            0.90,
            1.00,
            1.10
        ]
    }

    response = client.post(
        "/recommend-price",
        json=payload
    )

    assert response.status_code == 404



def test_auto_recommend_endpoint():

    response = client.get(
        "/recommend-auto/HOBBIES_1_295"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "AUTO_RECOMMEND"
    assert data["item_id"] == "HOBBIES_1_295"
    assert data["classification"] == "Inelastic"

    assert "forecast_demand" in data
    assert "candidate_prices" in data
    assert "recommended_price" in data
    assert "expected_revenue_uplift_pct" in data

    assert data["recommended_price"] == 0.52
    assert len(data["candidate_prices"]) == 5


def test_auto_recommend_guardrail_validation():

    response = client.get(
        "/recommend-auto/HOBBIES_1_295",
        params={
            "max_change_pct": 0.50
        }
    )

    assert response.status_code == 400



def test_profit_auto_endpoint():

    payload = {
        "item_id": "HOBBIES_1_295",
        "unit_cost": 0.30,
        "max_change_pct": 0.10
    }

    response = client.post(
        "/recommend-profit-auto",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "AUTO_RECOMMEND"
    assert data["item_id"] == "HOBBIES_1_295"
    assert data["unit_cost"] == 0.30

    assert "revenue_maximizing_price" in data
    assert "profit_maximizing_price" in data
    assert "expected_profit_at_profit_optimum" in data
    assert "expected_profit_uplift_pct" in data
    assert "scenarios" in data


def test_profit_auto_negative_cost():

    payload = {
        "item_id": "HOBBIES_1_295",
        "unit_cost": -0.10,
        "max_change_pct": 0.10
    }

    response = client.post(
        "/recommend-profit-auto",
        json=payload
    )

    assert response.status_code == 400


def test_profit_auto_excessive_price_change():

    payload = {
        "item_id": "HOBBIES_1_295",
        "unit_cost": 0.30,
        "max_change_pct": 0.50
    }

    response = client.post(
        "/recommend-profit-auto",
        json=payload
    )

    assert response.status_code == 400



def test_portfolio_opportunities_endpoint():

    response = client.get(
        "/portfolio-opportunities",
        params={
            "top_n": 5,
            "max_change_pct": 0.10
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "summary" in data
    assert "opportunities" in data

    assert len(data["opportunities"]) <= 5

    assert "opportunities" in data["summary"]
    assert "total_expected_revenue_gain" in data["summary"]
    assert "average_revenue_uplift_pct" in data["summary"]

    if data["opportunities"]:

        first = data["opportunities"][0]

        assert "rank" in first
        assert "item_id" in first
        assert "current_price" in first
        assert "recommended_price" in first
        assert "expected_revenue_gain" in first
        assert "expected_revenue_uplift_pct" in first


def test_portfolio_invalid_top_n():

    response = client.get(
        "/portfolio-opportunities",
        params={
            "top_n": 0,
            "max_change_pct": 0.10
        }
    )

    assert response.status_code == 400


def test_portfolio_invalid_guardrail():

    response = client.get(
        "/portfolio-opportunities",
        params={
            "top_n": 10,
            "max_change_pct": 0.50
        }
    )

    assert response.status_code == 400



def test_model_info_endpoint():

    response = client.get(
        "/model-info"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["model_type"] == "HistGradientBoostingRegressor"
    assert data["version"] == "1.0.0"

    assert "evaluation" in data
    assert "baseline" in data
    assert "features" in data
    assert "governance" in data
    assert "computed_metrics" in data

    assert len(data["features"]) == 8

    assert data["evaluation"]["mae"] > 0
    assert data["evaluation"]["rmse"] > 0

    assert (
        data["computed_metrics"]
        ["mae_improvement_vs_baseline_pct"]
        > 0
    )


def test_feature_importance_endpoint():

    response = client.get(
        "/feature-importance"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["method"] == "Permutation Importance"

    assert "features" in data
    assert len(data["features"]) == 8

    first = data["features"][0]

    assert "feature" in first
    assert "importance_mean" in first
    assert "importance_std" in first
    assert "rank" in first

    ranks = [
        feature["rank"]
        for feature in data["features"]
    ]

    assert sorted(ranks) == list(
        range(1, 9)
    )
