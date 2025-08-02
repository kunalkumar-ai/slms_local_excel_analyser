from typing import Dict, Any
import re

def build_prompt(schema: Dict[str, Any], sample: str, question: str) -> str:
    """
    Build a prompt for the SLM using the schema, sample data, and user question.
    """
    prompt = f"""
You are an expert data analyst. Given the following Excel sheet schema and a sample of the data, write a Pandas code snippet to answer the user's question.

Schema: {schema}

Sample data:
{sample}

Question: {question}

IMPORTANT: If the question refers to a specific value (e.g., a month or region), always filter the DataFrame for that value before aggregating or summarizing.Do NOT provide any additional instructions, meta-questions, or explanations.


Respond ONLY with a valid Pandas code snippet that can be executed on the DataFrame 'df'. Do NOT include explanations.

Always assign your answer to a variable named result and print it using print(result).


"""
    return prompt

def extract_pandas_code(response: str) -> str:
    """
    Extract the largest (full) Python code block from the SLM response.
    If no code block is found, fallback to all lines that look like code.
    """
    # Try to extract the largest python code block
    code_blocks = re.findall(r'```python(.*?)```', response, re.DOTALL)
    if code_blocks:
        # Return the largest code block (in case there are multiple)
        return max((cb.strip() for cb in code_blocks), key=len)
    # Fallback: extract all contiguous indented or code-like lines
    lines = response.strip().split('\n')
    code_lines = []
    in_code = False
    for line in lines:
        if line.strip() == '' and in_code:
            break
        if (('df' in line and ('[' in line or '.' in line)) or 'plt' in line or 'pd.' in line or 'np.' in line or 'sns.' in line):
            in_code = True
            code_lines.append(line)
        elif in_code:
            # End of code block
            break
    if code_lines:
        return '\n'.join(code_lines)
    # Fallback: return the whole response
    return response.strip()
