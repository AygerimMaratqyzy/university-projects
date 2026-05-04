def my_function(name,/,*,country = "Kazakhstan" ):
    print(f"My name is {name} , I am from", country)

my_function("Michael",country = "Netherlands")
my_function("Taylor",country ="Switzerland")
my_function("Kai",country = "Denmark")
my_function("Aigerim")


