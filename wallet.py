import binascii

import Crypto.Random
from Crypto.Hash import SHA3_512
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


class Wallet:
    def __init__(self, node_id):
        self.private_key = None
        self.public_key = None
        self.wallet_file = f"wallet-{node_id}.txt"

    def create_keys(self):
        self.private_key, self.public_key = self.generate_keys()
        print(
            f"Public key is {self.public_key}\n\nPrivate key is {self.private_key}\n\n"
        )

    def save_keys(self):
        """Saves the keys to a file (wallet.txt)."""
        if self.public_key is not None and self.private_key is not None:
            try:
                with open(self.wallet_file, mode="w") as f:
                    f.write(self.private_key)
                    f.write("\n")
                    f.write(self.public_key)
                return True
            except (IOError, IndexError):
                print("Saving wallet failed...")
                return False

    def load_keys(self):
        """Loads the keys from the wallet.txt file into the wallet."""
        try:
            with open(self.wallet_file, mode="r") as f:
                keys = f.readlines()
                self.private_key = keys[0][:-1]
                self.public_key = keys[1]
            return True
        except (IOError, IndexError):
            print("Loading wallet failed...")
            return False

    @staticmethod
    def generate_keys():
        private_key = RSA.generate(1024, Crypto.Random.new().read)
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
