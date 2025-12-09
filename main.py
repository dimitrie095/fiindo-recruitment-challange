from fiindo_api import (
    get_symbols,
    get_general_info,
    get_income_statement, 
    get_revenue_quarters, 
    get_net_income_ttm, 
    get_financials, 
    get_debt_ratio 
    )

from database import init_db, SessionLocal, upsert_ticker
from src.models import Ticker, IndustryAggregate
from config import INDUSTRIES_OF_INTEREST
from calculations import calculate_pe_ratio, calculate_revenue_growth, calculate_debt_ratio

def process_tickers():
    init_db()
    session = SessionLocal()
    symbols = get_symbols()
    print(f"Loaded {len(symbols)} symbols")

    industry_stats = {}

    for symbol in symbols:
        try:
            print(f"---check symbol: {symbol} ---")
            data = get_general_info(symbol)
            profile = data.get("fundamentals", {}).get("profile", {}).get("data", [{}])[0]

            industry = profile.get("industry")
            if industry not in INDUSTRIES_OF_INTEREST:
                print(f"check result: false")
                continue
            print(f"check result: true")

            price = profile.get("price")
            income_statement_data = get_income_statement(symbol)
            latest_quarter = None
            for record in income_statement_data.get("fundamentals", {}).get("financials", {}).get("income_statement", {}).get("data", []):
                if record.get("period") in ["Q1", "Q2", "Q3", "Q4"]:
                    latest_quarter = record
                    break  # oder suche nach dem neuesten Datum
            
            eps = latest_quarter.get("eps") if latest_quarter else None
            pe_ratio = calculate_pe_ratio(price, eps)
            print(f"{symbol} PE Ratio: {pe_ratio}")

            revenue_q1, revenue_q2 = get_revenue_quarters(income_statement_data)
            
            revenue_growth = calculate_revenue_growth(revenue_q1, revenue_q2)
            print(revenue_growth)
            print(f"{symbol} Revenue Growth: {revenue_growth}")

            net_income_ttm = get_net_income_ttm(income_statement_data)
            print(f"{symbol} Net Income TTM: {net_income_ttm}")

            debt_ratio = get_debt_ratio(symbol)
            print(f"{symbol} Debt Ratio: {debt_ratio}")


            ticker = Ticker(
                symbol=symbol,
                company_name=profile.get("companyName"),
                industry=industry,
                country=profile.get("country"),
                pe_ratio=pe_ratio,
                revenue_growth=revenue_growth,
                net_income_ttm=net_income_ttm,
                debt_ratio=debt_ratio
            )
            upsert_ticker(session, ticker)
            

            if industry not in industry_stats:
                industry_stats[industry] = {
                    "pe_ratios": [],
                    "revenue_growths": [],
                    "revenues": []
                }

            if pe_ratio is not None:
                industry_stats[industry]["pe_ratios"].append(pe_ratio)

            if revenue_growth is not None:
                industry_stats[industry]["revenue_growths"].append(revenue_growth)

            if revenue_q1 is not None:
                industry_stats[industry]["revenues"].append(revenue_q1)
            
            print(industry_stats)

        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    for industry, stats in industry_stats.items():
        avg_pe = (sum(stats["pe_ratios"]) / len(stats["pe_ratios"])) if stats["pe_ratios"] else None
        avg_rev_growth = (sum(stats["revenue_growths"]) / len(stats["revenue_growths"])) if stats["revenue_growths"] else None
        sum_revenue = sum(stats["revenues"]) if stats["revenues"] else None

        agg = IndustryAggregate(
            industry=industry,
            avg_pe_ratio=avg_pe,
            avg_revenue_growth=avg_rev_growth,
            sum_revenue=sum_revenue
        )
        session.merge(agg)

    session.commit()
    session.close()

if __name__ == "__main__":
    process_tickers()
