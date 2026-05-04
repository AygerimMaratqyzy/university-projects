class Calculator:
    def __init__(self,number):
        self.number = number
    def add(self,value):
        self.number += value
        print(f"After adding {value}: {self.number}")
    def substract(self,value):
        self.number -= value
        print(f"After substracting {value}:{self.number}")
    def multiply(self,value):
        self.number *= value
        print(f"after multiplying by {value}:{self.number}")
    def divide(self,value):
        if value == 0:
            print("Cannot divide by zero!")
        else:
            self.number /= value
            print(f"After dividing by {value}: {self.number}")
calc = Calculator(10)
calc.add(5)
calc.substract(3)
calc.multiply(4)
calc.divide(2)
calc.divide(0)