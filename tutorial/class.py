class MyClass:
    x=5

print (MyClass)
p1 = MyClass()
print (p1.x)
del p1
#print (p1.x)    # error

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

p1 = Person("Emil", 36)

print (p1.name)
print (p1.age)

