from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, Integer, DateTime, func

@as_declarative()
class Base:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() 