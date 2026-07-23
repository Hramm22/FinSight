from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, Text

from app.db.database import Base


class Briefing(Base):
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)

    market_data = Column(Text, nullable=False)
    news_data = Column(Text, nullable=False)

    macro_analysis = Column(Text, nullable=False)
    sector_analysis = Column(Text, nullable=False)
    interest_analysis = Column(Text, nullable=False)
    ai_summary = Column(Text, nullable=False)