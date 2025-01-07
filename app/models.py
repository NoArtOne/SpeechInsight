from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    role = Column(String, default='user')
    transactions = relationship('TransactionHistory', back_populates='user')
    tasks = relationship('MLTask', back_populates='user')

    def register(self, username, password):
        self.username = username
        self.password = password

    def login(self, password):
        return self.password == password

    def add_balance(self, amount):
        self.balance += amount

    def get_balance(self):
        return self.balance

    def get_transaction_history(self):
        return self.transactions

class MLModel(Base):
    __tablename__ = 'ml_models'
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String, nullable=False)
    model_path = Column(String, nullable=False)

    def load_model(self):
        # Загрузка модели
        pass

    def predict(self, data):
        # Предсказание
        pass

class TransactionHistory(Base):
    __tablename__ = 'transaction_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    transaction_type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship('User', back_populates='transactions')

    def add_transaction(self, user_id, transaction_type, amount):
        self.user_id = user_id
        self.transaction_type = transaction_type
        self.amount = amount

    def get_transactions_by_user(self, user_id):
        return self.query.filter_by(user_id=user_id).all()

class MLTask(Base):
    __tablename__ = 'ml_tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_data = Column(String, nullable=False)
    status = Column(String, default='pending')
    result = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship('User', back_populates='tasks')

    def create_task(self, user_id, task_data):
        self.user_id = user_id
        self.task_data = task_data

    def update_status(self, status):
        self.status = status

    def get_task_result(self):
        return self.result
