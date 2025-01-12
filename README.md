# Ask the Website

## Project Description

Ask the Website is a Chrome extension that enables users to interact with a bot capable of answering questions about the content of the active browser tab. The project consists of two main components:

1. A Chrome extension (frontend) that allows users to interact with the webpage and the bot.
2. A FastAPI server (backend) that processes requests and utilizes a local Large Language Model (LLM) to generate responses.

The primary goal of this project is to enhance web browsing by providing an intelligent assistant that can analyze, explain, and answer questions about the content of any web page the user is viewing. Users can switch between tabs, asking questions about different pages, integrating this assistance into their regular browsing workflow.


## Key Features

- Analysis of the current web page content
- Answering user questions about the page content
- Ability to select specific HTML tags for analysis

## Installation and Setup

### Clone the Repository

```bash
git clone https://github.com/bezbahen0/ask-the-website
```

### Install Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `./ask-the-website/chrome-extension` folder

Detailed instructions can be found [here](https://support.google.com/chrome/a/answer/2714278#:~:text=Go%20to%20chrome,Load%20unpacked.).

### Set Up and Run the Server

```bash
cd ask-the-website

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn server.app:app --port 8080
```

### Load the Model

By default, [this model](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf?download=true) is used. Download it to the `models` folder. The project supports all GGUF models compatible with llama_cpp.

## Features and Parameters

- **Supported page types**: Currently only text/html
- **Context parameters**:
  - Tag Attributes: use tag attributes (body only)
  - Only text: preprocess the page into MD format
  - Concatenate small chunks: combine small chunks for large pages
  - Body: use the body tag of the HTML page
  - Head: (under development)
  - Scripts: process script tags
- Selection of specific HTML tags on the page for analysis
- Chat with the bot without using page context

## Known Limitations and Issues

- Lack of support for large content types (PDF, JSON)
- Issues when working with large pages
- Inability to stop generation

## Development Plans

- Improve UI
- Add generation settings to ui (maximum context size, temperature, etc.)
- Token counting when selecting a tag
- Add a stop generation button
- Improve logging system

## Contributing

Welcome contributions to the project. If you have ideas or suggestions, please create an issue or submit a pull request.
