from sql_metadata import Parser
import re
from dateutil.parser import parse as date_parse, ParserError
from constants.allowed import allowed_commands, allowed_tables, allowed_columns

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
         # Check for ANY(column_name) IN (values)
        any_in_match = re.search(rf"ANY\s*\(\s*([^\)]+)\s*\)\s*IN\s*\(\s*([^\)]+)\s*\)", condition, re.IGNORECASE)
        if any_in_match:
            column = any_in_match.group(1).strip()
            values = any_in_match.group(2).split(',')
            if column in where_columns:
                formatted_values = []
                for value in values:
                    value = value.strip().strip("'").strip('"').rstrip(';')
                    value_type, formatted_value = identify_value_type(value)
                    formatted_values.append(formatted_value)
                if column not in result:
                    result[column] = []
                result[column].append({'operator': 'ANY IN', 'value': formatted_values, 'type': 'array'})
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