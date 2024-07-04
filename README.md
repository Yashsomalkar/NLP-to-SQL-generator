


# NLP to SQL Query Generator 🐘

This project uses OpenAI's GPT-4 API to generate SQL queries based on natural language questions. It employs Streamlit for the user interface, making it easy to input questions and get SQL queries as responses.

## Features

- Converts natural language questions into SQL queries.
- Ensures the generated SQL queries adhere to predefined guidelines, including:
  - Only using allowed commands (`SELECT`).
  - Only using allowed tables and columns.
  - Not using table aliases.
- Provides explanations for the generated SQL queries.
- Validates the structure and content of SQL queries.

## Installation

To get started, you'll need Python installed on your machine. You can use a virtual environment or install the dependencies globally.

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/nlp-to-sql-generator.git
cd nlp-to-sql-generator
```

### Step 2: Create and Activate a Virtual Environment (Optional but Recommended)

#### For Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

#### For macOS and Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install the Required Packages

```bash
pip install -r requirements.txt
```

## Usage

1. Ensure you have your OpenAI API key ready. You will need to add it to your Streamlit secrets.

2. Run the Streamlit app:

```bash
streamlit run app.py
```

3. Open the provided local URL in your web browser.

4. Enter your natural language question into the input field and receive the generated SQL query.

## Requirements

- Python 3.7 or higher
- Streamlit
- OpenAI API
- sql-metadata
- dateutil

All required packages are listed in the `requirements.txt` file.

## Adding Your OpenAI API Key

To securely add your OpenAI API key, follow these steps:

1. Create a `.streamlit` directory in the root of your project if it doesn't exist:

```bash
mkdir -p ~/.streamlit
```

2. Create a `secrets.toml` file in the `.streamlit` directory:

```bash
touch ~/.streamlit/secrets.toml
```

3. Add your OpenAI API key to the `secrets.toml` file:

```toml
[openai]
api_key = "your_openai_api_key"
```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License.

---

### Steps to Run

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/nlp-to-sql-generator.git
cd nlp-to-sql-generator
```

2. **Create and activate a virtual environment (optional):**

#### For Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

#### For macOS and Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install the required packages:**

```bash
pip install -r requirements.txt
```

4. **Add your OpenAI API key:**

- Create a `.streamlit` directory in your home directory:

```bash
mkdir -p ~/.streamlit
```

- Create a `secrets.toml` file:

```bash
touch ~/.streamlit/secrets.toml
```

- Add your OpenAI API key to the `secrets.toml` file:

```toml
[openai]
api_key = "your_openai_api_key"
```

5. **Run the Streamlit app:**

```bash
streamlit run app.py
```

6. **Open the provided local URL in your web browser and start using the app.**


