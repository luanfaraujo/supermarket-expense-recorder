import json
import os
import time
import tkinter as tk
from pathlib import Path
from tkinter import simpledialog
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

logging.info(" ")
logging.info("Robot started")


def load_item_name_mappings(mapping_path: Path) -> dict[str, str]:
    if not mapping_path.exists():
        return {}

    with mapping_path.open(encoding="utf-8") as mapping_file:
        mappings = json.load(mapping_file)

    if not isinstance(mappings, dict) or not all(
        isinstance(original, str) and isinstance(personalized, str)
        for original, personalized in mappings.items()
    ):
        raise ValueError(f"Invalid item name mappings in {mapping_path}")

    return mappings


def get_personalized_item_name(
    item_name: str,
    mappings: dict[str, str],
    mapping_path: Path,
) -> str:
    original_name = item_name.strip()
    if original_name in mappings:
        return mappings[original_name]

    dialog_root = tk.Tk()
    dialog_root.withdraw()
    try:
        personalized_name = simpledialog.askstring(
            "Personalizar nome do item",
            f"Nome encontrado na NF:\n{original_name}\n\n"
            "Digite o nome personalizado (ou deixe em branco para manter):",
            parent=dialog_root,
        )
    finally:
        dialog_root.destroy()

    personalized_name = (personalized_name or "").strip()
    if not personalized_name:
        personalized_name = original_name

    mappings[original_name] = personalized_name
    mapping_path.write_text(
        json.dumps(mappings, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    logging.info("Saved item name mapping: %s -> %s", original_name, personalized_name)
    return personalized_name


# Load environment variables
load_dotenv()
client = genai.Client()
gc = gspread.service_account(filename="credentials.json")
logging.info("Environment variables loaded and client initialized")

# Load sheet
gsheet = gc.open("Monthly expenses tracking")
worksheet = gsheet.get_worksheet(0)
logging.info("Google Sheet loaded successfully")

# Load images
accepted_formats = [".jpeg", ".png", ".jpg"]

for file in os.listdir("G:\\Meu Drive\\Expense Tracking\\images_to_process"):
    if file.endswith(tuple(accepted_formats)):
        nf_to_process = os.path.join("G:\\Meu Drive\\Expense Tracking\\images_to_process", file)
        img = Image.open(nf_to_process)
        logging.info("Image loaded successfully")
        # TODO implement delete the image after processing, but not now

for attempt in range(1, 4):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[img, "De acordo com essa imagem de uma nota fiscal, me informe, apenas:"
            "o nome do item que eu comprei e o valor total de cada um."
            "Ignore peso, quantidade, e qualquer outro dado que não seja o nome do item e o valor total."
            "Quanto ao preço, utilize ponto como separador decimal, e não vírgula."
            "Organize essa resposta com todos os dados em uma única linha, separados por um pipe (|)."
            "Por exemplo: NOME DO ITEM 1|VALOR TOTAL 1|NOME DO ITEM 2|VALOR TOTAL 2|NOME DO ITEM 3|VALOR TOTAL 3"]
        )
        break
    except Exception as e:
        is_service_unavailable = "503" in str(e)
        if not is_service_unavailable or attempt == 3:
            logging.error(f"Error generating response: {e}")
            raise

        logging.warning(
            f"Gemini returned 503 on attempt {attempt}/3. Retrying in 2 mins."
        )
        time.sleep(120)

# Convert response to list
response_string = response.text.strip()
response_list = [item.strip() for item in response_string.split("|")]
iterations = len(response_list) // 2  # Calculate the number of iterations based on the number of items
current_item = 0  # Initialize a variable to keep track of the current item being processed
item_name_mappings_path = Path(__file__).resolve().with_name("item_name_mappings.json")
item_name_mappings = load_item_name_mappings(item_name_mappings_path)

# Populate the Google Sheet with the extracted data
for i in range(iterations):
    item_name = get_personalized_item_name(
        response_list[current_item],
        item_name_mappings,
        item_name_mappings_path,
    )
    col_a_values = worksheet.col_values(1) # find all rows w/ data in column A
    next_empty_row = len(col_a_values) + 1 # the next empty row is the length of filled rows + 1
    worksheet.update_acell(f"A{next_empty_row}", today)
    worksheet.update_acell(f"C{next_empty_row}", item_name)
    worksheet.update_acell(f"D{next_empty_row}", response_list[current_item + 1].replace(".", ","))
    current_item = current_item + 2 # Move to the next item name in the response list

# Extract token usage metadata and output to log, for control
usage = response.usage_metadata
logging.info(f"Response generated successfully: {response.text}")
logging.info("--- Token Usage Report ---")
logging.info(f"Prompt (Input) Tokens: {usage.prompt_token_count}")
logging.info(f"Candidates (Output) Tokens: {usage.candidates_token_count}")
logging.info(f"Total Tokens Consumed: {usage.total_token_count}")
logging.info("--------------------------\n") # \n adds a blank line after the log entry, better readability