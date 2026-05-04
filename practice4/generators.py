def sq(N):               #1
    i = 1 
    while True:
        v = i * i
        if v <= N:
            yield v
        else:
            break
        i += 1
N = int(input())
for s in sq(N):
    print(s)

def even_numbers(n):             #2
    i = 0
    while i <= n:
        yield i
        i += 2 
n = int(input())
first = True
for s in even_numbers(n):
    if not first:
        print(",", end="")
    print(s,end="")
    first = False

def divisible(n):                      #3
    i = 0 
    while i <= n:
        if i % 3 == 0 and i % 4 == 0:
            yield i
        i += 1
    
n = int(input())
for s in divisible(n):
    print(s)

def squares(a,b):                   #4
    for i in range(a,b):
        yield i * i

a,b = map(int,input().split())

for s in squares(a,b):
    print(s)

def all_num(n):                  #5
    while n >= 0:
        yield n 
        n -= 1

n = int(input())
for s in all_num(n):
    print(s)