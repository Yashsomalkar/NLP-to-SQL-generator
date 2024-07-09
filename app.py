import streamlit as st
from openai import OpenAI
import re
from utils.checker import (
    contains_allowed_commands,
    contains_allowed_tables,
    contains_allowed_columns,
    extract_columns_and_comparisons
)
from utils.prompt import get_sql_prompt
from constants.table_schema import ddl_list
from constants.additional_context import doc_list

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
