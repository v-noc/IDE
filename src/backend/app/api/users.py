from fastapi import APIRouter, HTTPException, Depends
from ..db.dependencies import get_user_collection
from ..db.orm import CollectionManager
from ..models.user import NewUser, User, UpdateUser

router = APIRouter()

@router.post("/", response_model=User)
def create_new_user(user: NewUser, users: CollectionManager[User] = Depends(get_user_collection)):
    return users.create(user)

@router.get("/{key}", response_model=User)
def read_user(key: str, users: CollectionManager[User] = Depends(get_user_collection)):
    user = users.get(key)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{key}", response_model=User)
def update_existing_user(key: str, user_update: UpdateUser, users: CollectionManager[User] = Depends(get_user_collection)):
    updated_user = users.update(key, user_update)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{key}", status_code=204)
def delete_existing_user(key: str, users: CollectionManager[User] = Depends(get_user_collection)):
    if not users.delete(key):
        raise HTTPException(status_code=404, detail="User not found")
    return
