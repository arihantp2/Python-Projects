name=input(" Enter Your Name: ")
print("Hello " + name + " Let's start the game")
print("Press Start to Start the game ")
while True:
    start=input("").lower()
    if start=="start":
        print('''Here's a question for you
who is the current captain of Indian Cricket Team?
Dhoni
Virat
Rohit''')
    else:
        print("Please enter 'Start' to begin with the game")
    break

guess=" "
while True:
    guess = input("Enter your guess \n").lower()

    if guess == "dhoni" :
        print("He was our ex captain")

    elif guess == "rohit" :
        print(" I am sure he will be leading team one day")

    elif guess == "virat" :
        print("Congrats! you have got it right !!")

        break

    else:
        print("Enter correct name")

