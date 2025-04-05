from main import create_app  # type: ignore
from database.init import init_db  # type: ignore

init_db()

app = create_app()
