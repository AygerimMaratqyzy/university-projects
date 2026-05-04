from datetime import datetime,timedelta      #1
x = datetime.now() - timedelta(days=5)
print(x)

n = datetime.now()                             #2
print((n - timedelta(days=1)).strftime("%A"))
print(n.strftime("%A"))
print((n + timedelta(days=1)).strftime("%A"))

print(n.replace(microsecond=0))               #3

d1 = datetime.strptime(input(),"%Y-%m-%d %H:%M:%S")     #4
d2 = datetime.strptime(input(),"%Y-%m-%d %H:%M:%S")

diff_seconds = int((d2 - d1).total_seconds())
print(diff_seconds)