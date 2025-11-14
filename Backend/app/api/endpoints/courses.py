from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database.session import get_db
from ...database import crud
from ...auth.security import get_current_active_user, get_current_admin_user
from ...schemas.reservation import Course, CourseCreate
from ...schemas.user import User

router = APIRouter()

@router.get("/courses/", response_model=List[Course])
async def read_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    courses = crud.get_courses(db, skip=skip, limit=limit)
    return courses

@router.post("/courses/", response_model=Course)
async def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return crud.create_course(db=db, course=course)