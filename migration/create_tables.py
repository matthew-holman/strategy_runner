from sqlmodel import SQLModel

from app.db.db import Base, engine

# Import the DB models to create the tables

if __name__ == "__main__":
    # if config.TARGET_ENV != "local-dev":
    #     raise Exception("This script is for only local development!")

    Base.metadata.bind = engine.connect()
    SQLModel.metadata.create_all(engine)  # create tables in local
