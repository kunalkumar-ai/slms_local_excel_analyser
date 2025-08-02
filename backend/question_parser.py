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

Always provide the complete code (including imports and plotting commands) in a single Python code block.

Always assign your answer to a variable named result and print it using print(result).


"""
    return prompt

def extract_pandas_code(response: str) -> str:
    """
    Extract and concatenate all code blocks from the SLM response.
    Handles both ```python and ``` blocks.
    If no code block is found, fallback to a simple heuristic.
    """
    import re

    # Regex to find all code blocks, with or without 'python', case-insensitive
    code_blocks = re.findall(r'```(?:python)?\s*([\s\S]*?)\s*```', response, re.IGNORECASE | re.DOTALL)

    if code_blocks:
        # Concatenate all found code blocks, stripping whitespace from each
        full_code = "\n".join(block.strip() for block in code_blocks).strip()
        if full_code:
            return full_code

    # Fallback if no code blocks are found or they are empty
    lines = response.strip().split('\n')
    code_lines = []
    for line in lines:
        stripped = line.strip()
        # Heuristic for what looks like a code line
        if (
            stripped.startswith(('df', 'plt.', 'pd.', 'np.', 'sns.')) or
            ('=' in stripped and not stripped.startswith('#'))
        ):
            code_lines.append(line)

    if code_lines:
        return '\n'.join(code_lines)

    # Final fallback: return the whole response stripped, as it might be a single line of code
    return response.strip()
