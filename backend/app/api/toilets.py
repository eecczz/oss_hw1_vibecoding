from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies import get_current_user
from app.repositories.toilets import (
    create_toilet,
    delete_toilet,
    get_toilet,
    list_map_markers,
    list_nearby_toilets,
    list_toilets,
    update_toilet,
)
from app.schemas.toilets import (
    ToiletCreate,
    ToiletImportResponse,
    ToiletListResponse,
    ToiletMarkerResponse,
    ToiletResponse,
    ToiletUpdate,
)
from app.services.importer import import_csv_to_database
from app.settings import settings


router = APIRouter(
    prefix="/api/v1/toilets",
    tags=["toilets"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/import", response_model=ToiletImportResponse)
def import_toilets(replace_existing: bool = False) -> ToiletImportResponse:
    imported_rows = import_csv_to_database(settings.csv_path, replace_existing=replace_existing)
    return ToiletImportResponse(
        imported_rows=imported_rows,
        replaced_existing=replace_existing,
    )


@router.get("", response_model=ToiletListResponse)
def read_toilets(
    query: str | None = None,
    toilet_type_name: str | None = None,
    local_government_code: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> ToiletListResponse:
    payload = list_toilets(
        query=query,
        toilet_type_name=toilet_type_name,
        local_government_code=local_government_code,
        limit=limit,
        offset=offset,
    )
    return ToiletListResponse(**payload)


@router.get("/map", response_model=list[ToiletMarkerResponse])
def read_map_markers(
    limit: int | None = Query(default=None, ge=1, le=100000)
) -> list[ToiletMarkerResponse]:
    return [ToiletMarkerResponse(**item) for item in list_map_markers(limit=limit)]


@router.get("/nearby", response_model=list[ToiletMarkerResponse])
def read_nearby_toilets(
    latitude: float = Query(ge=33.0, le=39.5),
    longitude: float = Query(ge=124.0, le=132.5),
    limit: int = Query(default=100, ge=1, le=300),
) -> list[ToiletMarkerResponse]:
    return [
        ToiletMarkerResponse(**item)
        for item in list_nearby_toilets(latitude=latitude, longitude=longitude, limit=limit)
    ]


@router.get("/{management_number}", response_model=ToiletResponse)
def read_toilet(management_number: str) -> ToiletResponse:
    return ToiletResponse(**get_toilet(management_number))


@router.post("", response_model=ToiletResponse, status_code=status.HTTP_201_CREATED)
def create_toilet_item(payload: ToiletCreate) -> ToiletResponse:
    return ToiletResponse(**create_toilet(payload))


@router.put("/{management_number}", response_model=ToiletResponse)
def update_toilet_item(management_number: str, payload: ToiletUpdate) -> ToiletResponse:
    return ToiletResponse(**update_toilet(management_number, payload))


@router.delete("/{management_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_toilet_item(management_number: str) -> Response:
    delete_toilet(management_number)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
