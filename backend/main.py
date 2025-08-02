import sys
from excel_loader import load_excel, get_sheet_names, summarize_schema, sample_data
from question_parser import build_prompt, extract_pandas_code
from slm_interface import send_prompt_to_slm


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <excel_file> [sheet_name]")
        sys.exit(1)
    file_path = sys.argv[1]
    sheet_name = sys.argv[2] if len(sys.argv) > 2 else None

    # Load Excel file
    sheets = get_sheet_names(file_path)
    print(f"Sheet names: {sheets}")
    if sheet_name is None:
        sheet_name = sheets[0]
        print(f"No sheet specified. Using first sheet: {sheet_name}")
    df = load_excel(file_path, sheet_name=sheet_name)

    # Summarize schema and sample
    schema = summarize_schema(df)
    sample = sample_data(df, n=10).to_string(index=False)
    print("Schema summary:", schema)
    print("Sample data:\n", sample)

    # Get user question
    if len(sys.argv) > 3:
        question = " ".join(sys.argv[3:])
    else:
        question = input("Enter your question about this data: ")

    # Build prompt and send to SLM
    prompt = build_prompt(schema, sample, question)
    print("\n---\nPrompt sent to SLM:\n", prompt)
    slm_response = send_prompt_to_slm(prompt)
    print("\n---\nSLM Response:\n", slm_response)

    # Extract Pandas code
    pandas_code = extract_pandas_code(slm_response)
    print("\n---\nExtracted Pandas code:\n", pandas_code)

    # Utility to sanitize SLM code (remove import statements)
    def sanitize_code(code: str) -> str:
        lines = code.splitlines()
        sanitized = []
        for line in lines:
            stripped = line.strip()
            # Remove import statements
            if stripped.startswith("import ") or stripped.startswith("from "):
                continue
            # Remove any line that tries to create a new DataFrame (e.g., 'df = pd.DataFrame', 'df = pd.read_excel', etc.)
            if stripped.startswith("df ="):
                continue
            sanitized.append(line)
        return "\n".join(sanitized)

    # Safely execute Pandas code
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy import stats
    try:
        pandas_code_clean = sanitize_code(pandas_code)
        # Only allow access to 'df', safe builtins, and common data analysis libraries
        safe_builtins = {
            "print": print,
            "max": max,
            "min": min,
            "len": len,
            "sum": sum,
            "abs": abs,
            "range": range,
            "round": round,
            "sorted": sorted,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "any": any,
            "all": all,
            "list": list,
            "dict": dict,
            "set": set,
            "float": float,
            "int": int,
            "str": str,
            "bool": bool,
            "type": type,
            "isinstance": isinstance,
        }
        local_vars = {"df": df}
        exec(
            pandas_code_clean,
            {
                "__builtins__": safe_builtins,
                "pd": pd,
                "np": np,
                "plt": plt,
                "sns": sns,
                "stats": stats,
            },
            local_vars
        )
        # Print any new variables except 'df'
        result_vars = [k for k in local_vars if k != "df"]
        if result_vars:
            for var in result_vars:
                value = local_vars[var]
                # Only print if it's a DataFrame, Series, or a scalar (not modules/functions)
                if isinstance(value, (pd.DataFrame, pd.Series, int, float, str)):
                    print(f"\n---\nResult ({var}):\n", value)
        else:
            print("\n---\n(No result variable found. If your code used print, output should have appeared above.)")
        # Always show plots if any were created
        import matplotlib.pyplot as plt
        if plt.get_fignums():
            plt.show()
    except Exception as e:
        print("\n[ERROR] Failed to execute Pandas code:", e)

if __name__ == "__main__":
    main()
