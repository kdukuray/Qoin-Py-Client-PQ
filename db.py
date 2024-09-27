from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from enum import Enum as PyEnum
import os

Base = declarative_base()


# Choices equivalent in SQLAlchemy using Enum
class StatusEnum(PyEnum):
    pending = "pending"
    verified = "verified"


class Block(Base):
    __tablename__ = 'block'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(String(200), nullable=False)
    prev_block_hash = Column(String(200), nullable=False)


class Transaction(Base):
    __tablename__ = 'transaction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, nullable=False)
    trxn_uuid = Column(String(200), nullable=False)
    sender_pub_key = Column(Text, nullable=False)
    receiver_pub_key = Column(Text, nullable=False)
    amount = Column(Integer, nullable=False)
    trxn_hash = Column(String(200), nullable=False)
    trxn_signature = Column(Text, nullable=False)
    parent_block_id = Column(Integer, ForeignKey('block.id'), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)

    parent_block = relationship("Block", back_populates="transactions")


Block.transactions = relationship("Transaction", order_by=Transaction.id, back_populates="parent_block")


class Wallet(Base):
    __tablename__ = 'wallet'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, default='John Doe')
    private_key = Column(Text, nullable=False)
    public_key = Column(Text, nullable=False)
    balance = Column(Integer, nullable=False)


# Whenever a new node is created along with its local database,
# a genesis block must also be created. The following code snippet
# ensures that the genesis block is created.

db_file = "blockchain.db"
# Check if the database file exists
if not os.path.exists(db_file):
    # If the database file doesn't exist, run db.py to create it
    print("Database not found. Creating a new database...")
    engine = create_engine("sqlite:///blockchain.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    genesis_block = Block(hash="GenesisBlock", prev_block_hash='GenesisBlock')
    session.add(genesis_block)
    session.commit()

else:
    print("Database found. Connecting to the database...")

