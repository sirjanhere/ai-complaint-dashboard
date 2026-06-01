from sqlalchemy import Column, Integer, String, Text

from .database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String, default="pending", nullable=False)
