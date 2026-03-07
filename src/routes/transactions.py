from flask import Blueprint, jsonify, request, current_app
from src.models.transaction import Transaction, Category
from src.models.category_override import CategoryOverride
from src.models.user import db

transactions_bp = Blueprint("transactions", __name__)


def _create_or_update_override(description: str, category: str) -> None:
    """Create or update a category override for the given description.

    Args:
        description: The transaction description to override.
        category: The category to assign.
    """
    override = CategoryOverride.query.filter_by(
        description=description
    ).first()
    if override:
        override.category = category
    else:
        override = CategoryOverride(
            description=description, category=category
        )
        db.session.add(override)


@transactions_bp.route(
    "/transactions/<int:transaction_id>/category", methods=["PUT"]
)
def update_transaction_category(transaction_id: int):
    """Update a transaction's category and optionally remember the preference.

    Args:
        transaction_id: The ID of the transaction to update.

    Request body:
        {
            "category": "Supermarkets & Groceries",
            "remember": true  // optional, defaults to true
        }

    Returns:
        JSON with the updated transaction and override status.
    """
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404

    data = request.get_json()
    if not data or not data.get("category"):
        return jsonify({"error": "Category is required"}), 400

    new_category = data["category"].strip()
    remember = data.get("remember", True)

    # Validate that the category exists
    category_exists = Category.query.filter_by(name=new_category).first()
    if not category_exists:
        return jsonify(
            {"error": f'Category "{new_category}" does not exist'}
        ), 400

    old_category = transaction.category
    transaction.category = new_category

    if remember:
        _create_or_update_override(transaction.description, new_category)

    db.session.commit()

    current_app.logger.info(
        f"Transaction {transaction_id} category changed: "
        f"'{old_category}' -> '{new_category}' "
        f"(remember={remember})"
    )

    return jsonify({
        "success": True,
        "message": f"Category updated to '{new_category}'",
        "transaction": transaction.to_dict(),
        "override_saved": remember,
    })


@transactions_bp.route(
    "/transactions/bulk-recategorize", methods=["POST"]
)
def bulk_recategorize():
    """Re-apply a category to all transactions matching a description.

    Request body:
        {
            "description": "MERCADONA",
            "category": "Supermarkets & Groceries"
        }

    Returns:
        JSON with count of updated transactions.
    """
    data = request.get_json()
    if not data or not data.get("description") or not data.get("category"):
        return jsonify(
            {"error": "Both description and category are required"}
        ), 400

    description = data["description"].strip()
    new_category = data["category"].strip()

    # Validate category
    category_exists = Category.query.filter_by(name=new_category).first()
    if not category_exists:
        return jsonify(
            {"error": f'Category "{new_category}" does not exist'}
        ), 400

    # Update all matching transactions
    matching = Transaction.query.filter_by(description=description).all()
    updated_count = 0
    for txn in matching:
        if txn.category != new_category:
            txn.category = new_category
            updated_count += 1

    _create_or_update_override(description, new_category)
    db.session.commit()

    current_app.logger.info(
        f"Bulk recategorize: '{description}' -> '{new_category}' "
        f"({updated_count}/{len(matching)} updated)"
    )

    return jsonify({
        "success": True,
        "message": (
            f"Updated {updated_count} transactions to '{new_category}'"
        ),
        "updated_count": updated_count,
        "total_matching": len(matching),
    })
