from sqlalchemy import Column, String
from app.db.oracle import Base

class Lval(Base):
    __tablename__ = "LVAL"
    __table_args__ = {"schema": "ACSELD"}

    tipolval = Column("TIPOLVAL", String(8), primary_key=True)
    codlval  = Column("CODLVAL", String(100), primary_key=True)
    descrip  = Column("DESCRIP", String(150))
    desclong = Column("DESCLONG", String(2000))
    stslval  = Column("STSLVAL", String(3))