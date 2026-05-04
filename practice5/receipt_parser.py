import re
import json

def all_price(price_str):
    """
    Convert prices like '1 200,00' to float 1200.00
    """
    price_str = price_str.replace(" ", "").replace(",", ".")
    return float(price_str)

def parse_receipt(text):
    data = {}

    # Extract all products 
    product_pattern = r"\d+\.\s*(.+?)\n(\d+,\d+|\d+(?: \d{3})*,\d{2}) x (\d{1,3}(?: \d{3})*,\d{2})\n(\d{1,3}(?: \d{3})*,\d{2})"
    matches = re.findall(product_pattern, text, flags=re.DOTALL)

    products = []
    for match in matches:
        name = match[0].strip()
        qty = all_price(match[1])
        unit_price = all_price(match[2])
        total = all_price(match[3])
        products.append({
            "name": name,
            "quantity": qty,
            "unit_price": unit_price,
            "total_price": total
        })

    data["products"] = products

    # Extract total receipt 
    total_pattern = r"ИТОГО:\s*\n?(\d{1,3}(?: \d{3})*,\d{2})"
    total_match = re.search(total_pattern, text)
    data["total_receipt"] = all_price(total_match.group(1)) if total_match else None

    # Extract date and time
    datetime_pattern = r"Время:\s*(\d{2}\.\d{2}\.\d{4})\s*(\d{2}:\d{2}:\d{2})"
    datetime_match = re.search(datetime_pattern, text)
    if datetime_match:
        data["date"] = datetime_match.group(1)
        data["time"] = datetime_match.group(2)
    else:
        data["date"] = None
        data["time"] = None

    # Extract payment method
    payment_pattern = r"(Банковская карта)"
    payment_match = re.search(payment_pattern, text)
    data["payment_method"] = payment_match.group(1) if payment_match else None

    return data

if __name__ == "__main__":
    with open("raw.txt", "r", encoding="utf-8") as f:
        receipt_text = f.read()

    parsed_data = parse_receipt(receipt_text)
    print(json.dumps(parsed_data, indent=4, ensure_ascii=False))