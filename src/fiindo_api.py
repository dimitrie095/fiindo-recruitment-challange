import requests
from src.config import API_BASE_URL, API_AUTH_TOKEN

headers = {
    "Authorization": API_AUTH_TOKEN
}

def get_symbols():
    url = f"{API_BASE_URL}/symbols"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("symbols", [])

def get_general_info(symbol: str):
    url = f"{API_BASE_URL}/general/{symbol}?"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_income_statement(symbol: str):
    url = f"{API_BASE_URL}/financials/{symbol}/income_statement"

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Falls Fehler, Exception werfen
    
    return response.json()

def get_financials(symbol: str,statement_type:str):
    url = f"{API_BASE_URL}/financials/{symbol}/{statement_type}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Falls Fehler, Exception werfen
    
    return response.json()

def get_revenue_quarters(income_statement_data):
    """
    Extrahiert Q1 und Q2 Umsätze für Revenue Growth Berechnung.
    Falls Q1 fehlt → Q4 Vorjahr als Ersatz.
    Falls Q2 fehlt → kein Revenue Growth möglich.
    """

    records = income_statement_data.get("fundamentals", {}) \
        .get("financials", {}) \
        .get("income_statement", {}) \
        .get("data", [])

    if not records:
        return None, None

    # Nur Quartalsdaten (FY entfernen)
    quarter_records = [r for r in records if r.get("period") in ["Q1", "Q2", "Q3", "Q4"]]

    if not quarter_records:
        return None, None

    # Nach Datum DESC sortieren → neueste zuerst
    quarter_records.sort(key=lambda r: r.get("date"), reverse=True)

    # -------------------------
    # 1. Versuche Q1 + Q2 im gleichen Jahr
    # -------------------------
    q1, q2 = None, None

    # Index-basiert durchlaufen, um Q1 → Q2 logik zu garantieren
    for i, rec in enumerate(quarter_records):
        if rec.get("period") == "Q1":
            year = rec.get("date")[:4]
            q1 = rec.get("revenue")

            # Suche danach Q2 selben Jahres
            for r2 in quarter_records[i+1:]:
                if r2.get("period") == "Q2" and r2.get("date")[:4] == year:
                    q2 = r2.get("revenue")
                    return q1, q2

    # -------------------------
    # 2. Falls kein Q1/Q2 → nutze Q4 Vorjahr für Q1
    # -------------------------
    # Suche Q2
    q2_record = next((r for r in quarter_records if r.get("period") == "Q2"), None)
    if q2_record:
        q2 = q2_record.get("revenue")
        q2_year = int(q2_record.get("date")[:4])

        # Suche Q4 vom Vorjahr
        q4_prev_year_record = next(
            (r for r in quarter_records
             if r.get("period") == "Q4" and int(r.get("date")[:4]) == q2_year - 1),
            None
        )

        if q4_prev_year_record:
            q1 = q4_prev_year_record.get("revenue")
            return q1, q2

    # -------------------------
    # 3. Falls alles fehlt → kein Revenue Growth möglich
    # -------------------------
    return None, None



def get_net_income_ttm(income_statement_data):
    """
    Berechnet Net Income TTM (Trailing Twelve Months).
    TTM = Summe der letzten vier Quartale (Q1, Q2, Q3, Q4).
    Falls weniger als 4 Quartale vorhanden sind → return None.
    """

    records = income_statement_data.get("fundamentals", {}) \
        .get("financials", {}) \
        .get("income_statement", {}) \
        .get("data", [])

    if not records:
        return None

    # Nur Quartalsdaten verwenden
    quarter_records = [
        r for r in records
        if r.get("period") in ["Q1", "Q2", "Q3", "Q4"]
    ]

    if not quarter_records:
        return None

    # Sortieren nach Datum (neueste zuerst)
    quarter_records.sort(key=lambda r: r.get("date"), reverse=True)

    # Nimm die letzten 4 Quartale
    latest_four = quarter_records[:4]

    # Prüfe ob es wirklich vier sind
    if len(latest_four) < 4:
        return None

    # Netto Einkommen summieren
    net_income_values = []

    for q in latest_four:
        ni = q.get("netIncome")
        if ni is None:
            return None
        net_income_values.append(ni)

    return sum(net_income_values)

def get_debt_ratio(symbol: str) -> float | None:
    """
    Get Debt-to-Equity ratio = totalDebt / totalEquity
    using the Fiindo balance_sheet_statement endpoint.
    """

    data = get_financials(symbol, "balance_sheet_statement")
    try:
        records = (
            data.get("fundamentals", {})
                .get("financials", {})
                .get("balance_sheet_statement", {})
                .get("data", [])
        )
        
        if not records:
            print(f"[WARN] No balance sheet data for {symbol}")
            return None

        # filter FY records
        fy_records = [r for r in records if r.get("period") == "FY"]

        if not fy_records:
            print(f"[WARN] No FY records found for {symbol}")
            return None

        # sort by newest date
        fy_records.sort(key=lambda r: r.get("date", ""), reverse=True)
        latest = fy_records[0]

        total_debt = latest.get("totalDebt")
        total_equity = (
            latest.get("totalStockholdersEquity") or
            latest.get("totalEquity")
        )

        # validate
        if total_debt is None:
            print(f"[WARN] totalDebt missing for {symbol}")
            return None

        if total_equity is None or total_equity == 0:
            print(f"[WARN] totalEquity missing or zero for {symbol}")
            return None

        return total_debt / total_equity

    except Exception as e:
        print(f"[ERROR] get_debt_ratio({symbol}) failed:", e)
        return None
