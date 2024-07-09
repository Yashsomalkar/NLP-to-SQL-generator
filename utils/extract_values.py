import re
from dateutil.parser import parse as date_parse, ParserError
from sql_metadata import Parser
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

