"""Tests for the transaction management routes (category editing)."""
import pytest
from src.models.category_override import CategoryOverride
from src.models.transaction import Transaction


class TestUpdateTransactionCategory:
    """Test the PUT /api/transactions/<id>/category endpoint."""

    @pytest.mark.unit
    def test_update_category_success(
        self, client, sample_transactions, sample_categories
    ):
        """Test successfully updating a transaction's category."""
        txn = sample_transactions[0]  # Restaurant ABC, Food & Dining
        response = client.put(
            f"/api/transactions/{txn.id}/category",
            json={"category": "Transportation"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["transaction"]["category"] == "Transportation"
        assert data["override_saved"] is True

    @pytest.mark.unit
    def test_update_category_creates_override(
        self, client, db_session, sample_transactions, sample_categories
    ):
        """Test that updating category creates a CategoryOverride."""
        txn = sample_transactions[0]
        client.put(
            f"/api/transactions/{txn.id}/category",
            json={"category": "Transportation"},
        )
        override = CategoryOverride.query.filter_by(
            description=txn.description
        ).first()
        assert override is not None
        assert override.category == "Transportation"

    @pytest.mark.unit
    def test_update_category_without_remember(
        self, client, db_session, sample_transactions, sample_categories
    ):
        """Test updating category with remember=false skips override."""
        txn = sample_transactions[0]
        client.put(
            f"/api/transactions/{txn.id}/category",
            json={"category": "Transportation", "remember": False},
        )
        override = CategoryOverride.query.filter_by(
            description=txn.description
        ).first()
        assert override is None

    @pytest.mark.unit
    def test_update_category_not_found(self, client, sample_categories):
        """Test updating a non-existent transaction returns 404."""
        response = client.put(
            "/api/transactions/99999/category",
            json={"category": "Transportation"},
        )
        assert response.status_code == 404

    @pytest.mark.unit
    def test_update_category_invalid_category(
        self, client, sample_transactions, sample_categories
    ):
        """Test updating with a non-existent category returns 400."""
        txn = sample_transactions[0]
        response = client.put(
            f"/api/transactions/{txn.id}/category",
            json={"category": "NonExistentCategory"},
        )
        assert response.status_code == 400
        assert "does not exist" in response.get_json()["error"]

    @pytest.mark.unit
    def test_update_category_missing_body(
        self, client, sample_transactions, sample_categories
    ):
        """Test updating with no category in body returns 400."""
        txn = sample_transactions[0]
        response = client.put(
            f"/api/transactions/{txn.id}/category",
            json={},
        )
        assert response.status_code == 400


class TestBulkRecategorize:
    """Test the POST /api/transactions/bulk-recategorize endpoint."""

    @pytest.mark.unit
    def test_bulk_recategorize_success(
        self, client, db_session, sample_transactions, sample_categories
    ):
        """Test bulk recategorizing matching transactions."""
        response = client.post(
            "/api/transactions/bulk-recategorize",
            json={
                "description": "Restaurant ABC",
                "category": "Transportation",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["updated_count"] == 1
        assert data["total_matching"] == 1

    @pytest.mark.unit
    def test_bulk_recategorize_creates_override(
        self, client, db_session, sample_transactions, sample_categories
    ):
        """Test that bulk recategorize saves a CategoryOverride."""
        client.post(
            "/api/transactions/bulk-recategorize",
            json={
                "description": "Restaurant ABC",
                "category": "Transportation",
            },
        )
        override = CategoryOverride.query.filter_by(
            description="Restaurant ABC"
        ).first()
        assert override is not None
        assert override.category == "Transportation"

    @pytest.mark.unit
    def test_bulk_recategorize_missing_fields(self, client):
        """Test bulk recategorize with missing fields returns 400."""
        response = client.post(
            "/api/transactions/bulk-recategorize",
            json={"description": "Test"},
        )
        assert response.status_code == 400


class TestDeleteTransaction:
    """Test the DELETE /api/transactions/<id> endpoint."""

    @pytest.mark.unit
    def test_delete_transaction_success(
        self, client, db_session, sample_transactions
    ):
        """Test successfully deleting a transaction."""
        txn = sample_transactions[0]
        txn_id = txn.id
        response = client.delete(f"/api/transactions/{txn_id}")
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        assert Transaction.query.get(txn_id) is None

    @pytest.mark.unit
    def test_delete_transaction_not_found(self, client):
        """Test deleting a non-existent transaction returns 404."""
        response = client.delete("/api/transactions/99999")
        assert response.status_code == 404
        assert "error" in response.get_json()

    @pytest.mark.unit
    def test_delete_transaction_removes_only_target(
        self, client, db_session, sample_transactions
    ):
        """Test that deleting one transaction does not affect others."""
        txn_to_delete = sample_transactions[0]
        remaining = sample_transactions[1:]
        client.delete(f"/api/transactions/{txn_to_delete.id}")
        for txn in remaining:
            assert Transaction.query.get(txn.id) is not None
