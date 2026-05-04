password = input("Enter password: ")
is_long = len(password) >= 8
has_digit = "0" <= min(password) <= "9" or "0" <= max(password) <= "9"
if is_long and has_digit:
    print("Access granted")
else:
    print("Password too weak")