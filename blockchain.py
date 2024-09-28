import hashlib
import uuid
from helperfunctions import *
import json
import requests
from helperstructs import *
import db
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from pqcrypto.sign.dilithium4 import generate_keypair, sign, verify

# Local Server
# base_url = "http://127.0.0.1:8000/"
# Aws Server
base_url = "http://18.218.172.21:8000/"

engine = create_engine("sqlite:///blockchain.db")
Session = sessionmaker(bind=engine)
session = Session()


class Block:
    def __init__(self):
        self.hash = ""
        self.prev_block_hash = ""


class Transaction:
    def __init__(self, sender_id, sender_pub_key, receiver_pub_key, amount, trxn_id=0):
        self.sender_id = sender_id
        self.trxn_uuid = uuid.uuid4()
        self.sender_pub_key = sender_pub_key
        self.receiver_pub_key = receiver_pub_key
        self.amount = amount
        self.trxn_hash = ""
        self.trxn_signature = ""
        self.trxn_id = trxn_id

    def print(self):
        """Displays Transaction data."""
        print(f"""\n
Transaction UUID: {self.trxn_uuid},
Sender Public Key: {self.sender_pub_key[:100]}....,
Receiver Public Key: {self.receiver_pub_key[:100]}....,
Transaction Amount: {self.amount},
Transaction Hash: {self.trxn_hash},
Transaction Signature: {self.trxn_signature[:100]}....,\n
""")

    def as_dict_for_json(self):
        """Returns transaction data as dictionary (intended for each conversion in json)"""
        return ({
            "sender_id": self.sender_id,
            "trxn_uuid": str(self.trxn_uuid),
            "sender_pub_key": self.sender_pub_key,
            "receiver_pub_key": self.receiver_pub_key,
            "amount": self.amount,
            "trxn_hash": self.trxn_hash,
            "trxn_signature": self.trxn_signature
        })


class BlockChain:
    def mine_block(self, miner_id):
        """Retrieves pending transactions from the server,
        verifies them, creates block and sends block to the
        server.
        """
        # Get pending transactions from the server
        resp = requests.get(f"{base_url}postquantum/transactions/pending/")
        pending_transactions_list = resp.json()

        pending_transactions_from_server = []
        # For each pending transaction, create a Transaction object, and add it to the
        # list of pending transactions retrieved from the server
        for transaction_data in pending_transactions_list:
            pending_transaction = Transaction(sender_id=transaction_data.get("sender_id"),
                                              sender_pub_key=transaction_data.get("sender_pub_key"),
                                              receiver_pub_key=transaction_data.get("receiver_pub_key"),
                                              amount=transaction_data.get("amount"))
            pending_transaction.trxn_uuid = transaction_data.get("trxn_uuid")
            pending_transaction.trxn_hash = transaction_data.get("trxn_hash")
            pending_transaction.trxn_signature = transaction_data.get("trxn_signature")
            pending_transactions_from_server.append(pending_transaction)

        verified_transaction = []
        # Only add verified transactions to the verified transactions list
        for trxn in pending_transactions_from_server:
            if self.verify_transaction(trxn):
                verified_transaction.append(trxn)

        # if the list of verified transactions aren't empty
        # hash their uuid, get the current last block's hash
        # concatenate them all together, hash the result and use it as the current blocks hash
        if verified_transaction:
            all_transactions_hashes_as_str = "".join([trxn.trxn_hash for trxn in verified_transaction])
            previous_block_hash = session.query(db.Block).order_by(desc(db.Block.id)).first().hash
            new_block_hash_ingest = all_transactions_hashes_as_str + previous_block_hash
            new_block_hash = hashlib.sha256((bytes(new_block_hash_ingest, 'utf-8'))).hexdigest()

            # Construct a payload to be sent to the broadcasting server
            payload = {
                "hash": new_block_hash,
                "previous_block_hash": previous_block_hash,
                "transactions": [trxn.as_dict_for_json() for trxn in verified_transaction],
                "miner_id": miner_id
            }

            payload = json.dumps(payload)

            # Send the payload to the broadcasting server
            headers = {"Content-type": "application/json"}
            resp = requests.post(f"{base_url}postquantum/blocks/new/", data=payload, headers=headers)
        else:
            print("Unable to verify any of the transactions")

    @staticmethod
    def verify_transaction(transaction: Transaction) -> bool:
        # By default, we assume that the transactions are valid
        transaction_is_valid: bool = True

        # Checks that the sender has the necessary funds to make this transaction
        resp = requests.get(f"{base_url}postquantum/wallets/balance/{transaction.sender_id}/")
        sender_balance = resp.json().get("wallet_balance")
        # Checks that the transaction amount is valid
        if sender_balance < transaction.amount or transaction.amount < 0:
            transaction_is_valid = False
            print("Invalid Transaction Amount!")

        # Check that the transaction was signed with the proper credentials
        transaction_is_valid = verify(b64_to_binary(transaction.sender_pub_key),
                                      bytes(transaction.trxn_hash, 'utf-8'),
                                      b64_to_binary(transaction.trxn_signature))


        return transaction_is_valid


    def get_and_verify_current_block_chain_state(self):
        """Updates the state of local nodes"""
        # Get the last blocks ID
        last_block_id = session.query(db.Block).order_by(desc(db.Block.id)).first().id
        # Get the not synced blocks from the server
        all_blocks_list = requests.get(f"{base_url}postquantum/blocks/after/{last_block_id}/")
        all_blocks_list = all_blocks_list.json()
        all_blocks = []
        # for each block, serialize its data
        for block_data in all_blocks_list:
            block_obj = db.Block(id=block_data.get("id"), hash=block_data.get("hash"),
                                 prev_block_hash=block_data.get("prev_block_hash"))
            single_block = BlockStruct(block_data.get("id"), block_data.get("hash"), block_data.get("prev_block_hash"))

            # Get each blocks transactions
            all_block_transactions_data = requests.get(f"{base_url}postquantum/blocks/{block_obj.id}/transactions/")
            all_block_transactions_data = all_block_transactions_data.json()
            all_block_transactions_are_valid = True
            serialized_transactions = []
            # Verify each of the transactions in the block
            for trxn_data in all_block_transactions_data:
                trxn = Transaction(sender_id=trxn_data.get("sender_id"), sender_pub_key=trxn_data.get("sender_pub_key"),
                                   receiver_pub_key=trxn_data.get("receiver_pub_key"), amount=trxn_data.get("amount"),
                                   trxn_id=trxn_data.get("id"))
                trxn.trxn_uuid = trxn_data.get("trxn_uuid"),
                trxn.trxn_hash = trxn_data.get("trxn_hash"),
                # For some reason, the trxn hash and trxn uuid comes in as a tuple with one element, the actual
                # trxn hash, As a result, we must parse it out.
                trxn.trxn_uuid = trxn.trxn_uuid[0]
                trxn.trxn_hash = trxn.trxn_hash[0]
                trxn.trxn_signature = trxn_data.get("trxn_signature")
                trxn.print()
                serialized_transactions.append(trxn)
                if not (self.verify_transaction(trxn)):
                    all_block_transactions_are_valid = False
                    print(f"transaction {trxn.trxn_uuid} not valid")

            # If all the transactions in a block are valid, create a new block and create all of its transactions
            if all_block_transactions_are_valid:
                new_block = db.Block(id=block_obj.id, hash=block_obj.hash, prev_block_hash=block_obj.prev_block_hash)
                session.add(new_block)
                for trxn in serialized_transactions:
                    trxn_to_save = db.Transaction(id=trxn.trxn_id, sender_id=trxn.sender_id, trxn_uuid=trxn.trxn_uuid,
                                                  sender_pub_key=trxn.sender_pub_key,
                                                  receiver_pub_key=trxn.receiver_pub_key, amount=trxn.amount,
                                                  trxn_hash=trxn.trxn_hash, trxn_signature=trxn.trxn_signature,
                                                  parent_block_id=block_obj.id, status=db.StatusEnum.verified)

                    session.add(trxn_to_save)

                all_trxn_uuids = "".join([trxn.trxn_hash for trxn in serialized_transactions])
                all_trxn_uuids += block_obj.prev_block_hash
                session.commit()
            else:
                print("Unable to verify block")

    @staticmethod
    def print_current_chain_sate():
        """Displays the current state of the blockchain"""
        all_blocks = session.query(db.Block).all()
        for block in all_blocks:
            print("---------------------------------------------------------------------------------------------------")
            print()
            print(f"\t\t\t\t\tBlock: {block.id}")
            print(f"Block ID: {block.id} \nBlock Hash: {block.hash} \nPrev Block Hash: {block.prev_block_hash}")
            print()
            print()
            print("\t\t\t\t\tBlock Transactons")
            all_block_transactions = session.query(db.Transaction).filter_by(parent_block=block)
            for trxn in all_block_transactions:
                print()
                print(f"\tTransaction ID: {trxn.id}, \n\tTransaction UUID: {trxn.trxn_uuid},"
                      f"\n\tTransaction Hash: {trxn.trxn_hash}")
                print()
            print("---------------------------------------------------------------------------------------------------")

    def verify_block(self, block_id):
        """Verifies Blocks"""
        all_block_transactions_data = requests.get(f"{base_url}postquantum/blocks/{block_id}/transactions/")
        all_block_transactions_data = all_block_transactions_data.json()
        all_block_transactions_are_valid = True
        serialized_transactions = []
        for trxn_data in all_block_transactions_data:
            trxn = Transaction(trxn_data.get("sender_id"), trxn_data.get("sender_pub_key"),
                               trxn_data.get("receiver_pub_key"), trxn_data.get("amount"))
            trxn.trxn_uuid = trxn_data.get("trxn_uuid"),
            trxn.trxn_hash = trxn_data.get("trxn_hash"),
            # For some reason, the trxn hash comes in as a tuple with one element, the actual trxn hash
            # As a result, we must parse it out.
            trxn.trxn_hash = trxn.trxn_hash[0]
            trxn.trxn_signature = trxn_data.get("trxn_signature")
            serialized_transactions.append(trxn)
            if not(self.verify_transaction(trxn)):
                all_block_transactions_are_valid = False
                print(f"transaction {trxn.trxn_uuid} not valid")
        return all_block_transactions_are_valid

    @staticmethod
    def get_pending_transactions():
        # Get pending transactions from the server
        resp = requests.get(f"{base_url}postquantum/transactions/pending/")
        pending_transactions_list = resp.json()

        pending_transactions_from_server = []
        # For each pending transaction, create a Transaction object, and add it to the
        # list of pending transactions retrieved from the server
        for transaction_data in pending_transactions_list:
            pending_transaction = Transaction(sender_id=transaction_data.get("sender_id"),
                                              sender_pub_key=transaction_data.get("sender_pub_key"),
                                              receiver_pub_key=transaction_data.get("receiver_pub_key"),
                                              amount=transaction_data.get("amount"))
            pending_transaction.trxn_uuid = transaction_data.get("trxn_uuid")
            pending_transaction.trxn_hash = transaction_data.get("trxn_hash")
            pending_transaction.trxn_signature = transaction_data.get("trxn_signature")
            pending_transactions_from_server.append(pending_transaction)
        print("---------------------------------------------------------------------------------------------------")
        print("\t\t\t\t\tPending Transactons")
        for trxn in pending_transactions_from_server:
            trxn.print()
        print("---------------------------------------------------------------------------------------------------")


class Wallet:
    def __init__(self, wallet_id, name, private_key="", public_key=""):
        self.wallet_id = wallet_id
        self.name = name
        if private_key and public_key:
            self.private_key = private_key
            self.public_key = public_key
        else:
            self.public_key, self.private_key = generate_keypair()

            # convert key pair from binary to base64
            self.private_key = binary_to_b64(self.private_key)
            self.public_key = binary_to_b64(self.public_key)

        # Modify this to fetch the balance from the relay server or database
        self.balance = 1000

    def get_wallet_balance(self):
        """Retrieves the wallet's balance"""
        resp = requests.get(f"{base_url}postquantum/wallets/balance/{self.wallet_id}/")
        wallet_balance = resp.json().get("wallet_balance")
        return int(wallet_balance)

    def make_transaction(self, receiver_pub_key, amount):
        """Creates new transaction and broadcasts it to the server"""
        transaction = Transaction(self.wallet_id, self.public_key, receiver_pub_key, amount)
        transaction.trxn_hash = Wallet.generate_transaction_hash(transaction)
        transaction.trxn_signature = self.sign_transaction(transaction)

        # Sending the transaction to the broadcasting server
        headers = {"Content-type": "application/json"}

        transaction.trxn_signature = binary_to_b64(transaction.trxn_signature)
        payload = json.dumps(transaction.as_dict_for_json())
        requests.post(f"{base_url}postquantum/transactions/new/", data=payload, headers=headers)

    @staticmethod
    def generate_transaction_hash(transaction: Transaction) -> str:
        """Generates transaction hash"""
        transaction_string = f"id:{transaction.trxn_uuid}-sndrpk:{transaction.sender_pub_key}-" \
                             f"rcvrpk{transaction.sender_pub_key}-amt{transaction.amount}"
        transaction_string_as_bytes = bytes(transaction_string, 'utf-8')
        return hashlib.sha256(transaction_string_as_bytes).hexdigest()

    def sign_transaction(self, transaction: Transaction) -> bytes:
        """Generates transaction signature"""
        transaction_signature = sign(b64_to_binary(self.private_key), bytes(transaction.trxn_hash, "utf-8"))
        return transaction_signature







