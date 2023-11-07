"""Defines the Block class, which represents a single block in the blockchain."""

from time import time

from utility.printable import Printable


class Block(Printable):
    """A single block of our blockchain.
    Attributes:
        :index: The index of this block.
        :previous_hash: The hash of the previous block in the chain which this block is part of.
        :transactions: A list of transactions.
        :proof: The proof of work number that yielded this block.
        :timestamp: The timestamp of when this block was added to the blockchain.
    """

    def __init__(self, index, previous_hash, transactions, proof, timestamp=None):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.proof = proof
        self.timestamp = timestamp or time()
