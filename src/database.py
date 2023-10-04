from datetime import datetime
from peewee import SqliteDatabase, Model, FloatField
from peewee import UUIDField, TextField, DateTimeField, BooleanField, ForeignKeyField, FloatField, IntegerField
from uuid import uuid4

database = SqliteDatabase(database="database.db")

class BaseModel(Model):
    class Meta:
        database = database

class User(BaseModel):
    id         = UUIDField(unique=True, primary_key=True, default=uuid4)
    username   = TextField(unique=True)
    password   = TextField()
    blocked    = BooleanField(null=True, default=False)
    verified   = BooleanField(null=True, default=False)
    is_admin   = BooleanField(null=True, default=False)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

class Balance(BaseModel):
    user       = ForeignKeyField(User, backref='balances')
    balance    = FloatField(default=0)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
class Offer(BaseModel):
    offer_id   = TextField(unique=True, default=uuid4, primary_key=True)
    user       = ForeignKeyField(User, backref='offers')
    title      = TextField()
    text       = TextField()
    prize      = FloatField(default=0)
    settled    = BooleanField(default=False)   
    category   = TextField()
    expire_at  = DateTimeField(default=datetime.now)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
class Link(BaseModel):
    offer      = ForeignKeyField(Offer, backref='links')
    url        = TextField()
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
class Stakeholder(BaseModel):
    user       = ForeignKeyField(User, backref='stakeholders')
    offer      = ForeignKeyField(Offer, backref='stakeholders')
    day        = IntegerField(default=0)
    value      = FloatField(default=0)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
class Proposal(BaseModel):
    proposal_id = UUIDField(unique=True, primary_key=True, default=uuid4)
    user        = ForeignKeyField(User, backref='proposals')
    offer       = ForeignKeyField(Offer, backref='proposals')
    day         = IntegerField(default=0)
    created_at  = DateTimeField(default=datetime.now)
    updated_at  = DateTimeField(default=datetime.now)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
class ProposalVote(BaseModel):
    user       = ForeignKeyField(User, backref='proposal_votes')
    offer      = ForeignKeyField(Offer, backref='proposal_votes')
    proposal   = ForeignKeyField(Proposal, backref='proposal_votes')
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
database.create_tables([User, Balance, Offer, Link, Stakeholder, Proposal, ProposalVote])