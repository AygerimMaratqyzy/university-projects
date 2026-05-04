def myfunc(n):
    return lambda a:a * n
b = myfunc(5)
c = myfunc(6)

print(b(9))
print(c(9))