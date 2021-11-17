'''
input =
shop items sold = bread = 16 , butter = 21, tea bags = 55, coffee = 26, Paav = 12
add this data in dic. by user.
access different elements and add new element named cake=6 and cold drink = 11
'''
k=[x for x in input("Enter the list items : ").split( )]

shop_items={}
for items in k:
	print("Enter Value for shopping item",items)
	shop_items[items]=input()
	print(shop_items)


print(shop_items.keys())
print(shop_items.values())

print("Your maximum quantity in list is : ", max(shop_items.values()) + " is of item ", max(shop_items, key=shop_items.get))
print("Your minimum quantity in list is : ", min(shop_items.values()) + "is of item ", min(shop_items, key=shop_items.get))

x=input("Enter Item Name: ")
print(shop_items.get(x))

extra=[x for x in input("Enter the list items : ").split( )]
for items in extra:
	print("Enter Value for extra shopping list",items)
	shop_items[items]=input()
	print(shop_items)