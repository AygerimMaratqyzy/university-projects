import math                         #1
d = int(input("Input degree: "))
r = (math.pi * d)/180
print(f"Output radian:{r:.6f}")

h,b1,b2 = map(int,input().split())     #2
s = (b2+b1) * h/2
print(s)

num_s,length = map(int,input().split())                   #3
a = (num_s * length * length)/4 * math.tan(math.pi/num_s)
print("The area of the polygon is:",math.ceil(a))
 
length_of_base,height = map(float,input().split())        #4
ar = length_of_base * height
print(f"Expected Output: ",ar)