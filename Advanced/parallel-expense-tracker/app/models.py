from sqlalchemy import CheckConstraint, Column, Index, Integer, String

from app.database import Base


class Expense(Base):
    """ORM mapping for the ``expenses`` table.

    Mirrors db/schema.sql exactly so ORM queries and the migration-applied
    schema cannot drift. Money is stored as an INTEGER number of cents
    (``amount_cents``) — never a float — so storage and SUM() aggregation are
    exact. The ``amount`` property exposes the value as a 2-decimal number for
    the API/response layer.
    """

    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount_cents = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    note = Column(String, nullable=False, default="")
    created_at = Column(String, nullable=False)

    # These mirror the migration DDL. The migration (not create_all) is what
    # runs at runtime, but declaring them here keeps the ORM honest and lets
    # create_all reproduce the same guards if ever used directly.
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_expenses_amount_positive"),
        CheckConstraint("length(category) > 0", name="ck_expenses_category_nonempty"),
        Index("idx_expenses_category", "category"),
        Index("idx_expenses_created_at", "created_at"),
    )

    @property
    def amount(self) -> float:
        """Wire representation: cents -> a 2-decimal number (e.g. 1250 -> 12.5)."""
        return self.amount_cents / 100
