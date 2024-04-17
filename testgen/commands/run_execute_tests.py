import logging
import threading
import uuid

from testgen.commands.queries.execute_tests_query import CTestExecutionSQL
from testgen.common import (
    AssignConnectParms,
    RetrieveDBResultsToDictList,
    RetrieveTestExecParms,
    RunActionQueryList,
    RunThreadedRetrievalQueryList,
    WriteListToDB,
    date_service,
)
from testgen.common.database.database_service import empty_cache

from .run_execute_cat_tests import run_cat_test_queries
from .run_test_parameter_validation import run_parameter_validation_queries

LOG = logging.getLogger("testgen.cli")


def run_test_queries(strTestRunID, strTestTime, strProjectCode, strTestSuite, minutes_offset=0, spinner=None):
    booErrors = False

    LOG.info("CurrentStep: Retrieving TestExec Parameters")
    dctParms = RetrieveTestExecParms(strProjectCode, strTestSuite)

    # Set Project Connection Parms in common.db_bridgers from retrieved parms
    LOG.info("CurrentStep: Assigning Connection Parms")

    AssignConnectParms(
        dctParms["project_code"],
        dctParms["connection_id"],
        dctParms["project_host"],
        dctParms["project_port"],
        dctParms["project_db"],
        dctParms["table_group_schema"],
        dctParms["project_user"],
        dctParms["sql_flavor"],
        dctParms["url"],
        dctParms["connect_by_url"],
        "PROJECT",
    )

    LOG.info("CurrentStep: Initializing Query Generator")

    clsExecute = CTestExecutionSQL(strProjectCode, dctParms["sql_flavor"], strTestSuite, minutes_offset)
    clsExecute.run_date = strTestTime
    clsExecute.test_run_id = strTestRunID
    booClean = False

    # Add a record in Test Run table for the new Test Run
    strTestRunQuery = clsExecute.AddTestRecordtoTestRunTable()
    lstTestRunQuery = [strTestRunQuery]
    RunActionQueryList("DKTG", lstTestRunQuery)

    try:
        # Retrieve non-CAT Queries
        LOG.info("CurrentStep: Retrieve Non-CAT Queries")
        strQuery = clsExecute.GetTestsNonCAT(booClean)
        lstTestSet = RetrieveDBResultsToDictList("DKTG", strQuery)

        if len(lstTestSet) == 0:
            LOG.debug("0 non-CAT Queries retrieved.")

        if lstTestSet:
            LOG.info("CurrentStep: Preparing Non-CAT Tests")
            lstTestQueries = []
            for dctTest in lstTestSet:
                # Set Test Parms
                clsExecute.ClearTestParms()
                clsExecute.dctTestParms = dctTest
                lstTestQueries.append(clsExecute.GetTestQuery(booClean))
                if spinner:
                    spinner.next()

            # Execute list, returning test results
            LOG.info("CurrentStep: Executing Non-CAT Queries")
            lstTestResults, colResultNames, intErrors = RunThreadedRetrievalQueryList(
                "PROJECT", lstTestQueries, dctParms["max_threads"], spinner
            )

            # Copy test results to DK DB
            LOG.info("CurrentStep: Saving Non-CAT Test Results")
            if lstTestResults:
                WriteListToDB("DKTG", lstTestResults, colResultNames, "test_results")
            if intErrors > 0:
                booErrors = True
                LOG.warning(
                    f"Errors were encountered executing query tests. ({intErrors} errors occurred.) Please check log."
                )
        else:
            LOG.info("No tests found")

    except Exception as e:
        sqlsplit = e.args[0].split("[SQL", 1)
        errorline = sqlsplit[0].replace("'", "''") if len(sqlsplit) > 0 else "unknown error"
        clsExecute.exception_message = f"{type(e).__name__}: {errorline}"
        LOG.info("Updating the test run record with exception message")
        lstTestRunQuery = [clsExecute.PushTestRunStatusUpdateSQL()]
        RunActionQueryList("DKTG", lstTestRunQuery)
        raise

    else:
        return booErrors


def run_execution_steps_in_background(strProjectCode, strTestSuite, minutes_offset=0):
    LOG.info(f"Starting run_execution_steps_in_background against test suite: {strTestSuite}")
    empty_cache()
    background_thread = threading.Thread(
        target=run_execution_steps,
        args=(
            strProjectCode,
            strTestSuite,
            minutes_offset,
        ),
    )
    background_thread.start()


def run_execution_steps(strProjectCode, strTestSuite, minutes_offset=0, spinner=None):
    # Initialize required parms for all three steps
    booErrors = False
    strTestRunID = str(uuid.uuid4())
    strTestTime = date_service.get_now_as_string_with_offset(minutes_offset)

    if spinner:
        spinner.next()

    LOG.info("CurrentStep: Execute Step - Test Validation")
    run_parameter_validation_queries(strTestRunID, strTestTime, strProjectCode, strTestSuite, True)

    LOG.info("CurrentStep: Execute Step - Test Execution")
    if run_test_queries(strTestRunID, strTestTime, strProjectCode, strTestSuite, minutes_offset, spinner):
        booErrors = True

    LOG.info("CurrentStep: Execute Step - CAT Test Execution")
    if run_cat_test_queries(strTestRunID, strTestTime, strProjectCode, strTestSuite, minutes_offset, spinner):
        booErrors = True

    if booErrors:
        str_error_status = "with errors. Check log for details."
    else:
        str_error_status = "successfully."
    message = f"Test Execution completed {str_error_status}"
    return message
