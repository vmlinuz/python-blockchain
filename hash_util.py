import hashlib
import json


def hash_string_256(string):
    """Hashes a string using SHA256.

    Arguments:
        :string: The string which should be hashed.
    """
    return hashlib.sha256(string).hexdigest()


def hash_string_512(string):
    """Hashes a string using SHA3-512.

    Arguments:
        :string: The string which should be hashed.
    """
    return hashlib.sha3_512(string).hexdigest()


def hash_block(block):
    """Hashes a block and returns a string representation of it.

    Arguments:
        :block: The block that should be hashed.
    """
    return hash_string_512(json.dumps(block, sort_keys=True).encode())
