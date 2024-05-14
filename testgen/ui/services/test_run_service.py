import streamlit as st

import testgen.ui.queries.test_run_queries as test_run_queries


def cascade_delete(test_suite_names):
    schema = st.session_state["dbschema"]
    test_run_queries.cascade_delete(schema, test_suite_names)
