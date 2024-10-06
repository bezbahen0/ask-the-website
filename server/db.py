import datetime

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import TIMESTAMP, Column, Integer, String

from server.constants import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base = declarative_base()
metadata = MetaData()
engine = create_engine(DATABASE_URL)


class Messages(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    chat_id = Column(String, nullable=False)
    url = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    role = Column(String, nullable=False)
    message = Column(String, nullable=False)
    model_name = Column(String, nullable=True)
    rating = Column(Integer, nullable=True)
    service_comments = Column(String, nullable=True)
    version = Column(String, nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)


def add_message(
    user_id: int,
    chat_id: str,
    url: str,
    file_type: str,
    role: str,
    message: str,
    model_name: str,
    service_comments: str,
    version: str,
):
    with Session(engine) as session:
        message = Messages(
            user_id=user_id,
            chat_id=chat_id,
            url=url,
            file_type=file_type,
            role=role,
            message=message,
            model_name=model_name,
            service_comments=service_comments,
            version=version,
        )
        session.add(message)
        session.commit()
        session.flush()
        session.refresh(message)
    return message.id


def update_message_text(message_id: int, message: str):
    with Session(engine) as session:
        session.query(Messages).filter(Messages.id == message_id).update(
            {
                "message": message,
            }
        )
        session.commit()


def update_message_rating(message_id: int, rating: int = 0):
    with Session(engine) as session:
        session.query(Messages).filter(Messages.id == message_id).update(
            {"rating": rating}
        )
        session.commit()


def get_message_score(message_id: int):
    with Session(engine) as session:
        message = session.query(Messages).filter_by(id=message_id).first()
        return message


def get_chat_messages(chat_id: int):
    with Session(engine) as session:
        message = session.query(Messages).filter_by(chat_id=chat_id).order_by("id").all()
        return message


def update_message(message_id: int, message: str, rating: int = 0):
    with Session(engine) as session:
        session.query(Messages).filter(Messages.id == message_id).update(
            {"message": message, "rating": rating}
        )
        session.commit()


def add_rating(user_id: int, message: str, rating: int):
    with Session(engine) as session:
        rating = Messages(user_id=user_id, message=message, rating=rating)
        session.add(rating)
        session.commit()


if __name__ == "__main__":
    add_message(
        1,
        "test_chat",
        "null",
        "none type",
        "user",
        "just test message",
        "no model",
        "no service",
        "0.2.6",
    )
