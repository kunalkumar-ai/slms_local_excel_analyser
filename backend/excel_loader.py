import pandas as pd
from typing import List, Dict, Any, Optional


def load_excel(file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Loads an Excel file and returns a DataFrame for the specified sheet.
    If sheet_name is None, loads the first sheet.
    """
    return pd.read_excel(file_path, sheet_name=sheet_name)


def get_sheet_names(file_path: str) -> List[str]:
    """
    Returns a list of sheet names in the Excel file.
    """
    excel_file = pd.ExcelFile(file_path)
    return excel_file.sheet_names


def summarize_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Returns a summary of the DataFrame: column names, types, and non-null counts.
    """
    summary = {
        'columns': list(df.columns),
        'dtypes': df.dtypes.astype(str).to_dict(),
        'non_null': df.notnull().sum().to_dict(),
        'shape': df.shape
    }
    return summary


def sample_data(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Returns the first n rows of the DataFrame as a sample.
    """
    return df.head(n)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python excel_loader.py <excel_file>")
        sys.exit(1)
    file_path = sys.argv[1]
    print(f"Sheet names: {get_sheet_names(file_path)}")
    df = load_excel(file_path)
    print("Schema summary:", summarize_schema(df))
    print("Sample data:\n", sample_data(df))
