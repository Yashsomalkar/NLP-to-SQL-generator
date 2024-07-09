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