import csv
from connect import connect
def insert_from_csv(file= 'contacts.csv'):
    conn = connect()
    cur = conn.cursor()
    try:
        with open(file,newline='',encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute(
                    "INSERT INTO contacts (first_name, last_name, phone) VALUES (%s, %s, %s)",
                    (row['first_name'], row['last_name'], row['phone'])

                )
        conn.commit()
        print("Contacts succesfully added.")
    except Exception as e:
        print("Error:", e)
    finally:
        cur.close()
        conn.close()
def insert_console():
    """Insert a contact via console"""
    first_name = input("First name: ")
    last_name = input("Last name:")
    phone = input("Phone:")
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO contacts (first_name, last_name, phone) VALUES (%s, %s, %s)" ,
            (first_name,last_name,phone)
        )
        conn.commit()
        print("Contact added.")
    except Exception as e:
        print("Error:",e)
    finally:
        cur.close()
        conn.close()
def update_contact():
    """Update a contact's first name or phone number"""
    contact_id = input("the ID:")
    first_name = input("New First Name:")
    phone = input("New Phone:")

    conn = connect()
    cur = conn.cursor()
    try:
        if first_name:
            cur.execute("UPDATE contacts SET first_name=%s WHERE id=%s" , (first_name, contact_id))
        if phone:
            cur.execute("UPDATE contacts SET phone=%s WHERE id=%s" , (phone, contact_id))
        conn.commit()
        print("contact updated.")
    except Exception as e:
        print("Error:", e)
    finally:
        cur.close()
        conn.close()

def search_contacts():
    """Search contacts by first name or phone prefix"""
    name = input("Enter name to search:")
    phone_prefix = input("Enter phone prefix to search:")

    conn = connect()
    cur = conn.cursor()
    try:
        query = "SELECT * FROM contacts WHERE 1=1"
        params = []
        if name:
            query += " AND first_name ILIKE %s"
            params.append(f"%{name}%")
        if phone_prefix:
            query += " AND phone LIKE %s"
            params.append(f"{phone_prefix}%")
        cur.execute(query,params)
        rows = cur.fetchall()
        if rows:
            print("Search results:")
            for row in rows:
                print(f"ID: {row[0]}, First Name: {row[1]}, Last Name: {row[2]}, Phone: {row[3]}")
        else:
            print("No contacts found.")
    except Exception as e:
        print("Error:" , e)
    finally:
        cur.close()
        conn.close()

def delete_contact():
    """Delete a contact by first name or phone"""
    name = input("Enter the first name")
    phone = input("Enter the phone of the contact")

    conn = connect()
    cur = conn.cursor()
    try:
        query = "DELETE FROM contacts WHERE 1=1"
        params = []
        if name:
            query += " AND first_name=%s"
            params.append(name)
        if phone:
            query += " AND phone=%s"
            params.append(phone)
        cur.execute(query,params)
        conn.commit()
        print("Contact(s) deleted.")
    except Exception as e:
        print("Error:", e)
    finally:
        cur.close()
        conn.close()
    
def menu():
    """User menu for the PhoneBook application"""
    while True:
        print("\n=== PhoneBook Menu ===")
        print("1. Insert contacts from CSV")
        print("2. Add contact manually")
        print("3. Update contact")
        print("4. Search contacts")
        print("5. Delete contact")
        print("6. Exit")
        choice = input("Choose an option (1-6): ")

        if choice == '1':
            insert_from_csv()
        elif choice == '2':
            insert_console()
        elif choice == '3':
            update_contact()
        elif choice == '4':
            search_contacts()
        elif choice == '5':
            delete_contact()
        elif choice == '6':
            print("Exiting PhoneBook...")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    menu()