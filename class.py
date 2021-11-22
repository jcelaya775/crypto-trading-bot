class Dog:
    num = 30

    def __init__(self, age):  # constructor
        self.color = None
        self.age = age

    def something():  # static method
        print(Dog.num)


def main():
    my_dog = Dog(13)
    print(my_dog.age)
    Dog.something()


main()
