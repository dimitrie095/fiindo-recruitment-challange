def calculate_pe_ratio(price, eps):
    if eps is None or eps == 0:
        return None
    return price / eps

def calculate_revenue_growth(revenue_q1, revenue_q2):
    if revenue_q2 == 0 or revenue_q2 is None or revenue_q1 is None:
        return None
    return (revenue_q1 - revenue_q2) / revenue_q2

def calculate_debt_ratio(total_debt, total_equity):
    if total_equity == 0 or total_equity is None or total_debt is None:
        return None
    return total_debt / total_equity



def get_net_income_ttm(income_statements):
    # Suche den letzten FY Eintrag und nehme netIncome daraus
    for entry in sorted(income_statements, key=lambda x: x['date'], reverse=True):
        if entry.get("period") == "FY" and entry.get("netIncome") is not None:
            return entry["netIncome"]
    return None

