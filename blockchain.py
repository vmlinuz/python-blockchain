import functools
import json
import pickle

from block import Block
from hash_util import hash_block
from transaction import Transaction
from verification import Verification

# The reward we give to miners (for creating a new block)
MINING_REWARD = 10

blockchain_file_text = "blockchain.txt"
blockchain_file_pickle = "blockchain.pickle"


class Blockchain:
    def __init__(self, hosting_node_id):
        # Our starting block for the blockchain
        genesis_block = Block(0, "", [], 100, 0)
        # Initializing our (empty) blockchain list
        self.__chain = [genesis_block]
        # Unhandled transactions
        self.__open_transactions = []
        self.load_data_json()
        self.hosting_node = hosting_node_id

    @property
    def chain(self):
        """Returns a copy of the blockchain list."""
        return self.__chain[:]

    @chain.setter
    def chain(self, val):
        """The chain is immutable from outside the class."""
        pass

    @property
    def open_transactions(self):
        """Returns a copy of the open transactions list."""
        return self.__open_transactions[:]

    @open_transactions.setter
    def open_transactions(self, val):
        """The open_transactions is immutable from outside the class."""
        pass

    def load_data_json(self):
        """Initializes blockchain + open transactions data from a file."""
        try:
            with open(blockchain_file_text, mode="r") as f:
                file_content = f.readlines()
                orig_blockchain = json.loads(file_content[0][:-1])
                orig_open_transactions = json.loads(file_content[1])
                updated_blockchain = []
                for block in orig_blockchain:
                    converted_trasactions = [
                        Transaction(
                            tx["sender"],
                            tx["recipient"],
                            tx["amount"],
                        )
                        for tx in block["transactions"]
                    ]
                    updated_block = Block(
                        block["index"],
                        block["previous_hash"],
                        converted_trasactions,
                        block["proof"],
                        block["timestamp"],
                    )
                    updated_blockchain.append(updated_block)
                self.__chain = updated_blockchain
                updated_transactions = []
                for tx in orig_open_transactions:
                    updated_transaction = Transaction(
                        tx["sender"],
                        tx["recipient"],
                        tx["amount"],
                    )
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
        except (IOError, IndexError) as e:
            print(f"Exception accessing file {blockchain_file_text} encountered: {e}")

    def load_data_pickle(self):
        """Initializes blockchain + open transactions data from a file."""
        try:
            with open(blockchain_file_pickle, mode="rb") as f:
                file_content = pickle.loads(f.read())
                self.__chain = file_content["blockchain"]
                self.__open_transactions = file_content["open_transactions"]
        except (IOError, IndexError) as e:
            print(f"Exception accessing file {blockchain_file_pickle} encountered: {e}")

    def save_data_json(self):
        """Saves blockchain + open transactions snapshot to a file."""
        try:
            with open(blockchain_file_text, mode="w") as f:
                saveable_blockchain = [
                    block.__dict__
                    for block in [
                        Block(
                            block_el.index,
                            block_el.previous_hash,
                            [tx.__dict__ for tx in block_el.transactions],
                            block_el.proof,
                            block_el.timestamp,
                        )
                        for block_el in self.__chain
                    ]
                ]
                f.write(json.dumps(saveable_blockchain))
                f.write("\n")
                saveable_transactions = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_transactions))
        except IOError as e:
            print(f"Saving file {blockchain_file_text} failed: {e}")

    def save_data_pickle(self):
        """Saves blockchain + open transactions snapshot to a file."""
        try:
            with open(blockchain_file_pickle, mode="wb") as f:
                save_data = {
                    "blockchain": self.__chain,
                    "open_transactions": self.__open_transactions,
                }
                f.write(pickle.dumps(save_data))
        except IOError as e:
            print(f"Saving file {blockchain_file_pickle} failed: {e}")

    def proof_of_work(self):
        """Generate a proof of work for the open transactions, the hash of the previous block and a random number
        (which is guessed until it fits).
        """
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        # Try different PoW numbers and return the first valid one
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self):
        """Calculate and return the balance for a participant."""
        participant = self.hosting_node
        # Fetch a list of all sent coin amounts for the given person (empty lists are returned if the person was NOT the
        # sender) This fetches sent amounts of transactions that were already included in blocks of the blockchain
        tx_sender = [
            [tx.amount for tx in block.transactions if tx.sender == participant]
            for block in self.__chain
        ]
        # Fetch a list of all sent coin amounts for the given person (empty lists are returned if the person was NOT the
        # sender) This fetches sent amounts of open transactions (to avoid double spending)
        open_tx_sender = [
            tx.amount for tx in self.__open_transactions if tx.sender == participant
        ]
        tx_sender.append(open_tx_sender)
        amount_sent = functools.reduce(
            lambda tx_sum, tx_amount: tx_sum + sum(tx_amount)
            if len(tx_amount) > 0
            else tx_sum,
            tx_sender,
            0,
        )
        # This fetches received coin amounts of transactions that were already included in blocks of the blockchain We
        # ignore open transactions here because you shouldn't be able to spend coins before the transaction was confirmed
        # + included in a block
        tx_recipient = [
            [tx.amount for tx in block.transactions if tx.recipient == participant]
            for block in self.__chain
        ]
        amount_received = functools.reduce(
            lambda tx_sum, tx_amount: tx_sum + sum(tx_amount)
            if len(tx_amount) > 0
            else tx_sum,
            tx_recipient,
            0,
        )
        # Return the total balance
        return amount_received - amount_sent

    def get_last_blockchain_value(self):
        """Returns the last value of the current blockchain."""
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def add_transaction(self, recipient, sender, amount=1.0):
        """Append a new value as well as the last blockchain value to the blockchain

        Arguments:
            :sender: The sender of the coins.
            :recipient: The recipient of the coins.
            :amount: The amount of coins sent with the transaction (default = 1.0)
        """
        # transaction = {
        #     "sender": sender,
        #     "recipient": recipient,
        #     "amount": amount
        # }
        transaction = Transaction(sender, recipient, amount)
        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data_json()
            return True
        return False

    def mine_block(self):
        """Create a new block and add open transactions to it."""
        # Fetch the currently last block of the blockchain
        last_block = self.get_last_blockchain_value()
        # Hash the last block (=> to be able to compare it to the stored hash value)
        hashed_block = hash_block(last_block)
        proof = self.proof_of_work()
        # Miners should be rewarded, so let's create a reward transaction
        reward_transaction = Transaction("MINING", self.hosting_node, MINING_REWARD)
        # Copy transaction instead of manipulating the original open_transactions list
        # This ensures that if for some reason the mining should fail, we don't have the reward transaction stored in the
        copied_open_transactions = self.__open_transactions[:]
        copied_open_transactions.append(reward_transaction)
        block = Block(
            len(self.__chain),
            hashed_block,
            copied_open_transactions,
            proof,
        )
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data_json()
        return True
