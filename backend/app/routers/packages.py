from __future__ import annotations
"""
app/routers/packages.py — Package CRUD endpoints (admin-only).

All endpoints require a valid JWT supplied as Authorization: Bearer <token>.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin, get_db
from app.models.admin import Admin
from app.schemas.package import (
    PackageCreate,
    PackageListResponse,
    PackageOut,
    PackageUpdate,
)
from app.services import package_service

router = APIRouter(prefix="/api/packages", tags=["Packages"])


@router.post(
    "",
    response_model=PackageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new package (admin)",
)
def create_package(
    body: PackageCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
) -> PackageOut:
    package = package_service.create_package(db, data=body, admin_id=current_admin.id)
    return PackageOut.model_validate(package)


@router.get(
    "",
    response_model=PackageListResponse,
    summary="List all packages (admin, paginated)",
)
def list_packages(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> PackageListResponse:
    total, items = package_service.list_packages(db, page=page, page_size=page_size)
    return PackageListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get(
    "/{package_id}",
    response_model=PackageOut,
    summary="Get package details (admin)",
)
def get_package(
    package_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> PackageOut:
    package = package_service.get_package_by_id(db, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return PackageOut.model_validate(package)


@router.patch(
    "/{package_id}",
    response_model=PackageOut,
    summary="Update package metadata (admin)",
)
def update_package(
    package_id: uuid.UUID,
    body: PackageUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> PackageOut:
    package = package_service.get_package_by_id(db, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    updated = package_service.update_package(db, package, data=body)
    return PackageOut.model_validate(updated)


@router.delete(
    "/{package_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a package (admin)",
    response_model=None,
)
def delete_package(
    package_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    package = package_service.get_package_by_id(db, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    package_service.soft_delete_package(db, package)
