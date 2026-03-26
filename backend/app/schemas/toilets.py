from typing import Any

from pydantic import BaseModel, Field, field_validator


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class ToiletStallCountsBase(BaseModel):
    male_toilet_count: int = Field(default=0, ge=0)
    male_urinal_count: int = Field(default=0, ge=0)
    male_disabled_toilet_count: int = Field(default=0, ge=0)
    male_disabled_urinal_count: int = Field(default=0, ge=0)
    male_child_toilet_count: int = Field(default=0, ge=0)
    male_child_urinal_count: int = Field(default=0, ge=0)
    female_toilet_count: int = Field(default=0, ge=0)
    female_disabled_toilet_count: int = Field(default=0, ge=0)
    female_child_toilet_count: int = Field(default=0, ge=0)


class ToiletBase(BaseModel):
    local_government_code: str = Field(min_length=1)
    toilet_type_name: str = Field(min_length=1)
    name: str = Field(min_length=1)
    legal_basis_name: str | None = None
    road_address: str | None = None
    lot_address: str | None = None
    management_agency: str | None = None
    phone_number: str | None = None
    opening_hours_type: str | None = None
    opening_hours_detail: str | None = None
    installation_year_month: str | None = None
    latitude: float = Field(ge=33.0, le=39.5)
    longitude: float = Field(ge=124.0, le=132.5)
    ownership_type_name: str | None = None
    sewage_process_type_name: str | None = None
    safety_target_flag: bool = False
    emergency_bell_flag: bool = False
    emergency_bell_location: str | None = None
    entrance_cctv_flag: bool = False
    diaper_changing_table_flag: bool = False
    diaper_changing_table_location: str | None = None
    remodeling_year_month: str | None = None
    reference_date: str | None = None
    last_modified_at: str | None = None

    @field_validator(
        "local_government_code",
        "toilet_type_name",
        "name",
        "legal_basis_name",
        "road_address",
        "lot_address",
        "management_agency",
        "phone_number",
        "opening_hours_type",
        "opening_hours_detail",
        "installation_year_month",
        "ownership_type_name",
        "sewage_process_type_name",
        "emergency_bell_location",
        "diaper_changing_table_location",
        "remodeling_year_month",
        "reference_date",
        "last_modified_at",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            return clean_text(value)
        return value

    @field_validator("lot_address")
    @classmethod
    def validate_any_address(cls, value: str | None, info: Any) -> str | None:
        road_address = info.data.get("road_address")
        if not road_address and not value:
            raise ValueError("road_address 또는 lot_address 중 하나는 필요합니다.")
        return value


class ToiletCreate(ToiletBase, ToiletStallCountsBase):
    management_number: str = Field(min_length=1)


class ToiletUpdate(BaseModel):
    local_government_code: str | None = None
    toilet_type_name: str | None = None
    name: str | None = None
    legal_basis_name: str | None = None
    road_address: str | None = None
    lot_address: str | None = None
    management_agency: str | None = None
    phone_number: str | None = None
    opening_hours_type: str | None = None
    opening_hours_detail: str | None = None
    installation_year_month: str | None = None
    latitude: float | None = Field(default=None, ge=33.0, le=39.5)
    longitude: float | None = Field(default=None, ge=124.0, le=132.5)
    ownership_type_name: str | None = None
    sewage_process_type_name: str | None = None
    safety_target_flag: bool | None = None
    emergency_bell_flag: bool | None = None
    emergency_bell_location: str | None = None
    entrance_cctv_flag: bool | None = None
    diaper_changing_table_flag: bool | None = None
    diaper_changing_table_location: str | None = None
    remodeling_year_month: str | None = None
    reference_date: str | None = None
    last_modified_at: str | None = None
    male_toilet_count: int | None = Field(default=None, ge=0)
    male_urinal_count: int | None = Field(default=None, ge=0)
    male_disabled_toilet_count: int | None = Field(default=None, ge=0)
    male_disabled_urinal_count: int | None = Field(default=None, ge=0)
    male_child_toilet_count: int | None = Field(default=None, ge=0)
    male_child_urinal_count: int | None = Field(default=None, ge=0)
    female_toilet_count: int | None = Field(default=None, ge=0)
    female_disabled_toilet_count: int | None = Field(default=None, ge=0)
    female_child_toilet_count: int | None = Field(default=None, ge=0)


class ToiletResponse(ToiletCreate):
    ownership_type_name: str | None = None
    sewage_process_type_name: str | None = None
    distance_meters: float | None = None


class ToiletListResponse(BaseModel):
    total: int
    items: list[ToiletResponse]


class ToiletMarkerResponse(BaseModel):
    management_number: str
    name: str
    toilet_type_name: str
    latitude: float
    longitude: float
    road_address: str | None = None
    lot_address: str | None = None
    emergency_bell_flag: bool
    entrance_cctv_flag: bool
    diaper_changing_table_flag: bool
    distance_meters: float | None = None
    icon: str = "🚻"
    icon_size: int = 18


class ToiletImportResponse(BaseModel):
    imported_rows: int
    replaced_existing: bool
