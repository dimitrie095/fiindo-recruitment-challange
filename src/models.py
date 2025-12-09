from sqlalchemy import Column, String, Integer, Float, Date, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    company_name = Column(String)
    industry = Column(String)
    country = Column(String)

    pe_ratio = Column(Float)
    revenue_growth = Column(Float)
    net_income_ttm = Column(Float)
    debt_ratio = Column(Float)

class IndustryAggregate(Base):
    __tablename__ = "industry_aggregates"

    id = Column(Integer, primary_key=True)
    industry = Column(String, unique=True, nullable=False)

    avg_pe_ratio = Column(Float)
    avg_revenue_growth = Column(Float)
    sum_revenue = Column(Float)
