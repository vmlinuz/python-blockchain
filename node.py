from uuid import uuid4

from blockchain import Blockchain
from verification import Verification


class Node:
    def __init__(self):
        # self.id = str(uuid4())
        self.id = "Gyula"
        self.blockchain = Blockchain(self.id)

    def get_transaction_value(self):
        """Returns the input of the user (a new transaction amount) as a float."""
        tx_recepient = input("Enter the recepient of the transaction: ")
        tx_amount = float(input("Your transaction amount please: "))
        return tx_recepient, tx_amount

    def get_user_choice(self):
        """Prompts the user for its choice and return it."""
        user_input = input("Your choice: ")
        return user_input

    def print_blockchain_elements(self):
        """Output all blocks of the blockchain."""
        # Output the blockchain list to the console
        for block in self.blockchain.chain:
            print("Outputting Block")
            print(block)
        else:
            print("-" * 20)

    def listen_for_input(self):
        waiting_for_input = True
        # A while loop for the user input interface
        # It's a loop that exits once waiting_for_input becomes False or when break is called
        while waiting_for_input:
            print("Please choose")
            print("1: Add a new transaction value")
            print("2: Mine a new block")
            print("3: Output the blockchain blocks")
            print("4: Check open transaction validity")
            print("q: Quit")
            user_choice = self.get_user_choice()
            match user_choice:
                case "1":
                    recepient, amount = self.get_transaction_value()
                    if self.blockchain.add_transaction(
                        recepient, self.id, amount=amount
                    ):
                        print("Added transaction!")
                    else:
                        print("Transaction failed!")
                    print(self.blockchain.open_transactions)
                case "2":
                    self.blockchain.mine_block()
                case "3":
                    self.print_blockchain_elements()
                case "4":
                    verifier = Verification()
                    if verifier.verify_open_transactions(
                        self.blockchain.open_transactions, self.blockchain.get_balance
                    ):
                        print("All transactions are valid!")
                    else:
                        print("There are invalid transactions!")
                case "q":
                    # This will lead to the loop to exist because it's running condition becomes False
                    waiting_for_input = False
                case _:
                    print("Input was invalid, please pick a value from the list!")
            verifier = Verification()
            if not verifier.verify_chain(self.blockchain.chain):
                self.print_blockchain_elements()
                print("Invalid blockchain!")
                # Break out of the loop
                waiting_for_input = False
            print(f"Balance of {self.id} is {self.blockchain.get_balance():6.2f}")


node = Node()
node.listen_for_input()
