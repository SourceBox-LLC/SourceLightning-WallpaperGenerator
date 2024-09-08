from openai import OpenAI, OpenAIError, RateLimitError, Timeout
from dotenv import load_dotenv
import requests
import os
import platform
import ctypes  # For Windows wallpaper
from io import BytesIO
from PIL import Image, UnidentifiedImageError

# Function to save the API key to a .env file
def save_api_key_to_env(api_key, key_name="OPENAI_API_KEY"):
    if os.path.exists(".env"):
        os.remove(".env")  # Remove existing .env file if it exists
    with open(".env", "w") as env_file:
        env_file.write(f"{key_name}={api_key}\n")
    print(".env file created with the API key.")

def get_openai_api_key():
    # Check if API key is present in environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Prompt the user to enter the API key if not found
        manual_api_key = input("Enter your OpenAI API key: ")
        save_api_key_to_env(manual_api_key)
        # Reload the environment with the new API key
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
    return api_key

# Load environment variables
load_dotenv()

# Get the OpenAI API key
api_key = get_openai_api_key()

# Initialize the OpenAI client
try:
    client = OpenAI(api_key=api_key)
except OpenAIError as e:
    raise RuntimeError(f"Failed to initialize OpenAI client: {e}")

# Function to generate an image using OpenAI
def generate_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return image_url
    except RateLimitError:
        raise RuntimeError("Rate limit exceeded. Please wait and try again.")
    except Timeout:
        raise RuntimeError("The request to OpenAI timed out. Please try again.")
    except OpenAIError as e:
        raise RuntimeError(f"OpenAI API error: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to generate image: {e}")

# Function to download the image and save it locally
def save_image(image_url, file_path='generated_image.png'):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        img = Image.open(BytesIO(response.content))
        img.save(file_path)
        return file_path
    except requests.exceptions.Timeout:
        raise RuntimeError("Request to download image timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download image from {image_url}: {e}")
    except UnidentifiedImageError:
        raise RuntimeError("Failed to identify image content. It may be corrupted.")
    except PermissionError:
        raise RuntimeError(f"Permission denied: Cannot save image to {file_path}.")
    except Exception as e:
        raise RuntimeError(f"Failed to save image: {e}")

# Function to set wallpaper for Windows
def set_wallpaper_windows(image_path):
    try:
        abs_path = os.path.abspath(image_path)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 0)
    except Exception as e:
        raise RuntimeError(f"Failed to set wallpaper on Windows: {e}")

# Function to set wallpaper for Linux (GNOME example)
def set_wallpaper_linux(image_path):
    try:
        abs_path = os.path.abspath(image_path)
        command = f"gsettings set org.gnome.desktop.background picture-uri 'file://{abs_path}'"
        result = os.system(command)
        if result != 0:
            raise RuntimeError("Failed to set wallpaper on Linux. Check if `gsettings` is installed.")
    except Exception as e:
        raise RuntimeError(f"Failed to set wallpaper on Linux: {e}")

# Function to detect OS and set wallpaper accordingly
def set_wallpaper(image_path):
    current_os = platform.system()
    try:
        if current_os == 'Windows':
            set_wallpaper_windows(image_path)
        elif current_os == 'Linux':
            set_wallpaper_linux(image_path)
        else:
            raise RuntimeError(f"OS {current_os} is not supported for setting wallpaper.")
    except Exception as e:
        raise RuntimeError(f"Error setting wallpaper: {e}")

def main():
    try:
        # Get the prompt from the user
        prompt = input("Enter a prompt for the image: ")

        # Generate the image from OpenAI
        print("Generating image...")
        image_url = generate_image(prompt)

        # Save the image locally
        print("Saving image...")
        image_path = save_image(image_url, 'generated_image.png')

        # Set the image as the wallpaper
        print("Setting wallpaper...")
        set_wallpaper(image_path)
        print("Wallpaper set successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
