from src.interfaces.cli.lib.prediction import Prediction
from os.path import exists
from os import makedirs

import click
import json

makedirs("./data", exist_ok=True)
if (exists("prediction.json") == False):
    with open("prediction.json", "w") as w:
        json.dump({
            "url":   "http://127.0.0.1:3462",
            "token": None,
            "username": None, 
            "password": None
        }, w)

with open("prediction.json", "r") as r:
    configs = json.load(r)

prediction = Prediction(url=configs["url"], token=configs["token"])

@click.group()
def cli():
    ...

@cli.command("account")
def account():
    """Manage the user account."""
    
    print("""
    [1] - Login / Signup account 
    [2] - Show Balance
    """.replace("    ", ""))

    prompt = click.prompt("Select ID", type=int)
    if (prompt == 1):
        print("\n- Enter credentials: \n")
        
        username = click.prompt("Username")
        password = click.prompt("Password", hide_input=True)
        
        token = prediction.auth_account(
            username=username, 
            password=password
        )
        if (token[0] != 200):
            prediction.create_account(
                username=username, 
                password=password
            )
            token = prediction.auth_account(
                username=username, 
                password=password
            )
        
        if (token[0] == 200):
            configs["username"] = username
            configs["password"] = password
            configs["token"] = token[-1]["token"] 
            with open("prediction.json", "w") as w:
                json.dump(configs, w)
            
            print(json.dumps(token, indent=4))

    elif (prompt == 2):
        print("- User account balance: \n")
        
        balance = prediction.get_balance()
        print(json.dumps(balance, indent=4))

@cli.command("offer")
def offer():
    """Manage offer."""
    print("""
    [1] - Create New Offer
    [2] - List Offers
    [3] - Offer Reserve
    [4] - Show Offer
    [5] - Propose Day For Voting
    [6] - List Voting Proposals
    [7] - Vote on a proposal
    """.replace("    ", ""))
    
    prompt = click.prompt("Select ID", type=int)
    if (prompt == 1):
        print("\n- Create New Offer: \n")
        
        title = click.prompt("Title")
        text = click.prompt("Text")
        category = click.prompt("Category")
        if (click.prompt("Want to add links [False, True]", type=bool)):
            links = click.prompt("Links").replace(",", " ").split()
        else:
            links = None
        
        expire_in_years = click.prompt("Expire in years", type=int)
        print(json.dumps(prediction.create_offer(
            title=title,
            text=text,
            category=category,
            links=links,
            expire_in_years=expire_in_years
        ), indent=4))
    
    elif (prompt == 2):
        print("\n - List offers: \n")
        
        print(json.dumps(prediction.list_offers(), indent=3))
        
    elif (prompt == 3):
        print("\n - Offer Reserve: \n")

        offer_id = click.prompt("Offer ID", type=str)
        offer_day = click.prompt("Day", type=int)
        offer_value = click.prompt("Value", type=float)

        print(json.dumps(prediction.offer_reserve(offer_id, offer_day, offer_value), indent=3))
    
    elif (prompt == 4):
        print("\n - Show Offer: \n")

        offer_id = click.prompt("Offer ID", type=str)
        print(json.dumps(prediction.get_offer(offer_id=offer_id), indent=3))

    elif (prompt == 5):
        print("\n - Propose Day For Voting: \n")
        
        offer_id = click.prompt("Offer ID", type=str)
        offer_day = click.prompt("Day", type=int)

        print(json.dumps(prediction.offer_proposal(offer_id=offer_id, day=offer_day), indent=3))
    
    elif (prompt == 6):
        print("\n - List Voting Proposals: \n")
    
        offer_id = click.prompt("Offer ID", type=str)
        
        print(json.dumps(prediction.list_proposals(offer_id), indent=3))
    
    elif (prompt == 7):
        print("\n - Vote on a proposal: \n")
        
        proposal_id = click.prompt("Proposal ID", type=str)
        print(json.dumps(prediction.vote_proposal(proposal_id), indent=3))