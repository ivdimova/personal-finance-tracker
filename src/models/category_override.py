from src.models.user import db
from datetime import datetime


class CategoryOverride(db.Model):
    """Stores user category preferences for transaction descriptions.

    When a user manually changes a transaction's category, the mapping
    from description to the chosen category is stored here. Future
    transactions with matching descriptions will use this override
    instead of auto-categorization.
    """

    __tablename__ = "category_override"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False, unique=True)
    category = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        """Convert to dictionary representation.

        Returns:
            dict: Dictionary with all model fields.
        """
        return {
            "id": self.id,
            "description": self.description,
            "category": self.category,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        }
