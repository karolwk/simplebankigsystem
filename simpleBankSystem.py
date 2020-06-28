import random
import sqlite3

conn = sqlite3.connect('card.s3db')
cur = conn.cursor()

class Account:
    def __init__(self, conn_, cursor_):
        self.conn = conn_
        self.cursor = cursor_
        self.card_number = ""
        self.pin = ""
        self.balance = 0
        self.state_main_menu = {0: "Exit", 1: "Create an account", 2: "Log into account"}
        self.state_logged = {0: "Exit", 1: "Balance", 2: "Add income",
                             3: "Do transfer", 4: "Close account", 5: "Log out"}
        self.exit = False

    def add_income(self) -> None:
        # Adding income to database
        bal_to_add = int(input("Enter income: "))
        self.balance += bal_to_add
        self.update_database(bal_to_add, self.card_number)
        print("Income was added!")

    def add_card_database(self) -> None:

        self.cursor.execute('CREATE TABLE IF NOT EXISTS card (id INTEGER PRIMARY KEY AUTOINCREMENT,'
                            'number TEXT,'
                            'pin TEXT,'
                            'balance INTEGER DEFAULT 0 )')
        self.cursor.execute('INSERT INTO card (number, pin) VALUES (?,?)',
                            (self.card_number, self.pin))
        self.conn.commit()

    def close_account(self):
        self.cursor.execute('DELETE FROM card WHERE number = ?', (self.card_number,))
        self.conn.commit()
        self.card_number = None
        self.pin = None
        print('Account closed!')

    def check_card_in_database(self, card: str) -> bool:
        self.cursor.execute('SELECT number FROM card WHERE number = ?', (card,))
        if self.cursor.fetchone() is None:
            return False
        else:
            return True

    def check_pin_in_database(self, pin: str, card: str) -> bool:
        self.cursor.execute('SELECT * FROM card WHERE pin = ? AND number = ?', (pin, card))
        if self.cursor.fetchone() is None:
            return False
        else:
            return True

    def update_database(self, balance: int, card_number: str) -> None:
        # Update balance for specified card number
        self.cursor.execute('UPDATE card SET balance = balance + ? WHERE number = ?', (balance, card_number))
        self.conn.commit()

    def do_transfer(self):
        card_to_transfer = input("Enter card number: \n")
        # Verifying checksum and card length
        if (list(card_to_transfer)[-1] == self.luhn_algorithm(list(card_to_transfer[:len(card_to_transfer) - 1]))) and \
                len(card_to_transfer) == 16:
            if card_to_transfer != self.card_number:
                if self.check_card_in_database(card_to_transfer):
                    money_to_transfer = abs(int(input("Enter how much money you want to transfer: \n")))
                    if money_to_transfer <= self.balance:
                        self.balance -= money_to_transfer
                        self.update_database(-money_to_transfer, self.card_number)
                        self.update_database(money_to_transfer, card_to_transfer)
                        print("Success!")
                    else:
                        print("Not enough money!")
                else:
                    print("Such a card does not exist.")
            else:
                print("You can't transfer money to the same account!")
        else:
            print("Probably you made mistake in the card number. Please try again!")

    @staticmethod
    def luhn_algorithm(card: list) -> str:
        #  Generates checksum for card number
        card_temp = [int(x) for x in card]
        for i in range(0, len(card_temp), 2):
            card_temp[i] *= 2
            if card_temp[i] > 9:
                card_temp[i] -= 9
        if sum(card_temp) % 10 == 0:
            checksum = 0
        else:
            checksum = 10 - (sum(card_temp) % 10)
        return str(checksum)

    def operate_menu(self) -> None:
        while not self.exit:
            self.print_menu(self.state_main_menu)
            menu_number = input()
            if menu_number == "0":
                self.exit = True
            elif menu_number == "1":
                self.create_account()
            elif menu_number == "2":
                self.login()

    @staticmethod
    def print_menu(menu: dict) -> None:
        for x in range(1, len(menu)):
            print(f"{x}. {menu[x]}")
        print(f"0. {menu[0]}")

    def create_account(self) -> None:
        # Generating random card number with proper checksum
        card_n = list("".join(["400000", str(random.randint(0, 999999999)).zfill(9)]))
        self.card_number = "".join(card_n) + self.luhn_algorithm(card_n)
        #  splitting string to 4 equal parts only for string
        #  parts = [self.card_number[i:i+4] for i in range(0, len(self.card_number), 4)]
        self.pin = "".join(str(random.randint(0, 9999)).zfill(4))
        self.add_card_database()
        print(f"""
Your card has been created
Your card number:
{self.card_number}
Your card PIN:
{self.pin}
""")

    def login(self) -> None:
        # Login system, if pin and card numbers are correct then show account menu
        user_input_ = input("Enter your card number:\n")
        if self.check_card_in_database(user_input_):
            self.card_number = user_input_
            user_input_ = input("Enter your PIN:\n")
            if self.check_pin_in_database(user_input_, self.card_number):
                self.pin = user_input_
                self.cursor.execute('SELECT balance FROM card WHERE pin = ? AND number = ?',
                                    (self.pin, self.card_number))
                self.balance = self.cursor.fetchone()[0]
                print("You have successfully logged in!")
                while True:
                    self.print_menu(self.state_logged)
                    user_input_ = input()
                    if user_input_ == "1":
                        print(f"Balance: {self.balance}")
                    elif user_input_ == "2":
                        self.add_income()
                    elif user_input_ == "3":
                        self.do_transfer()
                    elif user_input_ == "4":
                        self.close_account()
                        break
                    elif user_input_ == "5":
                        break
                    elif user_input_ == "0":
                        self.exit = True
                        break
                    else:
                        print(f"Use numbers from 0 - {len(self.state_logged) - 1}")
            else:
                print("Wrong card number or PIN!\n")

        else:
            print("Wrong card number or PIN!\n")


account = Account(conn, cur)
account.operate_menu()
