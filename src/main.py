from src.fiindo_api import (
    get_symbols,
    get_general_info,
    get_income_statement, 
    get_revenue_quarters, 
    get_net_income_ttm, 
    get_financials, 
    get_debt_ratio 
)
from src.database import init_db, SessionLocal, upsert_ticker
from src.models import Ticker, IndustryAggregate
from src.config import INDUSTRIES_OF_INTEREST
from src.calculations import calculate_pe_ratio, calculate_revenue_growth, calculate_debt_ratio

def process_tickers():
    # Initialisiert die Datenbank (erzeugt Tabellen etc. falls nötig)
    init_db()
    # Erzeugt eine neue Session für DB-Operationen
    session = SessionLocal()
    # Holt alle Symbole (Ticker) von der API
    symbols = get_symbols()
    print(f"Loaded {len(symbols)} symbols")

    # Dictionary zum Sammeln von Statistiken pro Branche
    industry_stats = {}

    # Schleife über alle Symbole
    for symbol in symbols:
        try:
            print(f"---check symbol: {symbol} ---")
            # Holt allgemeine Informationen zum Ticker
            data = get_general_info(symbol)
            # Extrahiert das Profil aus der API-Antwort
            profile = data.get("fundamentals", {}).get("profile", {}).get("data", [{}])[0]

            # Holt die Branche des Unternehmens
            industry = profile.get("industry")
            # Filter: nur Branchen, die in INDUSTRIES_OF_INTEREST enthalten sind
            if industry not in INDUSTRIES_OF_INTEREST:
                print(f"check result: false")
                continue
            print(f"check result: true")

            # Holt den aktuellen Preis aus dem Profil
            price = profile.get("price")
            # Holt die Gewinn- und Verlustrechnung des Unternehmens
            income_statement_data = get_income_statement(symbol)
            
            # Sucht das aktuellste Quartal (Q1-Q4) aus den Income Statement Daten
            latest_quarter = None
            for record in income_statement_data.get("fundamentals", {}).get("financials", {}).get("income_statement", {}).get("data", []):
                if record.get("period") in ["Q1", "Q2", "Q3", "Q4"]:
                    latest_quarter = record
                    break  # hier könnte man alternativ das jüngste Datum finden
            
            # Holt EPS aus dem neuesten Quartal (earnings per share)
            eps = latest_quarter.get("eps") if latest_quarter else None
            # Berechnet das Kurs-Gewinn-Verhältnis (PE Ratio)
            pe_ratio = calculate_pe_ratio(price, eps)
            print(f"{symbol} PE Ratio: {pe_ratio}")

            # Holt Umsätze der letzten zwei Quartale
            revenue_q1, revenue_q2 = get_revenue_quarters(income_statement_data)
            
            # Berechnet das Umsatzwachstum zwischen den beiden Quartalen
            revenue_growth = calculate_revenue_growth(revenue_q1, revenue_q2)
            print(revenue_growth)
            print(f"{symbol} Revenue Growth: {revenue_growth}")

            # Holt den Nettogewinn der letzten 12 Monate (TTM)
            net_income_ttm = get_net_income_ttm(income_statement_data)
            print(f"{symbol} Net Income TTM: {net_income_ttm}")

            # Holt die Verschuldungsquote (Debt Ratio) des Unternehmens
            debt_ratio = get_debt_ratio(symbol)
            print(f"{symbol} Debt Ratio: {debt_ratio}")

            # Erzeugt ein Ticker-Objekt für die Datenbank
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
            # Fügt den Ticker in die Datenbank ein oder aktualisiert ihn, falls schon vorhanden
            upsert_ticker(session, ticker)

            # Falls die Branche noch nicht in industry_stats existiert, initialisiere sie
            if industry not in industry_stats:
                industry_stats[industry] = {
                    "pe_ratios": [],
                    "revenue_growths": [],
                    "revenues": []
                }

            # Werte sammeln, wenn vorhanden
            if pe_ratio is not None:
                industry_stats[industry]["pe_ratios"].append(pe_ratio)

            if revenue_growth is not None:
                industry_stats[industry]["revenue_growths"].append(revenue_growth)

            if revenue_q1 is not None:
                industry_stats[industry]["revenues"].append(revenue_q1)
            
            # Ausgabe der aktuellen Branchen-Statistiken für Debugging
            print(f"industry_stats: {industry_stats}")

        except Exception as e:
            # Fehlerbehandlung bei Problemen mit einzelnen Symbolen
            print(f"Error processing {symbol}: {e}")

    # Nach Abschluss der Schleife: Berechnung aggregierter Werte je Branche
    for industry, stats in industry_stats.items():
        avg_pe = (sum(stats["pe_ratios"]) / len(stats["pe_ratios"])) if stats["pe_ratios"] else None
        avg_rev_growth = (sum(stats["revenue_growths"]) / len(stats["revenue_growths"])) if stats["revenue_growths"] else None
        sum_revenue = sum(stats["revenues"]) if stats["revenues"] else None

        # Erzeugt ein IndustryAggregate-Objekt mit den aggregierten Daten
        agg = IndustryAggregate(
            industry=industry,
            avg_pe_ratio=avg_pe,
            avg_revenue_growth=avg_rev_growth,
            sum_revenue=sum_revenue
        )
        # Fügt das Aggregat in die Datenbank ein oder aktualisiert es
        session.merge(agg)

    # Speichert alle Änderungen in der Datenbank
    session.commit()
    # Schließt die Datenbank-Session
    session.close()

# Führt process_tickers nur aus, wenn dieses Skript direkt gestartet wird
if __name__ == "__main__":
    process_tickers()
