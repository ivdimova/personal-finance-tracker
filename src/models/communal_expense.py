from src.models.user import db
from datetime import datetime

class CommunalExpenseType(db.Model):
    """
    Model for storing user-defined communal expense types.
    
    Users can configure their own communal expenses like electricity, water, internet, etc.
    These are used to automatically categorize transactions.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Electricity", "Water", "Internet"
    keywords = db.Column(db.Text, nullable=True)  # JSON string of keywords for matching
    description = db.Column(db.String(255), nullable=True)  # Optional user description
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'keywords': self.keywords,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CommunalExpense(db.Model):
    """
    Model for storing actual communal expenses.
    
    This tracks monthly/recurring communal expenses and their amounts.
    """
    id = db.Column(db.Integer, primary_key=True)
    expense_type_id = db.Column(db.Integer, db.ForeignKey('communal_expense_type.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_recurring = db.Column(db.Boolean, default=True, nullable=False)  # Monthly recurring expense
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    expense_type = db.relationship('CommunalExpenseType', backref=db.backref('expenses', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'expense_type_id': self.expense_type_id,
            'expense_type_name': self.expense_type.name if self.expense_type else None,
            'amount': self.amount,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'is_recurring': self.is_recurring,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }