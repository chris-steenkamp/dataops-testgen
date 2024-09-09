import typing

import streamlit as st

import testgen.common.process_service as process_service
import testgen.ui.services.database_service as db
import testgen.ui.services.form_service as fm
import testgen.ui.services.query_service as dq
import testgen.ui.services.test_run_service as test_run_service
from testgen.common import date_service
from testgen.ui.components import widgets as testgen
from testgen.ui.navigation.menu import MenuItem
from testgen.ui.navigation.page import Page
from testgen.ui.session import session


class TestRunsPage(Page):
    path = "test-runs"
    can_activate: typing.ClassVar = [
        lambda: session.authentication_status,
        lambda: session.project != None or "overview",
    ]
    menu_item = MenuItem(icon="labs", label="Data Quality Testing", order=2)

    def render(self, project_code: str | None = None, table_group_id: str | None = None, test_suite_id: str | None = None, **_kwargs) -> None:
        project_code = project_code or st.session_state["project"]
        
        testgen.page_header(
            "Test Runs",
            "https://docs.datakitchen.io/article/dataops-testgen-help/test-results",
        )

        # Setup Toolbar
        group_filter_column, suite_filter_column, actions_column = st.columns([.3, .3, .4], vertical_alignment="bottom")
        testgen.flex_row_end(actions_column)

        with group_filter_column:
            # Table Groups selection -- optional criterion
            df_tg = get_db_table_group_choices(project_code)
            table_groups_id = testgen.toolbar_select(
                options=df_tg,
                value_column="id",
                display_column="table_groups_name",
                default_value=table_group_id,
                bind_to_query="table_group_id",
                label="Table Group",
            )

        with suite_filter_column:
            # Table Groups selection -- optional criterion
            df_ts = get_db_test_suite_choices(project_code, table_groups_id)
            test_suite_id = testgen.toolbar_select(
                options=df_ts,
                value_column="id",
                display_column="test_suite",
                default_value=test_suite_id,
                bind_to_query="test_suite_id",
                label="Test Suite",
            )

        df, show_columns = get_db_test_runs(project_code, table_groups_id, test_suite_id)

        time_columns = ["run_date"]
        date_service.accommodate_dataframe_to_timezone(df, st.session_state, time_columns)

        dct_selected_rows = fm.render_grid_select(df, show_columns)
        dct_selected_row = dct_selected_rows[0] if dct_selected_rows else None

        if actions_column.button(
            f":{'gray' if not dct_selected_row else 'green'}[Test Results　→]",
            help="Review test results for the selected run",
            disabled=not dct_selected_row,
        ):
            self.router.navigate("test-runs:results", { "run_id": dct_selected_row["test_run_id"] })

        fm.render_refresh_button(actions_column)

        if dct_selected_rows:
            open_record_detail(
                dct_selected_rows[0],
            )
            st.markdown(":orange[Click button to access test results for selected run.]")
        else:
            st.markdown(":orange[Select a run to access test results.]")


@st.cache_data(show_spinner=False)
def run_test_suite_lookup_query(str_schema, str_project, str_tg=None):
    str_tg_condition = f" AND s.table_groups_id = '{str_tg}' " if str_tg else ""
    str_sql = f"""
           SELECT s.id::VARCHAR(50),
                  s.test_suite,
                  COALESCE(s.test_suite_description, s.test_suite) AS test_suite_description
             FROM {str_schema}.test_suites s
        LEFT JOIN {str_schema}.table_groups tg ON s.table_groups_id = tg.id
            WHERE s.project_code = '{str_project}' {str_tg_condition}
         ORDER BY s.test_suite
    """
    return db.retrieve_data(str_sql)


@st.cache_data(show_spinner=False)
def get_db_table_group_choices(str_project_code):
    str_schema = st.session_state["dbschema"]
    return dq.run_table_groups_lookup_query(str_schema, str_project_code)


@st.cache_data(show_spinner=False)
def get_db_test_suite_choices(str_project_code, str_table_groups_id=None):
    str_schema = st.session_state["dbschema"]
    return run_test_suite_lookup_query(str_schema, str_project_code, str_table_groups_id)


# @st.cache_data(show_spinner="Retrieving Data")
def get_db_test_runs(str_project_code, str_tg=None, str_ts=None):
    str_schema = st.session_state["dbschema"]
    str_tg_condition = f" AND s.table_groups_id = '{str_tg}' " if str_tg else ""
    str_ts_condition = f" AND s.id = '{str_ts}' " if str_ts else ""
    str_sql = f"""
            SELECT r.test_starttime as run_date,
                   s.test_suite, s.test_suite_description,
                   r.status,
                   r.duration,
                   r.test_ct, r.passed_ct, r.failed_ct, r.warning_ct, r.error_ct,
                   ROUND(100.0 * r.passed_ct::DECIMAL(12, 4) / r.test_ct::DECIMAL(12, 4), 3) as passed_pct,
                   COALESCE(r.log_message, 'Test run completed successfully.') as log_message,
                   r.column_ct, r.column_failed_ct, r.column_warning_ct,
                   ROUND(100.0 * (r.column_ct - r.column_failed_ct - r.column_warning_ct)::DECIMAL(12, 4) / r.column_ct::DECIMAL(12, 4), 3) as column_passed_pct,
                   r.id::VARCHAR as test_run_id,
                   p.project_name,
                   s.table_groups_id::VARCHAR, tg.table_groups_name, tg.table_group_schema, process_id
              FROM {str_schema}.test_runs r
            INNER JOIN {str_schema}.test_suites s
              ON (r.test_suite_id = s.id)
            INNER JOIN {str_schema}.table_groups tg
              ON (s.table_groups_id = tg.id)
            INNER JOIN {str_schema}.projects p
               ON (s.project_code = p.project_code)
          WHERE s.project_code = '{str_project_code}' {str_tg_condition} {str_ts_condition}
          ORDER BY r.test_starttime DESC;
    """

    show_columns = [
        "run_date",
        "test_suite",
        "test_suite_description",
        "status",
        "duration",
        "test_ct",
        "failed_ct",
        "warning_ct",
    ]

    return db.retrieve_data(str_sql), show_columns


def open_record_detail(dct_selected_row):
    bottom_left_column, bottom_right_column = st.columns([0.5, 0.5])

    with bottom_left_column:
        # Show Run Detail
        lst_detail_columns = [
            "test_suite",
            "test_suite_description",
            "run_date",
            "status",
            "log_message",
            "table_groups_name",
            "test_ct",
            "passed_ct",
            "failed_ct",
            "warning_ct",
            "error_ct",
        ]
        fm.render_html_list(dct_selected_row, lst_detail_columns, "Run Information", 500)

    with bottom_right_column:
        st.write("<br/><br/>", unsafe_allow_html=True)
        _, button_column = st.columns([0.3, 0.7])
        with button_column:
            enable_kill_button = dct_selected_row and dct_selected_row["process_id"] is not None and dct_selected_row["status"] == "Running"

            if enable_kill_button:
                if st.button(
                    ":red[Cancel Run]",
                    help="Kill the selected test run",
                    use_container_width=True,
                    disabled=not enable_kill_button,
                ):
                    process_id = dct_selected_row["process_id"]
                    test_run_id = dct_selected_row["test_run_id"]
                    status, message = process_service.kill_test_run(process_id)

                    if status:
                        test_run_service.update_status(test_run_id, "Cancelled")

                    fm.reset_post_updates(str_message=f":{'green' if status else 'red'}[{message}]", as_toast=True)
