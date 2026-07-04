import os
from dotenv import load_dotenv
from google import genai
from PIL import Image
import logging

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
logging.info("Environment variables loaded and client initialized")

for file in os.listdir("images_to_process"):
    if file.endswith(".jpg"):
        nf_to_process = os.path.join("images_to_process", file)
        img = Image.open(nf_to_process)
        logging.info("Image loaded successfully")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[img, "De acordo com essa imagem de uma nota fiscal, me informe, apenas: o nome do item que eu comprei e o valor total de cada um."]
)

# Extract token usage metadata and output to log
usage = response.usage_metadata

print(response.text)
logging.info(f"Response generated successfully: {response.text}")
logging.info("--- Token Usage Report ---")
logging.info(f"Prompt (Input) Tokens: {usage.prompt_token_count}")
logging.info(f"Candidates (Output) Tokens: {usage.candidates_token_count}")
logging.info(f"Total Tokens Consumed: {usage.total_token_count}")
logging.info("--------------------------\n") # \n adds a blank line after the log entry, better readability