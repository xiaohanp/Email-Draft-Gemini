# Email Draft Gemini AI Assistant

![Email Agent Teaser](teaser.png)

A lightweight app that connects to your whole email threads via IMAP and uses Google Gemini to organize threads and draft replies based on the whole context. Built with Zimbra in mind, but works with any IMAP server.

## Features

- **Full conversation context**  
  Reconstructs entire email threads from `INBOX` and `Sent`, so replies are always grounded in the complete history  

- **Smart threading**  
  Groups messages by subject and cleans prefixes like `Re:` and `Fwd:` for coherent conversations  

- **Editable AI drafts**  
  Generates replies (via Gemini) in your writing style, with quick refinements 

- **Bilingual support**  
  Draft and translate seamlessly in English and French  

## Quick Start 

### 1. Setup Virtual Environment (Recommended)
Ensure you have Python 3.9+ installed. It's recommended to use a virtual environment.

**Using Python `venv`**:
```bash
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Mac/Linux: source .venv/bin/activate
```

**Using Conda**:
```bash
conda create -n email-agent python=3.10
conda activate email-agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the example environment file:
```bash
cp .env.example .env
```
Open `.env` and fill in your credentials:
1. **Google Gemini API Key**: Get this from Google AI Studio.
2. **IMAP Credentials**: Enter your IMAP host, email, and app password.
3. **Persona Instructions**: Customize the `MY_PERSONA` variable to let the AI know how you like to sound (e.g., *"I am a software engineer. My tone is professional but friendly..."*). 

### 4. Run the App
```bash
streamlit run app.py
```
The app will automatically launch in your default web browser at `http://localhost:8501`. 

## Security & Privacy 
- **Local Processing**: Your emails are fetched directly from your IMAP server to your local machine. They are only sent to the Gemini API when you explicitly request an AI draft or summary.
- **No Stored Passwords**: Your passwords live strictly in your local `.env` file, which is ignored by Git and never pushed to the cloud.
- **Drafts Only**: This application does **not** send emails on your behalf. It only saves drafts to your `Drafts` folder or copies text to your clipboard. 

## Contributing 
Contributions are welcome! If you use a different IMAP server and want to add connection profiles, or if you have ideas for new AI features, feel free to open a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
