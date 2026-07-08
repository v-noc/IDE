from app.walkthrough.schemas import BlockPlan, PlannedBlock, VisitNode
from app.walkthrough.validators import validate_block_plan


def _visit() -> VisitNode:
    return VisitNode(
        node_id="fn",
        name="fn",
        qname="fn",
        node_type="function",
        description="",
        level=0,
        order=0,
        parent_order=None,
        target_id="fn",
        mode="full",
        first_seen_order=None,
        has_code=True,
        start_line=10,
        end_line=50,
        line_count=41,
        gated=True,
    )


def test_overlapping_blocks_fail_validation():
    plan = BlockPlan(
        reasoning="bad",
        blocks=[
            PlannedBlock(start_line=10, end_line=30, focus="a"),
            PlannedBlock(start_line=15, end_line=40, focus="b"),
        ],
    )

    errors = validate_block_plan(plan, _visit())

    assert any("overlaps the previous block" in error for error in errors)
