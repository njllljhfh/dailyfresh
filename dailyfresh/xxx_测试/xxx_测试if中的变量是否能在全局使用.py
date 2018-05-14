a = {'a': 1}
if True:
    a['b'] = 2

print(a)

b = 1
print(id(b))
if True:
    b = 2
print(id(b))
print(b)
