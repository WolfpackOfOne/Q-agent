"""Ticker -> company name mapping for GDELT free-text queries.

Mirrors the WRDS 30-stock equity universe
(infrastructure/pipelines/wrds/src/wrds_lean/symbols.py) so sentiment data
lines up with an existing price universe out of the box.
"""

COMPANY_NAMES = {
    "AAPL": "Apple Inc",
    "AMGN": "Amgen Inc",
    "AXP":  "American Express",
    "BA":   "Boeing Company",
    "CAT":  "Caterpillar Inc",
    "CRM":  "Salesforce Inc",
    "CSCO": "Cisco Systems",
    "CVX":  "Chevron Corporation",
    "DIS":  "Walt Disney Company",
    "DOW":  "Dow Inc",
    "GS":   "Goldman Sachs",
    "HD":   "Home Depot",
    "HON":  "Honeywell International",
    "IBM":  "International Business Machines",
    "INTC": "Intel Corporation",
    "JNJ":  "Johnson & Johnson",
    "JPM":  "JPMorgan Chase",
    "KO":   "Coca-Cola Company",
    "MCD":  "McDonald's Corporation",
    "MMM":  "3M Company",
    "MRK":  "Merck & Co",
    "MSFT": "Microsoft Corporation",
    "NKE":  "Nike Inc",
    "PG":   "Procter & Gamble",
    "TRV":  "Travelers Companies",
    "UNH":  "UnitedHealth Group",
    "V":    "Visa Inc",
    "VZ":   "Verizon Communications",
    "WBA":  "Walgreens Boots Alliance",
    "WMT":  "Walmart Inc",
}

UNIVERSE = list(COMPANY_NAMES.keys())
