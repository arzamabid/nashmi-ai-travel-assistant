from db.models import (
    availability,  # noqa: F401
    inventory,  # noqa: F401
)
from db.models.base import Base
from db.session import engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("NASHMI database tables created successfully.")
