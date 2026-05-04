class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print("The animal makes a sound.")

class Dog(Animal):   # Dog inherits from Animal
    def speak(self): # Method overriding
        print(self.name, "says Woof!")

my_dog = Dog("Buddy")

print(my_dog.name)   # inherited attribute
my_dog.speak()  