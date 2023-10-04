from dotenv import load_dotenv
from os import environ

# Loads the variables of environments in the .env file
# of the current directory.
load_dotenv(environ.get("ENV_PATH", ".env"))

import logging

# Initialization logging and setting basic settings.
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("./data/bifrost.log", "a"), logging.StreamHandler()]
)

from src.interfaces import api

def main():
    api.start()