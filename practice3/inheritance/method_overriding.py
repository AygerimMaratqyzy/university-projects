class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print("The animal makes a sound.")

    def info(self):
        print("This is an animal named", self.name)

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)   
        self.breed = breed

    def speak(self):           
        print(self.name, "barks loudly!")

    def info(self):              
        super().info()          
        print("Breed:", self.breed)

my_dog = Dog("Buddy", "Golden Retriever")

my_dog.speak()   
my_dog.info()  