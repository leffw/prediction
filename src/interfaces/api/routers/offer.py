from src.interfaces.api.middlewares.authorization import isAuthorization
from src.interfaces.api.schemas import CreateOfferSchema, ProposalDaySchema, ProposalVoteSchema, ReserveOfferSchema
from playhouse.shortcuts import model_to_dict
from src.database import Balance, Offer, Link, Proposal, ProposalVote, Stakeholder, User
from fastapi import APIRouter, HTTPException, Depends, Request

import datetime

router = APIRouter()

@router.post("/api/v1/offer/create")
def create_offer(data: CreateOfferSchema, request: Request = Depends(isAuthorization)):
    if (request.data["verified"] == False):
        raise HTTPException(401, "You cannot access this feature as your account has not been verified.")

    if (request.data["is_admin"] == True):
        raise HTTPException(401, "You cannot access this feature.")

    if not (data.expire_in_years):
        data.expire_in_years = 1
        
    expire_in_years = datetime.datetime.now()
    expire_in_years+= datetime.timedelta(days=365 * data.expire_in_years)

    offer = Offer.get_or_create(
        user=request.data["id"],
        title=data.title,
        text=data.text,
        category=data.category,
        expire_at=expire_in_years
    )[0]
    links = [{"offer": offer.offer_id, "url": url} for url in data.links]
    if (links):
        Link.insert_many(links).execute()

    return { "offer_id": offer.offer_id }

@router.get("/api/v1/offers")
def list_offers(page: int = 1, size: int = 15):
    if (size > 15):
        raise HTTPException(400, "Size cannot be greater than 15.")

    offers = []
    for offer in (Offer
                  .select(Offer.title, Offer.text, Offer.category, Offer.prize, Offer.offer_id, Offer.created_at, Offer.expire_at, Offer.updated_at)
                  .where(Offer.settled == False)
                  .order_by(Offer.created_at.desc())
                  .limit(15)
                  .paginate(page, size)):

        offer = model_to_dict(offer)
        del offer["user"]
        del offer["settled"]
        
        offer["links"] = []
        offer["created_at"] = str(offer["created_at"])
        offer["updated_at"] = str(offer["updated_at"])

        for link in Link.select(Link.url).where(Link.offer == offer["offer_id"]):
            offer["links"].append(link.url)
        
        offers.append(offer)

    return offers

@router.post("/api/v1/offer/reserve")
def offer_reserve(data: ReserveOfferSchema, request: Request = Depends(isAuthorization)):
    if (request.data["verified"] == False):
        raise HTTPException(401, "You cannot access this feature as your account has not been verified.")

    if (request.data["is_admin"] == True):
        raise HTTPException(401, "You cannot access this feature.")

    offer = Offer.select().where((Offer.offer_id == data.offer_id))
    if (offer.exists() == False):
        raise HTTPException(404, detail="Offer does not exist.")
    else:
        offer = offer.get()
        if (offer.settled == True):
            raise HTTPException(400, detail="It is not possible to book a day as this offer has already been settled.")
        
        if not (offer.prize) and not (data.value):
            raise HTTPException(400, "You must enter a value greater than 0.")
        
        timestamp = datetime.datetime.now().timestamp() 
        if (timestamp > offer.expire_at.timestamp()):
            raise HTTPException(400, "This offer has expired.")
        
        if (timestamp > (datetime.datetime(datetime.datetime.now().year, 1, 1) + datetime.timedelta(days=data.day)).timestamp()):
            raise HTTPException(400, "A day before today cannot pass.")
        
        if (1 > data.value):
            raise HTTPException(400, "The value must be 1 greater than the current prize.")
        
        holder = Stakeholder.select(Stakeholder.value, Stakeholder.user).where(
            (Stakeholder.offer == data.offer_id) & 
            (Stakeholder.day == data.day)
        )
        if (holder.exists() == True):
            holder_value = holder.get().value
            if (data.value < ((holder_value) + (holder_value * 1.5 / 100))):
                raise HTTPException(400, "You cannot reserve this day.")
        
        balance = Balance.select().where(Balance.user == request.data["id"]).get()
        if (balance.balance < data.value):
            raise HTTPException(500, "Insufficient funds.")
        else:
            if (holder.exists() == True):
                holder = holder.get()

                Stakeholder.delete().where(
                    (Stakeholder.user == holder.user) & 
                    (Stakeholder.offer == data.offer_id) &
                    (Stakeholder.day == data.day)
                ).execute()
                
                holder_balance = Balance.select().where(Balance.user == holder.user).get()
                holder_balance.balance += holder.value
                holder_balance.save()
                            
            balance = balance.get()
            balance.balance -= data.value
            balance.save()
        
        Stakeholder.create(
            user=request.data["id"],
            offer=data.offer_id,
            day=data.day,
            value=data.value
        )
        offer.prize += data.value
        offer.save()
        return { "message": "Day booked successfully." }

@router.get("/api/v1/offer/{offer_id}")
def get_offer(offer_id: str):
    offer = Offer.select(Offer.title, Offer.text, Offer.prize, Offer.category, Offer.expire_at, Offer.offer_id, Offer.settled, Offer.created_at, Offer.updated_at).where((Offer.offer_id == offer_id))
    if (offer.exists() == False):
        raise HTTPException(404, detail="Offer does not exist.")
    else:
        offer = model_to_dict(offer.get())
        del offer["user"]
        
        offer["created_at"] = str(offer["created_at"])
        offer["updated_at"] = str(offer["updated_at"])
        offer["links"] = []
        for link in Link.select(Link.url).where(Link.offer == offer["offer_id"]):
            offer["links"].append(link.url)

        calendar = {}
        for stakeholder in Stakeholder.select(Stakeholder.day, Stakeholder.created_at).where((Stakeholder.offer == offer_id)):
            year = stakeholder.created_at.year
            if not (year in calendar.keys()):
                calendar[year] = []

            calendar[year].append(stakeholder.day)
        
        offer["calendar"] = calendar
        return offer

@router.post("/api/v1/offer/proposal")
def offer_proposal(data: ProposalDaySchema, request: Request = Depends(isAuthorization)):
    if (request.data["verified"] == False):
        raise HTTPException(401, "You cannot access this feature as your account has not been verified.")

    if  (request.data["is_admin"] == True):
        raise HTTPException(401, "You cannot access this feature.")

    if not (data.day):
        raise HTTPException(400, "It is necessary to inform the day.")
    
    if (Offer.select(Offer.user).where((Offer.offer_id == data.offer_id) & (Offer.settled == False)).exists() == False):
        raise HTTPException(400, "It is not possible to create a proposal for an order that has been settled.")
    
    stakeholder = Stakeholder.select(Stakeholder.id).where(
        (Stakeholder.user == request.data["id"]) & 
        (Stakeholder.offer == data.offer_id)
    )
    if (stakeholder.exists() == False):
        raise HTTPException(400, "You haven't booked any days so it's not possible to propose.")
    
    if (Stakeholder.select(Stakeholder.id).where(Stakeholder.day == data.day).exists() == False):
        raise HTTPException(400, "This day was not booked by anyone.")
    
    if (Proposal.select(Proposal.offer).where((Proposal.offer == data.offer_id) & (Proposal.user == request.data["id"])).exists() == True):
        raise HTTPException(400, "You have already made a proposal for this offer.")
    
    if (Proposal.select(Proposal.offer).where((Proposal.offer == data.offer_id) & (Proposal.day == data.day)).exists() == True):
        raise HTTPException(400, "This proposal already exists.")

    proposal = Proposal.get_or_create(user=request.data["id"], offer_id=data.offer_id, day=data.day)[0]
    return { "proposal_id": proposal.proposal_id }

@router.get("/api/v1/offer/{offer_id}/proposals")
def list_proposals(offer_id: str, request: Request = Depends(isAuthorization)):
    if (request.data["verified"] == False):
        raise HTTPException(401, "You cannot access this feature as your account has not been verified.")

    proposals = []
    for proposal in (Proposal
                     .select(Proposal.proposal_id, Proposal.day, Proposal.created_at, Proposal.updated_at)
                     .where((Proposal.offer == offer_id))
                     .order_by(Proposal.created_at.desc())):

        proposal = model_to_dict(proposal)
        del proposal["user"]
        del proposal["offer"]
        
        proposal["votes"] = ProposalVote.select().where(ProposalVote.proposal == proposal["proposal_id"]).count()        
        proposal["offer_id"] = offer_id
        proposal["created_at"] = str(proposal["created_at"])
        proposal["updated_at"] = str(proposal["updated_at"])

        proposals.append(proposal)
    
    return proposals

@router.post("/api/v1/offer/proposal/vote")
def vote_proposal(data: ProposalVoteSchema, request: Request = Depends(isAuthorization)):
    if (request.data["verified"] == False):
        raise HTTPException(401, "You cannot access this feature as your account has not been verified.")
    
    if (request.data["is_admin"] == False):
        raise HTTPException(401, "You cannot access this feature.")

    proposal = Proposal.select(Proposal.offer, Proposal.day).where(Proposal.proposal_id == data.proposal_id)
    if (proposal.exists() == False):
        raise HTTPException(404, "This proposal does not exist.")
    else:
        proposal = proposal.get()
    
    if (Offer.select(Offer.user).where((Offer.offer_id == proposal.offer) & (Offer.settled == False)).exists() == False):
        raise HTTPException(400, "It is not possible to vote a proposal for an order that has been settled.")
    
    if (ProposalVote.select(ProposalVote.proposal).where(
            (ProposalVote.user == request.data["id"]) & 
            (ProposalVote.proposal == data.proposal_id) &
            (ProposalVote.offer == proposal.offer)
        ).exists() == True):
        raise HTTPException(500, "You have already voted for the proposal.")
    else:
        ProposalVote.create(
            user=request.data["id"], 
            offer=proposal.offer, 
            proposal=data.proposal_id
        )
            
        judges_count = User.select().where((User.is_admin == True)).count()
        votes_count = ProposalVote.select().where((ProposalVote.proposal == data.proposal_id)).count() + 1
        if ((votes_count / judges_count * 100) >= 60):
            offer = Offer.select().where((Offer.offer_id == proposal.offer)).get()
            offer_prize = offer.prize
            
            offer.settled = True
            offer.save()
            
            holder = Stakeholder.select(Stakeholder.user).where(
                (Stakeholder.offer == proposal.offer) & 
                (Stakeholder.day == proposal.day)).get().user
            
            balance = Balance.select().where((Balance.user == holder)).get()
            balance.balance = balance.balance + offer_prize
            balance.save()
        
        return { "message": "Your vote was successful." }