from sqlalchemy.orm import Session

import databases.current as db

# Shared by all transaction classes, so objects fetched in one class stay attached when another commits.
session = Session(bind=db.engine, expire_on_commit=False)
