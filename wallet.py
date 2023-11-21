import binascii

import Cryptodome.Random
from Cryptodome.Hash import SHA3_512
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import PKCS1_v1_5


class Wallet:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self._balance = 0

    def create_keys(self):
        self.private_key, self.public_key = self.generate_keys()
        print(
            f"Public key is {self.public_key}\n\nPrivate key is {self.private_key}\n\n"
        )

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
                self.private_key = keys[0][:-1]
                self.public_key = keys[1]
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

    def sign_transaction(self, sender, recipient, amount):
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        h = SHA3_512.new((str(sender) + str(recipient) + str(amount)).encode("utf8"))
        signature = signer.sign(h)
        return binascii.hexlify(signature).decode("ascii")

    @staticmethod
    def verify_transaction(transaction):
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA3_512.new(
            (
                str(transaction.sender)
                + str(transaction.recipient)
                + str(transaction.amount)
            ).encode("utf8")
        )
        return verifier.verify(h, binascii.unhexlify(transaction.signature))

    def deposit(self, amount):
        self._balance += amount

    def withdraw(self, amount):
        self._balance -= amount

    def get_balance(self):
        return self._balance
