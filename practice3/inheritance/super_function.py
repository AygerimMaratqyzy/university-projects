class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print("The animal makes a sound.")

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)   
        self.breed = breed

    def speak(self):
        super().speak()         
        print(self.name, "says Woof!")

my_dog = Dog("Buddy", "Golden Retriever")

print(my_dog.name)    # inherited from Animal
print(my_dog.breed)   # defined in Dog
my_dog.speak()