thelist = ["apple", "banana", "cherry"]
for x in thelist:
    print(x)

for i in range(len(thelist)):
    print(i)

for i in range(len(thelist)):
    print(thelist[i])

thislist = ["orange", "mango", "kiwi", "pineapple", "banana"]
thislist.sort()
print(thislist)

thislist = [100, 50, 65, 82, 23]
thislist.sort()
print(thislist)

print ("copy list-----------------------------")
thislist = ["apple", "banana", "cherry"]
mylist = thislist.copy()
print(mylist)

mylist[0] = "MANGO"
print (mylist)
print (thislist)

yourlist = list(thislist)
print (yourlist)
