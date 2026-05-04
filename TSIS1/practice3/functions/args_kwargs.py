def show_student(name,*scores, **info):
    print("Name:",name)
    print("Scores:",end =" ")
    for s in scores:
        print(s,end=" ")
    print()

    print("Extra info:")
    for key,value in info.items():
        print(key,"=",value)

show_student("Alex",85,90,95,age=20,city="Almaty",scholarship=True)