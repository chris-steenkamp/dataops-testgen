import pandas as pd
import streamlit as st

import testgen.ui.services.database_service as db


@st.cache_data(show_spinner=False)
def get_by_table_group(schema, project_code, table_group_id):
    sql = f"""
            SELECT
                id::VARCHAR(50),
                project_code, test_suite,
                connection_id::VARCHAR(50),
                table_groups_id::VARCHAR(50),
                test_suite_description, test_action,
                case when severity is null then 'Inherit' else severity end,
                export_to_observability, test_suite_schema, component_key, component_type, component_name
            FROM {schema}.test_suites
            WHERE project_code = '{project_code}'
            AND table_groups_id = '{table_group_id}'
            ORDER BY test_suite;
    """
    return db.retrieve_data(sql)


def edit(schema, test_suite):
    sql = f"""UPDATE {schema}.test_suites
                SET
                    test_suite='{test_suite["test_suite"]}',
                    test_suite_description='{test_suite["test_suite_description"]}',
                    test_action=NULLIF('{test_suite["test_action"]}', ''),
                    severity=NULLIF('{test_suite["severity"]}', 'Inherit'),
                    export_to_observability='{'Y' if test_suite["export_to_observability"] else 'N'}',
                    test_suite_schema=NULLIF('{test_suite["test_suite_schema"]}', ''),
                    component_key=NULLIF('{test_suite["component_key"]}', ''),
                    component_type=NULLIF('{test_suite["component_type"]}', ''),
                    component_name=NULLIF('{test_suite["component_name"]}', '')
                where
                    id = '{test_suite["id"]}';
                    """
    db.execute_sql(sql)
    st.cache_data.clear()


def add(schema, test_suite):
    sql = f"""INSERT INTO {schema}.test_suites
                (id,
                project_code, test_suite, connection_id, table_groups_id, test_suite_description, test_action,
                severity, export_to_observability, test_suite_schema, component_key, component_type,
                component_name)
            SELECT
                gen_random_uuid(),
                '{test_suite["project_code"]}',
                '{test_suite["test_suite"]}',
                '{test_suite["connection_id"]}',
                '{test_suite["table_groups_id"]}',
                NULLIF('{test_suite["test_suite_description"]}', ''),
                NULLIF('{test_suite["test_action"]}', ''),
                NULLIF('{test_suite["severity"]}', 'Inherit'),
                '{'Y' if test_suite["export_to_observability"] else 'N' }'::character varying,
                NULLIF('{test_suite["test_suite_schema"]}', ''),
                NULLIF('{test_suite["component_key"]}', ''),
                NULLIF('{test_suite["component_type"]}', ''),
                NULLIF('{test_suite["component_name"]}', '')
                ;"""
    db.execute_sql(sql)
    st.cache_data.clear()


def delete(schema, test_suite_ids: list[str]):
    if not test_suite_ids:
        raise ValueError("No table group is specified.")

    ids_str = ",".join([f"'{item}'" for item in test_suite_ids])
    sql = f"""DELETE FROM {schema}.test_suites WHERE id in ({ids_str})"""
    db.execute_sql(sql)
    st.cache_data.clear()


def get_test_suite_dependencies(schema: str, test_suite_ids: list[str]) -> pd.DataFrame:
    ids_str = ", ".join([f"'{item}'" for item in test_suite_ids])
    sql = f"""
        SELECT DISTINCT test_suite_id FROM {schema}.test_definitions WHERE test_suite_id in ({ids_str})
        UNION
        SELECT DISTINCT test_suite_id FROM {schema}.test_results WHERE test_suite_id in ({ids_str});
    """
    return db.retrieve_data(sql)


def get_test_suite_usage(schema: str, test_suite_ids: list[str]) -> pd.DataFrame:
    ids_str = ", ".join([f"'{item}'" for item in test_suite_ids])
    sql = f"""
        SELECT DISTINCT test_suite_id FROM {schema}.test_runs WHERE test_suite_id in ({ids_str}) AND status = 'Running'
    """
    return db.retrieve_data(sql)


def get_test_suite_refresh_check(schema, test_suite_id):
    sql = f"""
           SELECT COUNT(*) as test_ct,
                  SUM(CASE WHEN COALESCE(d.lock_refresh, 'N') = 'N' THEN 1 ELSE 0 END) as unlocked_test_ct,
                  SUM(CASE WHEN COALESCE(d.lock_refresh, 'N') = 'N' AND d.last_manual_update IS NOT NULL THEN 1 ELSE 0 END) as unlocked_edits_ct
             FROM {schema}.test_definitions d
           INNER JOIN {schema}.test_types t
              ON (d.test_type = t.test_type)
            WHERE d.test_suite_id = '{test_suite_id}'
              AND t.run_type = 'CAT'
              AND t.selection_criteria IS NOT NULL;
"""
    return db.retrieve_data_list(sql)[0]


def get_generation_sets(schema):
    sql = f"""
           SELECT DISTINCT generation_set
             FROM {schema}.generation_sets
           ORDER BY generation_set;
"""
    return db.retrieve_data(sql)


def lock_edited_tests(schema, test_suite_id):
    sql = f"""
           UPDATE {schema}.test_definitions
              SET lock_refresh = 'Y'
            WHERE test_suite_id = '{test_suite_id}'
              AND last_manual_update IS NOT NULL
              AND lock_refresh = 'N';
"""
    db.execute_sql(sql)
    return True
