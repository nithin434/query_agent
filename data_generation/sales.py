import sqlite3
import random


conn = sqlite3.connect('transcripts.db') 
cursor = conn.cursor()


cursor.execute("SELECT id FROM calls")
call_ids = [row[0] for row in cursor.fetchall()]


product_types = {
    "TV": ["DirecTV Satellite", "DirecTV Stream", "U-verse TV"],
    "Internet": ["AT&T Fiber", "AT&T Internet", "Fixed Wireless"],
    "Wireless": ["AT&T Unlimited", "AT&T Prepaid", "FirstNet"],
    "None": ["No Sale"]
}


payment_methods = ["Credit card", "Debit card", "ACH", None]


sales_data = []

for call_id in call_ids:

    sale_success = random.random() < 0.7
    
    if sale_success:

        product_type = random.choice(list(product_types.keys())[:-1])

        product_subtype = random.choice(product_types[product_type])

        payment_method = random.choice(payment_methods[:-1]) 

        convinced_with_rep = random.random() < 0.85
        verification_done = random.random() < 0.95
        knows_autopay = random.random() < 0.9
    else:

        product_type = "None"
        product_subtype = "No Sale"
        payment_method = None
        convinced_with_rep = random.random() < 0.3
        verification_done = random.random() < 0.5
        knows_autopay = random.random() < 0.4
    
    sales_data.append((
        call_id,
        product_type,
        product_subtype,
        sale_success,
        payment_method,
        convinced_with_rep,
        verification_done,
        knows_autopay
    ))


try:
    cursor.executemany("""
        INSERT INTO sales (
            call_id,
            product_type,
            product_subtype,
            sale_success,
            payment_method,
            convinced_with_rep,
            verification_done,
            knows_autopay_requirement
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sales_data)
    

    conn.commit()
    print(f"Successfully inserted {len(sales_data)} records into the sales table")

except sqlite3.Error as e:
    print(f"Error inserting data: {e}")
    conn.rollback()


conn.close()