class Student:
    def __init__(self,name,age):
        self.name = name
        self.age = age
    def greet(self):
        print(f"Hello! My name is {self.name} and I'm {self.age} years old.")

s1 = Student("Aigerim",17)
s1.greet()