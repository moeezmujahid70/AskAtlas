# Gemini Powered ChatBot

Welcome to the **AI Powered ChatBot** project! This project leverages LLM'S to create an interactive chatbot interface using Streamlit.

## Installation

To get started, clone this repository and install the required dependencies.

```bash
git clone https://github.com/manogyaguragai/Gemini_powered_chatbot.git
cd Gemini_powered_chatbot
pip install -r requirements.txt
```

## Configuration

This project uses environment variables to manage the API key for Google Generative AI. Follow these steps to set up your environment:

1. Create a `.env` file in the project root directory.
2. Add your Google API key to the `.env` file:

    ```plaintext
    GOOGLE_API_KEY=your_google_api_key_here
    ```

## Usage

To run the chatbot application, use the following command:

```bash
streamlit run chatbot.py
```

This will start a local Streamlit server. Click on the given link to interact with the chatbot.

## Code Overview

The main components of the project are as follows:

- **Environment Setup**: Load environment variables using `dotenv`.
- **API Configuration**: Configure the Google Generative AI with the provided API key.
- **Streamlit UI**: Create a user interface with Streamlit to interact with the chatbot.    

```