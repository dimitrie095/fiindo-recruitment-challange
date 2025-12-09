from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base, Ticker
from config import DB_PATH

engine = create_engine(DB_PATH)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def upsert_ticker(session, ticker_obj):
    existing = session.query(Ticker).filter_by(symbol=ticker_obj.symbol).first()

    if existing:
        # update fields
        existing.company_name = ticker_obj.company_name
        existing.industry = ticker_obj.industry
        existing.country = ticker_obj.country
        existing.pe_ratio = ticker_obj.pe_ratio
        existing.revenue_growth = ticker_obj.revenue_growth
        existing.net_income_ttm = ticker_obj.net_income_ttm
        existing.debt_ratio = ticker_obj.debt_ratio
    else:
        session.add(ticker_obj)

    session.commit()

