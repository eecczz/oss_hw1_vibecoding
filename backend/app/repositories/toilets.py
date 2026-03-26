import math
import sqlite3
from typing import Any

from fastapi import HTTPException, status

from app.db.database import get_connection
from app.db.schema import SCHEMA_SQL
from app.schemas.toilets import ToiletCreate, ToiletUpdate


STALL_FIELDS = [
    "male_toilet_count",
    "male_urinal_count",
    "male_disabled_toilet_count",
    "male_disabled_urinal_count",
    "male_child_toilet_count",
    "male_child_urinal_count",
    "female_toilet_count",
    "female_disabled_toilet_count",
    "female_child_toilet_count",
]


BASE_SELECT = """
SELECT
    t.management_number,
    t.local_government_code,
    tt.name AS toilet_type_name,
    t.name,
    t.legal_basis_name,
    t.road_address,
    t.lot_address,
    t.management_agency,
    t.phone_number,
    t.opening_hours_type,
    t.opening_hours_detail,
    t.installation_year_month,
    t.latitude,
    t.longitude,
    ot.name AS ownership_type_name,
    spt.name AS sewage_process_type_name,
    t.safety_target_flag,
    t.emergency_bell_flag,
    t.emergency_bell_location,
    t.entrance_cctv_flag,
    t.diaper_changing_table_flag,
    t.diaper_changing_table_location,
    t.remodeling_year_month,
    t.reference_date,
    t.last_modified_at,
    sc.male_toilet_count,
    sc.male_urinal_count,
    sc.male_disabled_toilet_count,
    sc.male_disabled_urinal_count,
    sc.male_child_toilet_count,
    sc.male_child_urinal_count,
    sc.female_toilet_count,
    sc.female_disabled_toilet_count,
    sc.female_child_toilet_count
FROM toilets t
JOIN toilet_types tt ON tt.id = t.toilet_type_id
LEFT JOIN ownership_types ot ON ot.id = t.ownership_type_id
LEFT JOIN sewage_process_types spt ON spt.id = t.sewage_process_type_id
JOIN toilet_stall_counts sc ON sc.management_number = t.management_number
"""


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA_SQL)


def count_toilets() -> int:
    with get_connection() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM toilets").fetchone()
        return int(row["count"])


def _normalize_flag(value: bool | None) -> int:
    return 1 if value else 0


def _get_lookup_id(connection: sqlite3.Connection, table: str, value: str | None) -> int | None:
    if not value:
        return None
    connection.execute(f"INSERT OR IGNORE INTO {table} (name) VALUES (?)", (value,))
    row = connection.execute(f"SELECT id FROM {table} WHERE name = ?", (value,)).fetchone()
    return int(row["id"]) if row else None


def _ensure_municipality(connection: sqlite3.Connection, code: str) -> None:
    connection.execute(
        "INSERT OR IGNORE INTO municipalities (local_government_code) VALUES (?)",
        (code,),
    )


def _payload_to_database_record(
    connection: sqlite3.Connection,
    management_number: str,
    payload: ToiletCreate | ToiletUpdate,
    current: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, int]]:
    raw = payload.model_dump(exclude_unset=True)
    merged = dict(current or {})
    merged.update({key: value for key, value in raw.items() if value is not None})

    local_government_code = merged.get("local_government_code")
    toilet_type_name = merged.get("toilet_type_name")
    if not local_government_code or not toilet_type_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="local_government_code와 toilet_type_name은 필수입니다.",
        )

    _ensure_municipality(connection, local_government_code)
    record = {
        "management_number": management_number,
        "local_government_code": local_government_code,
        "toilet_type_id": _get_lookup_id(connection, "toilet_types", toilet_type_name),
        "ownership_type_id": _get_lookup_id(
            connection, "ownership_types", merged.get("ownership_type_name")
        ),
        "sewage_process_type_id": _get_lookup_id(
            connection, "sewage_process_types", merged.get("sewage_process_type_name")
        ),
        "legal_basis_name": merged.get("legal_basis_name"),
        "name": merged.get("name"),
        "road_address": merged.get("road_address"),
        "lot_address": merged.get("lot_address"),
        "management_agency": merged.get("management_agency"),
        "phone_number": merged.get("phone_number"),
        "opening_hours_type": merged.get("opening_hours_type"),
        "opening_hours_detail": merged.get("opening_hours_detail"),
        "installation_year_month": merged.get("installation_year_month"),
        "latitude": merged.get("latitude"),
        "longitude": merged.get("longitude"),
        "safety_target_flag": _normalize_flag(merged.get("safety_target_flag")),
        "emergency_bell_flag": _normalize_flag(merged.get("emergency_bell_flag")),
        "emergency_bell_location": merged.get("emergency_bell_location"),
        "entrance_cctv_flag": _normalize_flag(merged.get("entrance_cctv_flag")),
        "diaper_changing_table_flag": _normalize_flag(
            merged.get("diaper_changing_table_flag")
        ),
        "diaper_changing_table_location": merged.get("diaper_changing_table_location"),
        "remodeling_year_month": merged.get("remodeling_year_month"),
        "reference_date": merged.get("reference_date"),
        "last_modified_at": merged.get("last_modified_at"),
    }
    stall_counts = {field: int(merged.get(field, 0) or 0) for field in STALL_FIELDS}
    return record, stall_counts


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in [
        "safety_target_flag",
        "emergency_bell_flag",
        "entrance_cctv_flag",
        "diaper_changing_table_flag",
    ]:
        data[key] = bool(data[key])
    return data


def _fetch_one(connection: sqlite3.Connection, management_number: str) -> dict[str, Any] | None:
    row = connection.execute(
        f"{BASE_SELECT} WHERE t.management_number = ?",
        (management_number,),
    ).fetchone()
    return _row_to_dict(row) if row else None


def create_toilet(payload: ToiletCreate) -> dict[str, Any]:
    with get_connection() as connection:
        if _fetch_one(connection, payload.management_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 존재하는 management_number입니다.",
            )
        record, stall_counts = _payload_to_database_record(
            connection, payload.management_number, payload
        )
        connection.execute(
            """
            INSERT INTO toilets (
                management_number, local_government_code, toilet_type_id, ownership_type_id,
                sewage_process_type_id, legal_basis_name, name, road_address, lot_address,
                management_agency, phone_number, opening_hours_type, opening_hours_detail,
                installation_year_month, latitude, longitude, safety_target_flag,
                emergency_bell_flag, emergency_bell_location, entrance_cctv_flag,
                diaper_changing_table_flag, diaper_changing_table_location,
                remodeling_year_month, reference_date, last_modified_at
            ) VALUES (
                :management_number, :local_government_code, :toilet_type_id, :ownership_type_id,
                :sewage_process_type_id, :legal_basis_name, :name, :road_address, :lot_address,
                :management_agency, :phone_number, :opening_hours_type, :opening_hours_detail,
                :installation_year_month, :latitude, :longitude, :safety_target_flag,
                :emergency_bell_flag, :emergency_bell_location, :entrance_cctv_flag,
                :diaper_changing_table_flag, :diaper_changing_table_location,
                :remodeling_year_month, :reference_date, :last_modified_at
            )
            """,
            record,
        )
        connection.execute(
            """
            INSERT INTO toilet_stall_counts (
                management_number, male_toilet_count, male_urinal_count,
                male_disabled_toilet_count, male_disabled_urinal_count,
                male_child_toilet_count, male_child_urinal_count,
                female_toilet_count, female_disabled_toilet_count, female_child_toilet_count
            ) VALUES (
                :management_number, :male_toilet_count, :male_urinal_count,
                :male_disabled_toilet_count, :male_disabled_urinal_count,
                :male_child_toilet_count, :male_child_urinal_count,
                :female_toilet_count, :female_disabled_toilet_count, :female_child_toilet_count
            )
            """,
            {"management_number": payload.management_number, **stall_counts},
        )
        result = _fetch_one(connection, payload.management_number)
        return result if result else {}


def get_toilet(management_number: str) -> dict[str, Any]:
    with get_connection() as connection:
        result = _fetch_one(connection, management_number)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="데이터가 없습니다.")
        return result


def list_toilets(
    query: str | None = None,
    toilet_type_name: str | None = None,
    local_government_code: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any]:
    filters: list[str] = []
    params: list[Any] = []

    if query:
        filters.append("(t.name LIKE ? OR t.road_address LIKE ? OR t.lot_address LIKE ?)")
        like_query = f"%{query}%"
        params.extend([like_query, like_query, like_query])

    if toilet_type_name:
        filters.append("tt.name = ?")
        params.append(toilet_type_name)

    if local_government_code:
        filters.append("t.local_government_code = ?")
        params.append(local_government_code)

    where_clause = f" WHERE {' AND '.join(filters)}" if filters else ""

    with get_connection() as connection:
        total_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM toilets t JOIN toilet_types tt ON tt.id = t.toilet_type_id{where_clause}",
            params,
        ).fetchone()
        rows = connection.execute(
            f"{BASE_SELECT}{where_clause} ORDER BY t.name LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
        return {
            "total": int(total_row["count"]) if total_row else 0,
            "items": [_row_to_dict(row) for row in rows],
        }


def update_toilet(management_number: str, payload: ToiletUpdate) -> dict[str, Any]:
    with get_connection() as connection:
        current = _fetch_one(connection, management_number)
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="데이터가 없습니다.")

        record, stall_counts = _payload_to_database_record(
            connection, management_number, payload, current=current
        )
        connection.execute(
            """
            UPDATE toilets
            SET
                local_government_code = :local_government_code,
                toilet_type_id = :toilet_type_id,
                ownership_type_id = :ownership_type_id,
                sewage_process_type_id = :sewage_process_type_id,
                legal_basis_name = :legal_basis_name,
                name = :name,
                road_address = :road_address,
                lot_address = :lot_address,
                management_agency = :management_agency,
                phone_number = :phone_number,
                opening_hours_type = :opening_hours_type,
                opening_hours_detail = :opening_hours_detail,
                installation_year_month = :installation_year_month,
                latitude = :latitude,
                longitude = :longitude,
                safety_target_flag = :safety_target_flag,
                emergency_bell_flag = :emergency_bell_flag,
                emergency_bell_location = :emergency_bell_location,
                entrance_cctv_flag = :entrance_cctv_flag,
                diaper_changing_table_flag = :diaper_changing_table_flag,
                diaper_changing_table_location = :diaper_changing_table_location,
                remodeling_year_month = :remodeling_year_month,
                reference_date = :reference_date,
                last_modified_at = :last_modified_at,
                updated_at = CURRENT_TIMESTAMP
            WHERE management_number = :management_number
            """,
            record,
        )
        connection.execute(
            """
            UPDATE toilet_stall_counts
            SET
                male_toilet_count = :male_toilet_count,
                male_urinal_count = :male_urinal_count,
                male_disabled_toilet_count = :male_disabled_toilet_count,
                male_disabled_urinal_count = :male_disabled_urinal_count,
                male_child_toilet_count = :male_child_toilet_count,
                male_child_urinal_count = :male_child_urinal_count,
                female_toilet_count = :female_toilet_count,
                female_disabled_toilet_count = :female_disabled_toilet_count,
                female_child_toilet_count = :female_child_toilet_count
            WHERE management_number = :management_number
            """,
            {"management_number": management_number, **stall_counts},
        )
        result = _fetch_one(connection, management_number)
        return result if result else {}


def delete_toilet(management_number: str) -> None:
    with get_connection() as connection:
        deleted = connection.execute(
            "DELETE FROM toilets WHERE management_number = ?",
            (management_number,),
        )
        if deleted.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="데이터가 없습니다.")


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def list_map_markers(limit: int | None = None) -> list[dict[str, Any]]:
    sql = """
    SELECT
        t.management_number,
        t.name,
        tt.name AS toilet_type_name,
        t.latitude,
        t.longitude,
        t.road_address,
        t.lot_address,
        t.emergency_bell_flag,
        t.entrance_cctv_flag,
        t.diaper_changing_table_flag
    FROM toilets t
    JOIN toilet_types tt ON tt.id = t.toilet_type_id
    ORDER BY t.name
    """
    params: list[Any] = []
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)

    with get_connection() as connection:
        rows = connection.execute(sql, params).fetchall()

    markers = []
    for row in rows:
        item = dict(row)
        item["emergency_bell_flag"] = bool(item["emergency_bell_flag"])
        item["entrance_cctv_flag"] = bool(item["entrance_cctv_flag"])
        item["diaper_changing_table_flag"] = bool(item["diaper_changing_table_flag"])
        item["icon"] = "🚻"
        item["icon_size"] = 18
        markers.append(item)
    return markers


def list_nearby_toilets(latitude: float, longitude: float, limit: int = 100) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                t.management_number,
                t.name,
                tt.name AS toilet_type_name,
                t.latitude,
                t.longitude,
                t.road_address,
                t.lot_address,
                t.emergency_bell_flag,
                t.entrance_cctv_flag,
                t.diaper_changing_table_flag
            FROM toilets t
            JOIN toilet_types tt ON tt.id = t.toilet_type_id
            WHERE t.latitude BETWEEN ? AND ?
              AND t.longitude BETWEEN ? AND ?
            """,
            (latitude - 0.7, latitude + 0.7, longitude - 0.7, longitude + 0.7),
        ).fetchall()

    candidates: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["distance_meters"] = round(
            _haversine_distance(latitude, longitude, item["latitude"], item["longitude"]),
            2,
        )
        item["emergency_bell_flag"] = bool(item["emergency_bell_flag"])
        item["entrance_cctv_flag"] = bool(item["entrance_cctv_flag"])
        item["diaper_changing_table_flag"] = bool(item["diaper_changing_table_flag"])
        candidates.append(item)

    candidates.sort(key=lambda item: item["distance_meters"])
    result = []
    for rank, item in enumerate(candidates[:limit], start=1):
        item["icon"] = "🚻"
        item["icon_size"] = max(18, 46 - rank // 3)
        result.append(item)
    return result
