import binascii

import Cryptodome.Random
from Cryptodome.PublicKey import RSA


class Wallet:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self._balance = 0

    def create_keys(self):
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key

    def save_keys(self):
        if self.public_key is not None and self.private_key is not None:
            try:
                with open("wallet.txt", mode="w") as f:
                    f.write(self.private_key)
                    f.write("\n")
                    f.write(self.public_key)
            except (IOError, IndexError):
                print("Saving wallet failed...")

    def load_keys(self):
        try:
            with open("wallet.txt", mode="r") as f:
                keys = f.readlines()
                self.public_key = keys[0][:-1]
                self.private_key = keys[1]
        except (IOError, IndexError):
            print("Loading wallet failed...")

    @staticmethod
    def generate_keys():
        private_key = RSA.generate(1024, Cryptodome.Random.new().read)
        public_key = private_key.publickey()
        return (
            binascii.hexlify(private_key.exportKey(format="DER")).decode("ascii"),
            binascii.hexlify(public_key.exportKey(format="DER")).decode("ascii"),
        )

    def deposit(self, amount):
        self._balance += amount

    def withdraw(self, amount):
        self._balance -= amount

    def get_balance(self):
        return self._balance
