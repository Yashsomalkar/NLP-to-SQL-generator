import streamlit as st
from openai import OpenAI
import re
from sql_metadata import Parser
from dateutil.parser import parse as date_parse
from dateutil.parser import ParserError

def add_ddl_to_prompt(initial_prompt: str, ddl_list: list[str], max_tokens: int = 14000) -> str:
    if ddl_list:
        initial_prompt += "\n===Tables \n"
        for ddl in ddl_list:
            if (len(initial_prompt) + len(ddl)) < max_tokens:
                initial_prompt += f"{ddl}\n\n"
    return initial_prompt

def add_documentation_to_prompt(initial_prompt: str, documentation_list: list[str], max_tokens: int = 14000) -> str:
    if documentation_list:
        initial_prompt += "\n===Additional Context \n\n"
        for documentation in documentation_list:
            if (len(initial_prompt) + len(documentation)) < max_tokens:
                initial_prompt += f"{documentation}\n\n"
    return initial_prompt

def get_sql_prompt(question: str, question_sql_list: list, ddl_list: list, doc_list: list) -> str:
    initial_prompt = (
        "You are a PostgreSQL expert. Please help to generate a SQL query to answer the question. "
        "Your response should ONLY be based on the given context and follow the response guidelines and format instructions. "
    )
    initial_prompt = add_ddl_to_prompt(initial_prompt, ddl_list)
    initial_prompt = add_documentation_to_prompt(initial_prompt, doc_list)

    initial_prompt += (
        "===Response Guidelines \n"
        "5. If the provided context is sufficient, please generate a valid SQL query (in markdown ```sql\n(.*?)```) without any explanations for the question. \n"
        "6. If the provided context is almost sufficient but requires knowledge of a specific string in a particular column, please generate an intermediate SQL query to find the distinct strings in that column. Prepend the query with a comment saying intermediate_sql. \n"
        "7. If the provided context is insufficient, please explain why it can't be generated. \n"
        "8. Please use the most relevant table(s). \n"
        "9. If the question has been asked and answered before, please repeat the answer exactly as it was given before. \n"
        "10. If the question is ambiguous, please ask for clarification and generate an intermediate query. \n"
        "11. Avoid using '*'. Specify columns in table specifically that needs to be used.\n"
        "12. Do not use table aliases or abbreviations. Use full table names for clarity. \n"
  
    )

    message_log = [{'role': 'system', 'content': initial_prompt}]

    for example in question_sql_list:
        if example and "question" in example and "sql" in example:
            message_log.append({'role': 'user', 'content': example["question"]})
            message_log.append({'role': 'assistant', 'content': example["sql"]})

    message_log.append({'role': 'user', 'content': question})

    return message_log

# Hardcoded table schema and additional context
ddl_list = [
    "CREATE TABLE Company (TargetCompanyId SERIAL PRIMARY KEY,TargetCompanyName VARCHAR(255) NOT NULL,Country VARCHAR(100),IncorporationDate DATE,Sector VARCHAR(100),BusinessDescription TEXT,IsPubliclyListed BOOLEAN);",
    "CREATE TABLE Deals (DealId SERIAL PRIMARY KEY,TargetCompanyId INT REFERENCES Company(TargetCompanyId),Date DATE NOT NULL,TotalAmountInDollarInMillion DECIMAL(18, 2),AmountInRupeeInCrores DECIMAL(18, 2),InvestorsNames TEXT[],DivestorsNames TEXT[],DealType VARCHAR(10) CHECK (DealType IN ('credit', 'equity')));",
    "CREATE TABLE Portfolio (TargetCompanyId INT REFERENCES Company(TargetCompanyId),FundManagerId INT REFERENCES FundManager(FundManagerId),PRIMARY KEY (TargetCompanyId, FundManagerId));",
    "CREATE TABLE FM_Deal (DealId INT REFERENCES Deals(DealId),FundManagerId INT REFERENCES FundManager(FundManagerId),BuyOrSell VARCHAR(4) CHECK (BuyOrSell IN ('buy', 'sell')),Amount DECIMAL(18, 2),Stake DECIMAL(5, 2),PRIMARY KEY (DealId, FundManagerId));",
    "CREATE TABLE FundManager (FundManagerId SERIAL PRIMARY KEY,FundManagerName VARCHAR(255) NOT NULL,Country VARCHAR(100),InterestedSector TEXT[],InterestedGeographies TEXT[]);"
]

doc_list = [
    "AmountInRupeeInCrores has unit in Crores example: if there is 1,00,00,000 inr or rupees would be 1",
    "TotalAmountInDollarInMillion has unit in Million Dollars example : if there is 1,000,000 dollars would be 1",
    "Amount has the unit Million Dollars"
]

allowed_commands = ["SELECT"]
allowed_tables = ["FundManager", "Company", "Deals", "Portfolio", "FM_Deal", "FundManager"]
allowed_columns = {
    "Company": [
        "TargetCompanyId",
        "TargetCompanyName",
        "Country",
        "IncorporationDate",
        "Sector",
        "BusinessDescription",
        "IsPubliclyListed"
    ],
    "Deals": [
        "DealId",
        "TargetCompanyId",
        "Date",
        "TotalAmountInDollarInMillion",
        "AmountInRupeeInCrores",
        "InvestorsNames",
        "DivestorsNames",
        "DealType"
    ],
    "Portfolio": [
        "TargetCompanyId",
        "FundManagerId"
    ],
    "FM_Deal": [
        "DealId",
        "TargetCompanyId",
        "FundManagerId",
        "BuyOrSell",
        "Amount",
        "Stake"
    ],
    "FundManager": [
        "FundManagerId",
        "FundManagerName",
        "Country",
        "InterestedSector",
        "InterestedGeographies"
    ]
}

def split_sql_queries(sql: str) -> list:
    return [query.strip() for query in sql.split(';') if query.strip()]

def contains_allowed_commands(sql: str) -> bool:
    queries = split_sql_queries(sql)
    for query in queries:
        try:
            parser = Parser(query)
            command = parser.query_type.replace("QueryType.", "").upper()
            print(f"Extracted command: {command}")
            if command not in allowed_commands:
                return False
        except Exception as e:
            print(f"Error parsing command: {e}")
            return False
    return True

def contains_allowed_tables(sql: str) -> bool:
    queries = split_sql_queries(sql)
    for query in queries:
        try:
            parser = Parser(query)
            tables = parser.tables
            print(f"Extracted tables: {tables}")
            for table in tables:
                if table not in allowed_tables:
                    return False
        except Exception as e:
            print(f"Error parsing tables: {e}")
            return False
    return True

def contains_allowed_columns(sql: str) -> bool:
    queries = split_sql_queries(sql)
    for query in queries:
        try:
            parser = Parser(query)
            columns = parser.columns
            tables = parser.tables
            print(f"Extracted columns: {columns}")
            print(f"Extracted tables: {tables}")

            # Check if all tables in the query are allowed
            if not all(table in allowed_columns for table in tables):
                print(f"One or more tables in the query are not allowed")
                return False

            # Iterate through columns
            for col in columns:
                parts = col.split('.')
                if len(parts) > 1:
                    table_name, col_name = parts[0], parts[-1]
                    print(f"checking in col {col_name}")
                    # Check if the table name (or alias) is allowed or created in the query
                    if table_name not in allowed_columns and table_name not in tables:
                        if not contains_allowed_tables(query):
                            print(f"Table alias or created table {table_name} not allowed")
                            return False
                    if col_name not in allowed_columns.get(table_name, []):
                        print(f"Column {col_name} in table {table_name} is not allowed")
                        return False
                else:
                    col_name = parts[-1]
                    print(f"checking in col {col_name}")
                    found = False
                    for table_name, allowed_cols in allowed_columns.items():
                        print(f"allowed coloumn name from {allowed_cols} ")
                        if col_name in allowed_cols:
                            found = True
                            print("checks passed for coloumns check")
                            break
                    if not found:
                        print(f"Column {col_name} is not allowed in any table")
                        return False

        except Exception as e:
            print(f"Error parsing columns: {e}")
            return False
    return True

def extract_columns_and_comparisons(sql):
    parser = Parser(sql)
    
    # Get columns in WHERE clause
    where_columns = parser.columns_dict.get('where', [])
    
    # Initialize the result dictionary
    result = {}
    
    # Define comparison operators, sorted to ensure >= and <= are checked before > and <
    comparison_operators = ['>=', '<=', '> =', '< =', '=','!=', '! =', 'LIKE', 'ILIKE', '>', '<']
    
    # Extract the WHERE clause
    where_clause_match = re.search(r'WHERE (.*)', sql, re.IGNORECASE | re.DOTALL)
    if where_clause_match:
        where_clause = where_clause_match.group(1)
    else:
        return result
    
    # Helper function to identify value type
    def identify_value_type(value):
        # Check if it's a boolean
        if value.lower() == 'true':
            return 'boolean', True
        elif value.lower() == 'false':
            return 'boolean', False
        if 'CURRENT_DATE' in value.upper():
            return 'date', value
        
        try:
            # Check if it's a number
            int_value = int(value)
            return 'integer', int_value
        except ValueError:
            try:

                # check if its a float
                float_value = float(value)
                return 'float', float_value
            except ValueError:
                try:
            
                    # Check if it's a date
                    date_value = date_parse(value, fuzzy=False)
                    return 'date', date_value.strftime('%Y-%m-%d')
                except (ParserError, ValueError):
                    # Otherwise, it's a string
                    return 'string', value
    conditions = re.split(r'\s+(AND|OR)\s+', where_clause, flags=re.IGNORECASE)
    for condition in conditions:
        # Check for ANY() function with any operator
        # <value> = ANY(column name)
        for operator in comparison_operators:
            any_match = re.search(rf"'([^']*)'\s*{re.escape(operator)}\s*ANY\s*\(\s*([^\)]+)\s*\)", condition, re.IGNORECASE)
            if any_match:
                value = any_match.group(1)
                column = any_match.group(2).strip()
                if column in where_columns:
                    value_type, formatted_value = identify_value_type(value)
                    if column not in result:
                        result[column] = []
                    result[column].append({'operator': operator, 'value': formatted_value, 'type': value_type})
                continue
        # Check for @> ARRAY construct
        #column_name @> ARRAY[values]
        array_match = re.search(rf"([^\s]+)\s*@>\s*ARRAY\s*\[([^\]]+)\]", condition, re.IGNORECASE)
        if array_match:
            column = array_match.group(1).strip()
            values = array_match.group(2).split(',')
            if column in where_columns:
                formatted_values = []
                for value in values:
                    value = value.strip().strip("'").strip('"').rstrip(';')
                    value_type, formatted_value = identify_value_type(value)
                    formatted_values.append(formatted_value)
                if column not in result:
                    result[column] = []
                result[column].append({'operator': '@> ARRAY', 'value': formatted_values, 'type': 'array'})
            continue
        

        # Iterate through each column found in the WHERE clause
        for column in where_columns:
            for operator in comparison_operators:
                # Regex pattern to find the column with its comparison operator and value
                pattern = re.compile(rf"{column}\s*({re.escape(operator)})\s*(\"[^\"]*\"|'[^']*'|[^'\"\s;]+)", re.IGNORECASE)
                match = pattern.search(condition)
                if match:
                    operator = match.group(1).upper()
                    value = match.group(2).strip("'").strip('"').rstrip(';')
                    value_type, formatted_value = identify_value_type(value)
                    result[column] = {'operator': operator, 'value': formatted_value, 'type': value_type}
                    break  # Stop after the first match for this column

    return result

# Chat Interface
st.title("SQL Query Generator 🐘")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def generate_response(question):
    question_sql_list = []  # Populate this with any previous Q&A pairs if available
    prompt = get_sql_prompt(question, question_sql_list, ddl_list, doc_list)

    print(f"Generated prompt: {prompt}")

    response = OpenAI(api_key=st.secrets["openai"]["api_key"]).chat.completions.create(
        model=st.session_state["openai_model"],
        messages=prompt
    )

    response_content = response.choices[0].message.content
    print(f"Full response: {response_content}")

    # Check if the response contains only allowed SQL commands and tables
    sqls = []
    sql_blocks = re.findall(r"```sql\n(.*?)```", response_content, re.DOTALL)
    for sql in sql_blocks:
        sql = sql.strip()  # Remove any leading/trailing whitespace
        print(f"Checking SQL: {sql}")
        if not contains_allowed_commands(sql):
            print("Response contains disallowed SQL commands.")
            return "Not allowed: The response contains disallowed SQL commands.", []
        if not contains_allowed_tables(sql):
            print("Response contains disallowed tables.")
            return "Not allowed: The response contains disallowed tables.", []
        if not contains_allowed_columns(sql):
            print("Response contains non-allowed columns.")
            return "Not allowed: The response contains non-allowed columns.", []
        sqls.append(sql)

    print(f"Extracted SQLs: {sqls}")

    return response_content, sqls

def generate_description_response(sql):
    description_prompt = f"Please be concise, describe what SQL does in concise way : {sql}"
    description_response = OpenAI(api_key=st.secrets["openai"]["api_key"]).chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[{'role': 'system', 'content': description_prompt}]
    )
    print(f"Description response for SQL '{sql}': {description_response.choices[0].message.content}")
    return description_response.choices[0].message.content

if prompt := st.chat_input("Enter your question: example: Give list of Fund Managers?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    full_response, sqls = generate_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    with st.chat_message("assistant"):
        st.markdown(full_response)

    if sqls:
        for sql in sqls:
            description_response = generate_description_response(sql)
            st.session_state.messages.append({"role": "assistant", "content": description_response})

            with st.chat_message("assistant"):
                st.markdown(description_response)

            # Extract columns and comparisons from SQL
            columns_and_comparisons = extract_columns_and_comparisons(sql)
            print(f"Extracted columns and comparisons: {columns_and_comparisons}")
            st.session_state.messages.append({"role": "assistant", "content": f"Extracted columns and comparisons: {columns_and_comparisons}"})

            with st.chat_message("assistant"):
                st.markdown(f" Testing : Extracted columns and comparisons: {columns_and_comparisons}")
