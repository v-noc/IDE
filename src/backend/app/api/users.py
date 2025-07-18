from fastapi import APIRouter, HTTPException, Depends
from ..db.dependencies import get_db_service
from ..db.service import DatabaseService
from ..models.user import NewUser, User, UpdateUser
from ..models.follows import Follows, NewFollows

router = APIRouter()

@router.post("/", response_model=User)
def create_new_user(user: NewUser, db: DatabaseService = Depends(get_db_service)):
    return db.users.create(user)

@router.get("/by_email/{email}", response_model=User)
def read_user_by_email(email: str, db: DatabaseService = Depends(get_db_service)):
    user = db.users.find_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{key}", response_model=User)
def read_user(key: str, db: DatabaseService = Depends(get_db_service)):
    user = db.users.get(key)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{key}", response_model=User)
def update_existing_user(key: str, user_update: UpdateUser, db: DatabaseService = Depends(get_db_service)):
    updated_user = db.users.update(key, user_update)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{key}", status_code=204)
def delete_existing_user(key: str, db: DatabaseService = Depends(get_db_service)):
    if not db.users.delete(key):
        raise HTTPException(status_code=404, detail="User not found")
    return

@router.post("/{from_key}/follows/{to_key}", response_model=Follows)
def follow_user(from_key: str, to_key: str, db: DatabaseService = Depends(get_db_service)):
    from_user_doc_id = f"users/{from_key}"
    to_user_doc_id = f"users/{to_key}"
    return db.follows.create(from_user_doc_id, to_user_doc_id, NewFollows())
