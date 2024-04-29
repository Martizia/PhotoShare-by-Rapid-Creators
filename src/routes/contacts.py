import pathlib
from datetime import date, timedelta

from fastapi import (APIRouter, Depends, File, HTTPException, Path, Query,
                     UploadFile, status)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import Contact, Role, User
from src.repository import contacts as repository_contacts
from src.schemas.schemas import ContactModel, ContactResponse
from src.services.auth import auth_service
from src.services.roles import RoleAccess

router = APIRouter(prefix='/contacts')

access_to_route_all = RoleAccess([Role.admin, Role.moderator])

@router.get("/",
            response_model=list[ContactResponse],
            tags=['Contacts'],
            dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def get_contacts(limit: int = 100,
                       offset: int = 0,
                       db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user)):
    contacts = await repository_contacts.get_contacts(limit, offset, db, current_user)
    return contacts

@router.get("/all",
            response_model=list[ContactResponse],
            tags=['Contacts'],
            dependencies=[Depends(access_to_route_all), Depends(RateLimiter(times=1, seconds=20))])
async def get_all_contacts(limit: int = 100,
                           offset: int = 0,
                           db: AsyncSession = Depends(get_db)):
    contacts = await repository_contacts.get_all_contacts(limit, offset, db)
    return contacts

@router.post("/",
             response_model=ContactResponse,
             tags=['Contacts'],
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RateLimiter(times=1, seconds=45))])
async def create_contact(body: ContactModel,
                         db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    email_search = select(Contact).filter_by(email=body.email, user=current_user)
    result = await db.execute(email_search)
    email_exists = result.scalar_one_or_none()

    number_search = select(Contact).filter_by(contact_number=body.contact_number, user=current_user)
    result = await db.execute(number_search)
    number_exists = result.scalar_one_or_none()

    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with the mentioned email already exists."
        )

    if number_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with the mentioned contact number already exists."
        )

    return await repository_contacts.create_contact(body, current_user, db)

@router.get("/{contact_id}",
            response_model=ContactResponse,
            tags=['Contacts'],
            dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def get_contact(contact_id: int = Path(ge=1),
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.get_contact(contact_id, current_user, db)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return contact

@router.put("/{contact_id}",
            response_model=ContactResponse,
            tags=['Contacts'],
            dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def update_contact(body: ContactModel,
                         contact_id: int = Path(ge=1),
                         db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    email_search = select(Contact).filter_by(email=body.email, user=current_user)
    result = await db.execute(email_search)
    email_exists = result.scalar_one_or_none()

    number_search = select(Contact).filter_by(contact_number=body.contact_number, user=current_user)
    result = await db.execute(number_search)
    number_exists = result.scalar_one_or_none()

    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with the mentioned email already exists."
        )

    if number_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with the mentioned contact number already exists."
        )

    contact = await repository_contacts.update_contact(contact_id, body, current_user, db)

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with id {contact_id} not found")
    return contact

@router.delete("/{contact_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               tags=['Contacts'],
               dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def remove_contact(contact_id: int = Path(ge=1),
                         db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.remove_contact(contact_id, current_user, db)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return contact

@router.get("/search/",
            response_model=list[ContactResponse] | ContactResponse,
            tags=['Contacts'],
            dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def find_contact(first_name: str = Query(None),
                       last_name: str = Query(None),
                       email: str = Query(None),
                       db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user)):
    if first_name:
        return await repository_contacts.find_contact_by_first_name(first_name, current_user, db)
    elif last_name:
        return await repository_contacts.find_contact_by_last_name(last_name, current_user, db)
    elif email:
        return await repository_contacts.find_contact_by_email(email, current_user, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide at least one parameter"
        )

@router.get("/birthdays/",
            response_model=list[ContactResponse],
            tags=['Birthdays'],
            dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def get_upcoming_birthdays(skip: int = 0,
                                 limit: int = 100,
                                 db: AsyncSession = Depends(get_db),
                                 current_user: User = Depends(auth_service.get_current_user)):
    current_date = date.today()
    to_date = current_date + timedelta(days=7)

    birthdays = await repository_contacts.upcoming_birthdays(current_date, to_date, skip, limit, current_user, db)
    return birthdays

MAX_FILE_SIZE = 1_000_000


@router.post("/upload-file/",
             tags=['Upload File'],
             dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def upload_file(file: UploadFile = File()):
    pathlib.Path("uploads").mkdir(exist_ok=True)
    file_path = f"uploads/{file.filename}"

    file_size = 0
    with open(file_path, "wb") as f:
        while True:
            chunk = await file.read(1024)
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                f.close()
                pathlib.Path(file_path).unlink()
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large, max size is {MAX_FILE_SIZE} bytes"
                )
            f.write(chunk)
    return {"file_path": file_path}
