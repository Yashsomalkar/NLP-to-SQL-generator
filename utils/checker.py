from sql_metadata import Parser
from constants.allowed import allowed_commands, allowed_tables, allowed_columns
from utils.extract_values import extract_columns_and_comparisons
from constants.country_code import country_codes
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

def validate_country_codes(sql: str) -> bool:
    extracted_data = extract_columns_and_comparisons(sql)
    for column, comparison in extracted_data.items():
        print(f"checking coloumn in country codes {column}\n and comparison : {comparison}")
        if 'country' in column.lower():
            value = comparison['value']
            if isinstance(value, list):
                if not all(v in country_codes for v in value):
                    return False
            else:
                if value not in country_codes:
                    return False
    return True