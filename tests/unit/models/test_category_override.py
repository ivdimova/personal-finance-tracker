"""Tests for the CategoryOverride model."""
import pytest
from sqlalchemy.exc import IntegrityError
from src.models.category_override import CategoryOverride


class TestCategoryOverrideModel:
    """Test suite for CategoryOverride model."""

    @pytest.mark.unit
    def test_create_override(self, db_session):
        """Test creating a category override record."""
        override = CategoryOverride(
            description="Test Merchant", category="Food & Dining"
        )
        db_session.add(override)
        db_session.commit()

        assert override.id is not None
        assert override.description == "Test Merchant"
        assert override.category == "Food & Dining"
        assert override.created_at is not None

    @pytest.mark.unit
    def test_to_dict(self, db_session):
        """Test to_dict returns correct structure."""
        override = CategoryOverride(
            description="Test Merchant", category="Other"
        )
        db_session.add(override)
        db_session.commit()

        result = override.to_dict()
        assert result["id"] == override.id
        assert result["description"] == "Test Merchant"
        assert result["category"] == "Other"
        assert "created_at" in result
        assert "updated_at" in result

    @pytest.mark.unit
    def test_unique_description_constraint(self, db_session):
        """Test that duplicate descriptions are rejected."""
        override1 = CategoryOverride(
            description="Same Description", category="Food & Dining"
        )
        db_session.add(override1)
        db_session.commit()

        override2 = CategoryOverride(
            description="Same Description", category="Transportation"
        )
        db_session.add(override2)
        with pytest.raises(IntegrityError):
            db_session.commit()
