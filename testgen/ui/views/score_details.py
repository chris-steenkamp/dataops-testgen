from typing import ClassVar, TypedDict

from testgen.testgen.ui.queries import table_group_queries
from testgen.testgen.ui.queries.scoring_queries import (
    get_score_card_breakdown,
    get_score_card_issues,
    get_table_group_score_card,
)
from testgen.ui.components import widgets as testgen
from testgen.ui.navigation.page import Page
from testgen.ui.navigation.router import Router
from testgen.ui.session import session
from testgen.ui.views.score_dashboard import format_all_scores
from testgen.utils import friendly_score


class ScoreDetailsPage(Page):
    path = "score-dashboard:details"
    can_activate: ClassVar = [
        lambda: session.authentication_status,
    ]

    def render(
        self,
        *,
        name: str,
        category: str = "column_name",
        score_type: str = "score",
        drilldown: str | None = None,
        **_kwargs
    ):
        project_code: str = session.project

        testgen.page_header(
            "Score Details",
            breadcrumbs=[
                {"path": "score-dashboard", "label": "Score Dashboard", "params": {"project_code": project_code}},
                {"label": name},
            ],
        )

        table_group_dict = table_group_queries.get_by_name(project_code, name)

        breakdown: ResultSet | None = None
        issues: ResultSet | None = None

        if drilldown:
            issues = get_issues(project_code, table_group_dict["id"], score_type, category, drilldown)
        else:
            breakdown = get_score_breakdown(project_code, table_group_dict["id"], score_type, category)

        testgen.testgen_component(
            "score_details",
            props={
                "category": category,
                "score_type": score_type,
                "drilldown": drilldown,
                "score": format_all_scores(get_table_group_score_card(project_code, table_group_dict["id"])),
                "breakdown": breakdown,
                "issues": issues,
            },
            on_change_handlers={
                "CategoryChanged": select_category,
                "ScoreTypeChanged": select_score_type,
            },
        )


def get_score_breakdown(project_code: str, table_group_id: str, score_type: str, category: str) -> "ResultSet":
    columns = {"column_name": ["table_name", "column_name"]}.get(category, [category])
    results = get_score_card_breakdown(project_code, table_group_id, score_type, category)
    return {
        "columns": [*columns, "impact", "score", "issue_ct"],
        "items": [{**row, "score": friendly_score(row["score"])} for row in results],
    }


def get_issues(project_code: str, table_group_id: str, score_type: str, category: str, value: str) -> "ResultSet":
    issues = get_score_card_issues(project_code, table_group_id, score_type, category, value)
    return {
        "columns": ["type", "status", "detail", "time"],
        "items": issues,
    }


def select_category(category: str) -> None:
    Router().set_query_params({"category": category})


def select_score_type(score_type: str) -> None:
    Router().set_query_params({"score_type": score_type})


class ResultSet(TypedDict):
    columns: list[str]
    items: list[dict]
