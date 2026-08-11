"""Import every model module here so Alembic's autogenerate (and Base.metadata.create_all)
sees the full schema from a single import of app.models.
"""
from app.models.base import Base  # noqa: F401
from app.models import foundation  # noqa: F401
from app.models import accounting  # noqa: F401
from app.models import master_data  # noqa: F401
from app.models import leasing  # noqa: F401
from app.models import inventory  # noqa: F401
