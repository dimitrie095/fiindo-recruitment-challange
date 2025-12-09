import requests

API_BASE = "https://api.test.fiindo.com/api/v1/financials"

def fetch_financial_data(symbol, statement_type):
    """
    Lädt die Financial Statement Daten (income_statement, cash_flow_statement, balance_sheet).
    """
    url = f"{API_BASE}/{symbol}/{statement_type}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('fundamentals', {}).get('financials', {}).get(statement_type, {}).get('data', [])
    else:
        return []

def calculate_revenue_growth(rev_q1, rev_q2):
    if rev_q1 is None or rev_q2 is None or rev_q1 == 0:
        return None
    return (rev_q2 - rev_q1) / rev_q1

def get_revenue_quarters(income_statements):
    """
    Findet Q1 und Q2 Umsätze für Berechnung des Revenue Growth.
    Wenn Q1 fehlt, versucht Q4 vom Vorjahr als Q1 zu verwenden.
    """
    sorted_statements = sorted(income_statements, key=lambda x: x['date'])
    
    # Suche Q1 und Q2 nach Datum
    rev_q1 = None
    rev_q2 = None
    for i, entry in enumerate(sorted_statements):
        period = entry.get("period")
        revenue = entry.get("revenue")
        date = entry.get("date")
        
        if period == "Q1":
            rev_q1 = revenue
            # Versuche direkt danach Q2 im gleichen Jahr zu finden
            for next_entry in sorted_statements[i+1:]:
                if next_entry.get("period") == "Q2" and next_entry.get("date")[:4] == date[:4]:
                    rev_q2 = next_entry.get("revenue")
                    break
            if rev_q2 is not None:
                break
    
    # Falls Q1 nicht gefunden, versuche Q2 und Q4 des Vorjahres
    if rev_q1 is None or rev_q2 is None:
        rev_q1 = None
        rev_q2 = None
        for entry in sorted_statements:
            if entry.get("period") == "Q2":
                rev_q2 = entry.get("revenue")
                year_q2 = entry.get("date")[:4]
                # Suche Q4 vom Vorjahr
                for e in sorted_statements:
                    if e.get("period") == "Q4" and e.get("date")[:4] == str(int(year_q2)-1):
                        rev_q1 = e.get("revenue")
                        break
                break

    return rev_q1, rev_q2

def get_net_income_ttm(income_statements):
    # Suche den letzten FY Eintrag und nehme netIncome daraus
    fy_entries = [e for e in income_statements if e.get("period") == "FY" and e.get("netIncome") is not None]
    if not fy_entries:
        return None
    latest_fy = max(fy_entries, key=lambda x: x['date'])
    return latest_fy.get("netIncome")

def get_debt_ratio(balance_sheets):
    # Nimmt den letzten FY Eintrag
    fy_entries = [e for e in balance_sheets if e.get("period") == "FY"]
    if not fy_entries:
        return None
    
    latest_fy = max(fy_entries, key=lambda x: x['date'])
    total_debt = latest_fy.get("totalDebt") or latest_fy.get("longTermDebt") or None
    total_equity = latest_fy.get("totalEquity") or None
    
    if total_debt is None or total_equity is None or total_equity == 0:
        return None
    
    return total_debt / total_equity

def process_tickers(tickers):
    results = {}
    
    for symbol in tickers:
        income_statements = fetch_financial_data(symbol, "income_statement")
        balance_sheets = fetch_financial_data(symbol, "balance_sheet")
        
        # Revenue Growth (Q1 vs Q2)
        rev_q1, rev_q2 = get_revenue_quarters(income_statements)
        revenue_growth = calculate_revenue_growth(rev_q1, rev_q2)
        
        # Net Income TTM
        net_income_ttm = get_net_income_ttm(income_statements)
        
        # Debt Ratio
        debt_ratio = get_debt_ratio(balance_sheets)
        
        results[symbol] = {
            "RevenueGrowthQoQ": revenue_growth,
            "NetIncomeTTM": net_income_ttm,
            "DebtRatio": debt_ratio,
        }
        
    return results

# Beispielaufruf
if __name__ == "__main__":
    tickers = ["THS.L", "HEX.L"]
    data = process_tickers(tickers)
    for sym, metrics in data.items():
        print(f"{sym}: {metrics}")
