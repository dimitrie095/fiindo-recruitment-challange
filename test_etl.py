import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base, Ticker
from database import upsert_ticker

# Setup in-memory SQLite DB für Tests
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)  # Tabellen erstellen
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

def test_upsert_ticker(db_session):
    ticker = Ticker(
        symbol="TEST.L",
        company_name="Test Company",
        industry="Technology",
        country="US",
        pe_ratio=15.5,
        revenue_growth=0.1,
        net_income_ttm=1000000,
        debt_ratio=0.2
    )
    upsert_ticker(db_session, ticker)

    result = db_session.query(Ticker).filter_by(symbol="TEST.L").first()
    assert result is not None
    assert result.company_name == "Test Company"
