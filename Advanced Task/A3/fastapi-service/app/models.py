from sqlalchemy import Column, Float, Integer, String

from .database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    country = Column(String, nullable=False)
    merchant_category = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    score = Column(Integer, nullable=True)
    risk_level = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    created_at = Column(String, nullable=True)
