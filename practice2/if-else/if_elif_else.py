gpa = float(input("GPA:"))
income = int(input("Family income: "))
disc_issues = input("Discipline issues? (yes/no) :")

if disc_issues == "yes":
    print("Scolarship denied")
elif gpa >= 3.7 and income < 500000:
    print("Full scolarship")
elif gpa >= 3.3:
    print("Partial scholarship")
else:
    print("No scholarship")
