import streamlit as st
import pandas as pd
import io
import sys
import os
from pathlib import Path

# Import backend logic
BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_PATH))

import excel_loader
import question_parser
import slm_interface

st.set_page_config(page_title="Local Excel Data Analyst", layout="wide")
st.title("🔒 Local Excel Data Analyst")

# Session state for file and dataframe
def get_state():
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'schema' not in st.session_state:
        st.session_state.schema = None
    if 'sheet_names' not in st.session_state:
        st.session_state.sheet_names = None
    if 'sample' not in st.session_state:
        st.session_state.sample = None
    if 'sheet' not in st.session_state:
        st.session_state.sheet = None
get_state()

# File uploader
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])  # Only Excel

if uploaded_file:
    # Save uploaded file to a temp location for backend compatibility
    temp_path = BACKEND_PATH / "_uploaded_temp.xlsx"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())
    # Load sheets
    sheet_names = excel_loader.get_sheet_names(str(temp_path))
    st.session_state.sheet_names = sheet_names
    # Sheet selector
    sheet = st.selectbox("Select sheet", sheet_names, index=0)
    st.session_state.sheet = sheet
    # Load df
    df = excel_loader.load_excel(str(temp_path), sheet)
    st.session_state.df = df
    # Schema summary
    schema = excel_loader.summarize_schema(df)
    st.session_state.schema = schema
    # Sample data
    sample = df.head(10)
    st.session_state.sample = sample
    # Show schema and sample
    st.subheader("Schema summary")
    st.json(schema)
    st.subheader("Sample data")
    st.dataframe(sample)

if st.session_state.df is not None:
    st.markdown("---")
    st.subheader("Ask a question about your data:")
    user_question = st.text_input("Natural language question", "e.g. plot the profit for January month")
    if st.button("Submit question") and user_question.strip():
        # Build prompt
        prompt = question_parser.build_prompt(
            st.session_state.schema,
            st.session_state.sample,
            user_question
        )
        st.code(prompt, language="markdown")
        # Query SLM
        with st.spinner("Querying local SLM..."):
            slm_response = slm_interface.send_prompt_to_slm(prompt)
        st.subheader("SLM Response")
        st.code(slm_response, language="markdown")
        # Extract Pandas code
        pandas_code = question_parser.extract_pandas_code(slm_response)
        st.subheader("Extracted Pandas code")
        st.code(pandas_code, language="python")
        # Run code safely
        from contextlib import redirect_stdout, redirect_stderr
        import matplotlib.pyplot as plt
        import numpy as np
        import seaborn as sns
        from scipy import stats
        import builtins

        # Sanitize code (reuse backend logic if possible)
        def sanitize_code(code: str) -> str:
            lines = code.splitlines()
            sanitized = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    continue
                if stripped.startswith("df ="):
                    continue
                sanitized.append(line)
            return "\n".join(sanitized)

        pandas_code_clean = sanitize_code(pandas_code)
        safe_builtins = {
            "print": print,
            "max": max,
            "min": min,
            "len": len,
            "sum": sum,
            "abs": abs,
            "range": range
        }
        local_vars = {"df": st.session_state.df}
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
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
            # Show printed output
            std_out_val = stdout.getvalue()
            std_err_val = stderr.getvalue()
            if std_out_val:
                st.text("[stdout]\n" + std_out_val)
            if std_err_val:
                st.text("[stderr]\n" + std_err_val)
            # Show new variables
            result_vars = [k for k in local_vars if k != "df"]
            for var in result_vars:
                value = local_vars[var]
                if isinstance(value, (pd.DataFrame, pd.Series, int, float, str)):
                    st.write(f"**Result ({var}):**")
                    st.write(value)
            # Show plot if created
            figs = [plt.figure(n) for n in plt.get_fignums()]
            for fig in figs:
                st.pyplot(fig)
            plt.close('all')
        except Exception as e:
            st.error(f"[ERROR] Failed to execute Pandas code: {e}")
