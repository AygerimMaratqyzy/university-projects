class Father:
    def skills(self):
        print("Gardening")

class Mother:
    def skills(self):
        print("Cooking")

class Child(Father, Mother):
    def skills(self):
        print("Drawing")
        Father.skills(self)  
        Mother.skills(self)   

kid = Child()
kid.skills()