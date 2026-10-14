from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.permissions import require_roles
from app.database.database import get_db
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.core.security import hash_password


DEFAULT_ROLE_NAME = "user"
ADMIN_ROLE_NAME = "admin"


def _forbid_self_lockout(
    target: User,
    current_user: User,
    detail: str
) -> None:
    """
    An admin cannot deactivate, demote or delete their own account.
    This guarantees the system never ends up without an active admin.
    """

    if target.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Public registration. New accounts always get the default role;
    only an admin can change it afterwards through PUT /users/{user_id}.
    """

    existing_user = db.query(User).filter(User.username == user.username).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    existing_email = db.query(User).filter(User.email == user.email).first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )

    role = db.query(Role).filter(Role.name == DEFAULT_ROLE_NAME).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default role is not configured. Run the seed script."
        )

    new_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name or "",
        hashed_password=hash_password(user.password),
        role_id=role.id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_data = user_update.model_dump(exclude_unset=True)

    for field in ("role_id", "is_active"):
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"{field} cannot be null"
            )

    if "role_id" in update_data:
        role = db.query(Role).filter(Role.id == update_data["role_id"]).first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        if role.name != ADMIN_ROLE_NAME:
            _forbid_self_lockout(
                user,
                current_user,
                "You cannot remove your own admin role"
            )

    if update_data.get("is_active") is False:
        _forbid_self_lockout(
            user,
            current_user,
            "You cannot deactivate your own account"
        )

    if "email" in update_data:
        existing_email = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user.id
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    _forbid_self_lockout(
        user,
        current_user,
        "You cannot deactivate your own account"
    )

    user.is_active = False

    db.commit()
    db.refresh(user)

    return user


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = True

    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    _forbid_self_lockout(
        user,
        current_user,
        "You cannot delete your own account"
    )

    # Documents and chunks are removed by ON DELETE CASCADE; the stored
    # files have to be removed by hand once the transaction succeeds.
    file_paths = [Path(document.filepath) for document in user.documents]

    db.delete(user)
    db.commit()

    for file_path in file_paths:
        file_path.unlink(missing_ok=True)

    return None