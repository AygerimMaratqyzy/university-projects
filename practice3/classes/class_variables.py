class Dog:
    sp = "Canis familiaris"
    def __init__(self,name,age):
        self.name = name
        self.age =age
    def info(self):
        print(f"My name is {self.name}, I am {self.age} years old.")
        print(f"My species is {Dog.sp}")

dog1 = Dog("Buddy", 3)
dog2 =Dog("lucy",5)

dog1.info()
dog2.info()

print("All dogs belong to species:" ,Dog.sp)

print(dog1.name)
print(dog2.age)
        