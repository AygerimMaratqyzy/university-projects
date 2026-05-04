from functools import reduce
nums = [7,14,21,28,35,42]
cubed_nums = list(map(lambda x:x**3,nums))     #map()
print("Cubed numbers:",cubed_nums)
divisble_by_3 = list(filter(lambda x:x % 3 == 0,nums))  #filter()
sum_nums = reduce(lambda a,b: a + b,nums)                #reduce()
print("Sum of numbers:",sum_nums)
av = sum_nums/len(nums)
print("average:",av)