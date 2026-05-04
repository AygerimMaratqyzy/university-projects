import csv
import json
import math
from datetime import date, datetime
from connect import get_connection
from config import PAGE_SIZE, DEFAULT_CSV_PATH, DEFAULT_JSON_PATH


def _row_as_dict(row, cursor):
    """Turn a psycopg2 row tuple into a dict using cursor.description."""
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def _print_contact(c: dict):
    """Pretty-print one contact row from v_contacts / search_contacts."""
    print(f"  ID      : {c.get('id', '-')}")
    print(f"  Name    : {c.get('full_name', c.get('first_name', ''))}")
    if c.get('email'):
        print(f"  Email   : {c['email']}")
    if c.get('birthday'):
        print(f"  Birthday: {c['birthday']}")
    if c.get('grp'):
        print(f"  Group   : {c['grp']}")
    print(f"  Phones  : {c.get('phones_csv') or '(none)'}")
    print()


def _resolve_group_id(cur, group_name: str):
    """Return group id, creating the group row if needed."""
    cur.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO groups (name) VALUES (%s) RETURNING id", (group_name,))
    return cur.fetchone()[0]


#1.insert/upsert

def insert_or_update():
    print("\n── Add / Update contact ─────────────────────────────────")
    first_name = input("First name : ").strip()
    last_name  = input("Last name  : ").strip() or None

    #fix:phone collection loop is self-contained; everything else is outside it
    while True:
        phone = input("Phone (digits only, blank to skip): ").strip()
        if phone == "":
            phone = None
            break
        if phone.isdigit():
            break
        print("  Phone must contain only digits. Try again.")

    phone_type = None
    if phone:
        while True:
            phone_type = input("Phone type [home/work/mobile]: ").strip().lower()
            if phone_type in ("home", "work", "mobile"):
                break
            print("  Must be home, work or mobile.")

    email    = input("Email (blank to skip)              : ").strip() or None
    birthday = None
    bday_str = input("Birthday YYYY-MM-DD (blank to skip): ").strip()
    if bday_str:
        try:
            birthday = datetime.strptime(bday_str, "%Y-%m-%d").date()
        except ValueError:
            print("  ! Invalid date format – birthday skipped.")

    group_name = input("Group [Family/Work/Friend/Other/custom]: ").strip() or None

    conn = get_connection()
    cur  = conn.cursor()
    try:
        #fix:procedure name added to execute call
        cur.execute(
            "CALL upsert_contact(%s, %s, %s, %s)",
            (first_name, last_name, phone, phone_type or "mobile")
        )

        cur.execute(
            """
            UPDATE contacts
            SET email    = COALESCE(%s, email),
                birthday = COALESCE(%s, birthday)
            WHERE first_name = %s
              AND COALESCE(last_name, '') = %s
            """,
            (email, birthday, first_name, last_name or "")
        )

        if group_name:
            group_id = _resolve_group_id(cur, group_name)
            cur.execute(
                "UPDATE contacts SET group_id = %s "
                "WHERE first_name = %s AND COALESCE(last_name, '') = %s",
                (group_id, first_name, last_name or "")
            )

        conn.commit()
        print("  Contact saved.")
    except Exception as e:
        conn.rollback()
        print("  Error:", e)
    finally:
        cur.close()
        conn.close()


#2.add phone

def add_phone():
    """Add an extra number to an existing contact."""
    print("\n── Add phone number ─────────────────────────────────────")
    name = input("Contact name (First or First Last): ").strip()

    while True:
        phone = input("Phone (digits only): ").strip()
        if phone.isdigit():
            break
        print("  Digits only.")

    while True:
        ptype = input("Type [home/work/mobile]: ").strip().lower()
        if ptype in ("home", "work", "mobile"):
            break
        print("  Must be home, work or mobile.")

    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, ptype))
        conn.commit()
        print("  Phone added.")
    except Exception as e:
        conn.rollback()
        print("  Error:", e)
    finally:
        cur.close()
        conn.close()


#3.move to group

def move_to_group():
    """Move a contact to a group (creates the group if it doesn't exist)."""
    print("\n── Move contact to group ────────────────────────────────")
    name  = input("Contact name (First or First Last): ").strip()
    group = input("Group name                        : ").strip()

    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("CALL move_to_group(%s, %s)", (name, group))
        conn.commit()
        print(f"  {name} moved to group '{group}'.")
    except Exception as e:
        conn.rollback()
        print("  Error:", e)
    finally:
        cur.close()
        conn.close()


#4.search

def search():
    print("\n── Search contacts ──────────────────────────────────────")
    pattern = input("Search query: ").strip()
    if not pattern:
        print("  ! Query cannot be empty.")
        return

    print("Sort by: [1] Name  [2] Birthday  [3] Date added")
    sort_choice = input("Choice [1]: ").strip() or "1"
    #fix:fallback key was "full name" (with space); corrected to "full_name"
    sort_key = {"1": "full_name", "2": "birthday", "3": "created_at"}.get(
        sort_choice, "full_name"
    )

    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT * FROM search_contacts(%s)", (pattern,))
        rows = cur.fetchall()
        if not rows:
            print("  No contacts found.")
            return

        contacts = [_row_as_dict(r, cur) for r in rows]

        def sort_val(c):
            v = c.get(sort_key) or ""
            return str(v).lower()

        contacts.sort(key=sort_val)
        print(f"\n  {len(contacts)} result(s):\n")
        for c in contacts:
            _print_contact(c)
    except Exception as e:
        print("  Error:", e)
    finally:
        cur.close()
        conn.close()


#5.filter by group

def filter_by_group():
    print("\n── Filter by group ──────────────────────────────────────")
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, name FROM groups ORDER BY name")
        groups = cur.fetchall()
        if not groups:
            print("  No groups found.")
            return

        print("  Available groups:")
        for gid, gname in groups:
            print(f"    {gid}. {gname}")

        choice = input("Enter group ID or name: ").strip()

        if choice.isdigit():
            cur.execute(
                """
                SELECT * FROM v_contacts
                WHERE  grp = (SELECT name FROM groups WHERE id = %s)
                ORDER  BY first_name, last_name
                """,
                (int(choice),)
            )
        else:
            cur.execute(
                "SELECT * FROM v_contacts WHERE grp ILIKE %s ORDER BY first_name, last_name",
                (choice,)
            )

        rows = cur.fetchall()
        if not rows:
            print("  No contacts in this group.")
            return

        contacts = [_row_as_dict(r, cur) for r in rows]
        print(f"\n  {len(contacts)} contact(s):\n")
        for c in contacts:
            _print_contact(c)
    except Exception as e:
        print("  Error:", e)
    finally:
        cur.close()
        conn.close()


#6.delete

def delete():
    """Delete a contact by name or phone."""
    print("\n── Delete contact ───────────────────────────────────────")
    value = input("Enter name or phone to delete: ").strip()
    conn  = get_connection()
    cur   = conn.cursor()
    try:
        cur.execute("CALL delete_contact(%s)", (value,))
        conn.commit()
        print("  Contact(s) deleted.")
    except Exception as e:
        conn.rollback()
        print("  Error:", e)
    finally:
        cur.close()
        conn.close()


#7.paginated listing

def paginate():
    print("\n── All contacts (paginated) ─────────────────────────────")
    page  = 0
    limit = PAGE_SIZE

    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM contacts")
    total = cur.fetchone()[0]
    if total == 0:
        print("  No contacts in the database.")
        cur.close()
        conn.close()
        return

    total_pages = math.ceil(total / limit)

    while True:
        offset = page * limit
        cur.execute("SELECT * FROM get_contacts_paginated(%s, %s)", (limit, offset))
        rows     = cur.fetchall()
        contacts = [_row_as_dict(r, cur) for r in rows]

        print(f"\n  Page {page + 1} of {total_pages} ({total} total contacts)\n")
        for c in contacts:
            _print_contact(c)

        options = []
        if page > 0:
            options.append("[p]rev")
        if page < total_pages - 1:
            options.append("[n]ext")
        options.append("[q]uit")

        nav = input("  Navigate: " + "  ".join(options) + " → ").strip().lower()
        if nav == "n" and page < total_pages - 1:
            page += 1
        elif nav == "p" and page > 0:
            page -= 1
        elif nav == "q":
            break
        else:
            print("  ! Invalid navigation key.")

    cur.close()
    conn.close()


#8.bulk insert

def bulk_insert():
    print("\n── Bulk insert ──────────────────────────────────────────")
    try:
        n = int(input("How many contacts: ").strip())
    except ValueError:
        print("  ! Enter a number.")
        return

    first_names, last_names, phones = [], [], []
    for i in range(n):
        print(f"\n  Contact {i + 1}/{n}")
        first_names.append(input("    First name : ").strip())
        last_names.append(input("    Last name  : ").strip() or None)
        while True:
            ph = input("    Phone (digits only): ").strip()
            if ph.isdigit():
                phones.append(ph)
                break
            print("    Digits only.")

    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT bulk_insert_contacts(%s::TEXT[], %s::TEXT[], %s::TEXT[])",
            (first_names, last_names, phones)
        )
        invalid = cur.fetchone()[0]
        conn.commit()
        #fix:else was incorrectly attached to the for loop; now correctly tied to if
        if invalid:
            print("\n  Invalid / rejected entries:")
            for item in invalid:
                print("  •", item)
        else:
            print("  All contacts inserted successfully.")
    except Exception as e:
        conn.rollback()
        print("  Error:", e)
    finally:
        cur.close()
        conn.close()


#9.csv import

def insert_from_csv(file=DEFAULT_CSV_PATH):
    print(f"\n── Import from CSV: {file} ────────────────────────────")
    conn = get_connection()
    cur  = conn.cursor()
    ok = skipped = 0

    try:
        with open(file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fn    = row.get("first_name", "").strip()
                ln    = row.get("last_name",  "").strip() or None
                ph    = row.get("phone",      "").strip() or None
                ptype = row.get("phone_type", "mobile").strip().lower()
                email = row.get("email",      "").strip() or None
                bday  = row.get("birthday",   "").strip() or None
                grp   = row.get("group",      "").strip() or None

                if not fn:
                    print(f"  ! Skipping row with no first_name: {row}")
                    skipped += 1
                    continue

                if ph and not ph.isdigit():
                    print(f"  ! Skipping {fn}: phone '{ph}' contains non-digits.")
                    skipped += 1
                    continue

                if ptype not in ("home", "work", "mobile"):
                    ptype = "mobile"

                birthday = None
                if bday:
                    try:
                        birthday = datetime.strptime(bday, "%Y-%m-%d").date()
                    except ValueError:
                        print(f"  ! {fn}: bad birthday '{bday}' – skipped.")

                group_id = None
                if grp:
                    group_id = _resolve_group_id(cur, grp)

                cur.execute(
                    """
                    INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """,
                    (fn, ln, email, birthday, group_id)
                )
                contact_id = cur.fetchone()[0]
 
                if ph:
                    cur.execute(
                        """
                        INSERT INTO phones (contact_id, phone, type)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (contact_id, ph, ptype)
                    )
                ok += 1

        conn.commit()
        print(f"  Imported {ok} contact(s), skipped {skipped}.")
    except FileNotFoundError:
        print(f"  File '{file}' not found.")
    except Exception as e:
        conn.rollback()
        print("  Error:", e)
    finally:
        cur.close()
        conn.close()


#10.json export

def export_to_json(file=DEFAULT_JSON_PATH):
    """Export all contacts (with phones and group) to a JSON file."""
    print(f"\n── Export to JSON: {file} ───────────────────────────────")
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                c.id, c.first_name, c.last_name, c.email,
                c.birthday::TEXT, c.created_at::TEXT,
                g.name AS grp,
                COALESCE(
                    JSON_AGG(
                        JSON_BUILD_OBJECT('phone', p.phone, 'type', p.type)
                        ORDER BY p.type
                    ) FILTER (WHERE p.id IS NOT NULL),
                    '[]'
                ) AS phones
            FROM contacts c
            LEFT JOIN groups g ON g.id = c.group_id
            LEFT JOIN phones p ON p.contact_id = c.id
            GROUP BY c.id, c.first_name, c.last_name,
                     c.email, c.birthday, c.created_at, g.name
            ORDER BY c.first_name, c.last_name
            """
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        data = [dict(zip(cols, row)) for row in rows]

        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        print(f"  Exported {len(data)} contact(s) → {file}")
    except Exception as e:
        print("  Error:", e)
    finally:
        cur.close()
        conn.close()


#11.json import

def import_json_json(file=DEFAULT_JSON_PATH):
    print(f"\n── Import from JSON: {file} ─────────────────────────────")
    try:
        with open(file, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"  File '{file}' not found.")
        return
    except json.JSONDecodeError as e:
        print(f"  Invalid JSON: {e}")
        return

    conn = get_connection()
    cur  = conn.cursor()
    ok = skipped = overwritten = 0

    try:
        for rec in data:
            fn    = (rec.get("first_name") or "").strip()
            ln    = (rec.get("last_name")  or "").strip() or None
            email = (rec.get("email")      or "").strip() or None
            bday  = (rec.get("birthday")   or "").strip() or None
            grp   = (rec.get("grp")        or "").strip() or None
            phones_list = rec.get("phones") or []

            if not fn:
                print(f"  ! Skipping record with no first_name: {rec}")
                skipped += 1
                continue

            birthday = None
            if bday:
                try:
                    birthday = datetime.strptime(bday, "%Y-%m-%d").date()
                except ValueError:
                    pass

            cur.execute(
                "SELECT id FROM contacts WHERE first_name = %s AND COALESCE(last_name, '') = %s",
                (fn, ln or "")
            )
            existing = cur.fetchone()

            if existing:
                choice = input(
                    f"  ! Duplicate: '{fn} {ln or ''}' already exists. "
                    "[s]kip / [o]verwrite? "
                ).strip().lower()
                if choice != "o":
                    skipped += 1
                    continue
                contact_id = existing[0]
                cur.execute("DELETE FROM phones WHERE contact_id = %s", (contact_id,))
                group_id = _resolve_group_id(cur, grp) if grp else None
                cur.execute(
                    """
                    UPDATE contacts
                    SET email = %(email)s, birthday = %(birthday)s, group_id = %(gid)s
                    WHERE id = %(cid)s
                    """,
                    {"email": email, "birthday": birthday,
                     "gid": group_id, "cid": contact_id}
                )
                overwritten += 1
            else:
                group_id = _resolve_group_id(cur, grp) if grp else None
                cur.execute(
                    """
                    INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                    """,
                    (fn, ln, email, birthday, group_id)
                )
                contact_id = cur.fetchone()[0]
                ok += 1

            for ph in phones_list:
                p_num  = (ph.get("phone") or "").strip()
                p_type = (ph.get("type")  or "mobile").strip().lower()
                if p_num and p_num.isdigit():
                    if p_type not in ("home", "work", "mobile"):
                        p_type = "mobile"
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                        (contact_id, p_num, p_type)
                    )

        conn.commit()
        print(f"  ✓ Inserted: {ok}  |  Overwritten: {overwritten}  |  Skipped: {skipped}")
    except Exception as e:
        conn.rollback()
        print("  ✗ Error:", e)
    finally:
        cur.close()
        conn.close()


#main menu

def menu():
    while True:
        print("\n" + "=" * 50)
        print("          PhoneBook  –  TSIS1")
        print("=" * 50)
        print(" 1. Add / Update contact")
        print(" 2. Add extra phone number to a contact")
        print(" 3. Move contact to group")
        print(" 4. Search contacts  (name / email / phone)")
        print(" 5. Filter contacts by group")
        print(" 6. Delete contact")
        print(" 7. List all contacts  (paginated)")
        print(" 8. Bulk insert contacts")
        print("─" * 50)
        print(" 9. Import contacts from CSV")
        print("10. Import contacts from JSON")
        print("11. Export contacts to JSON")
        print("─" * 50)
        print(" 0. Exit")
        print("=" * 50)

        choice = input("Choose an option: ").strip()

        if   choice == "1":  insert_or_update()
        elif choice == "2":  add_phone()
        elif choice == "3":  move_to_group()
        elif choice == "4":  search()
        elif choice == "5":  filter_by_group()
        elif choice == "6":  delete()
        elif choice == "7":  paginate()
        elif choice == "8":  bulk_insert()
        elif choice == "9":
            path = input(f"CSV path [{DEFAULT_CSV_PATH}]: ").strip() or DEFAULT_CSV_PATH
            insert_from_csv(path)
        elif choice == "10":
            path = input(f"JSON path [{DEFAULT_JSON_PATH}]: ").strip() or DEFAULT_JSON_PATH
            #fix:was calling undefined import_from_json; corrected to import_json_json
            import_json_json(path)
        elif choice == "11":
            path = input(f"JSON path [{DEFAULT_JSON_PATH}]: ").strip() or DEFAULT_JSON_PATH
            export_to_json(path)
        elif choice == "0":
            print("Exiting PhoneBook. Goodbye!")
            break
        else:
            print("  ! Invalid choice – please enter a number from the menu.")


if __name__ == "__main__":
    menu()