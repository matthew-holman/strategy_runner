from datetime import datetime
from numbers import Number
from typing import Dict

from sqlalchemy import Column


class ColumnMappingMixIn:  # pragma: no cover
    @classmethod
    def column_mapping(cls) -> Dict[str, str]:
        return {
            column_name: cls._get_column_type(column)
            for column_name, column in vars(cls).items()
            if isinstance(column, Column)
        }

    @classmethod
    def get_column(cls, column: str) -> Column:
        return getattr(cls, column)

    @staticmethod
    def _get_column_type(column: Column) -> str:
        try:
            python_type = column.type.python_type
        except NotImplementedError:
            return "text"

        if python_type is str:
            return "text"

        if python_type is bool:
            return "boolean"

        if python_type is datetime:
            return "date"

        if issubclass(python_type, Number):
            return "number"

        return str(python_type)
