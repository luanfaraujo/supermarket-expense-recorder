import os
from dotenv import load_dotenv
from google import genai
from PIL import Image
import logging
import gspread
import datetime as dt

dt_now = dt.datetime.now()
today = str(dt_now.date())

# Set up logging config
logging.basicConfig(
    filename="supermarket_robot.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

logging.info("Robot started")

# Load environment variables
load_dotenv()
client = genai.Client()
gc = gspread.service_account(filename="credentials.json")
logging.info("Environment variables loaded and client initialized")

# Load sheet
gsheet = gc.open("Monthly expenses tracking")
worksheet = gsheet.get_worksheet(0)

# Load images
for file in os.listdir("images_to_process"):
    if file.endswith(".jpg"):
        nf_to_process = os.path.join("images_to_process", file)
        img = Image.open(nf_to_process)
        logging.info("Image loaded successfully")
        # implement delete the image after processing, but not now

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[img, "De acordo com essa imagem de uma nota fiscal, me informe, apenas:"
    "o nome do item que eu comprei e o valor total de cada um."
    "Quanto ao preço, utilize ponto como separador decimal, e não vírgula."
    "Organize essa resposta com todos os dados em uma linha, separados por vírgula."]
)

# Convert response to list
response_string = response.text.strip()
response_list = response_string.split(",")
response_list = [item.replace(".", ",") for item in response_list]

# Populate the Google Sheet with the extracted data
# TODO need to make this work for every item in the response, loop it somehow
col_a_values = worksheet.col_values(1) # find all rows w/ data in column A
next_empty_row = len(col_a_values) + 1 # the next empty row is the length of filled rows + 1
worksheet.update_acell(f"A{next_empty_row}", today)
worksheet.update_acell(f"C{next_empty_row}", response_list[0])
worksheet.update_acell(f"D{next_empty_row}", response_list[1])

# Extract token usage metadata and output to log, for control
usage = response.usage_metadata

logging.info(f"Response generated successfully: {response.text}")
logging.info("--- Token Usage Report ---")
logging.info(f"Prompt (Input) Tokens: {usage.prompt_token_count}")
logging.info(f"Candidates (Output) Tokens: {usage.candidates_token_count}")
logging.info(f"Total Tokens Consumed: {usage.total_token_count}")
logging.info("--------------------------\n") # \n adds a blank line after the log entry, better readability