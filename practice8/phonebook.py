from connect import get_connection
def insert_or_update():
    name = input("Enter name: ")

    while True:
        phone = input("Enter phone: ")
        if not phone.isdigit():
            print("Phone must contain only digits! Try again.")
            continue

    
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("CALL upsert_contact(%s, %s)", (name, phone))
            conn.commit()
            print("Saved successfully!")
            cur.close()
            conn.close()
            break
        except Exception as e:
            print("Database error:", e)
            conn.rollback()
            cur.close()
            conn.close()


def search():
    pattern = input("Search: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM search_contacts(%s)", (pattern,))
    rows = cur.fetchall()

    for row in rows:
        print(row)

    cur.close()
    conn.close()


def paginate():
    limit = int(input("Limit: "))
    offset = int(input("Offset: "))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM get_contacts_paginated(%s, %s)", (limit, offset))
    rows = cur.fetchall()

    for row in rows:
        print(row)

    cur.close()
    conn.close()


def delete():
    value = input("Enter name or phone to delete: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("CALL delete_contact(%s)", (value,))
    conn.commit()

    cur.close()
    conn.close()


def bulk_insert():
    n = int(input("How many contacts: "))
    names = []
    phones = []

    for _ in range(n):
        names.append(input("Name: "))
        while True:
            phone = input("Phone: ")
            if phone.isdigit():
                phones.append(phone)
                break
            else:
                print("Phone must contain only digits!")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT bulk_insert_contacts(%s::TEXT[], %s::TEXT[])",
        (names, phones)
    )

    invalid_data = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    if invalid_data:
        print("Invalid entries:")
        for item in invalid_data:
            print(item)
    else:
        print("All contacts inserted successfully.")

def menu():
    while True:
        print("\n--- PhoneBook ---")
        print("1. Insert/Update")
        print("2. Search")
        print("3. Pagination")
        print("4. Delete")
        print("5. Bulk Insert")
        print("6. Exit")

        choice = input("Choose: ")

        if choice == "1":
            insert_or_update()
        elif choice == "2":
            search()
        elif choice == "3":
            paginate()
        elif choice == "4":
            delete()
        elif choice == "5":
            bulk_insert()
        elif choice == "6":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    menu()