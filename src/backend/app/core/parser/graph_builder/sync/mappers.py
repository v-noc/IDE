from app.core.model.properties import CodePosition
from app.core.parser.scope_manager.models import ScopeModel


def map_scope_to_position(scope: ScopeModel) -> CodePosition:
    """Map ScopeModel position fields to CodePosition."""
    return CodePosition(
        line_no=scope.start_line,
        col_offset=scope.start_col,
        end_line_no=scope.end_line,
        end_col_offset=scope.end_col,
    )
