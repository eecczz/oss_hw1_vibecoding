from pathlib import Path

import pandas as pd

from app.db.database import get_connection
from app.repositories.toilets import count_toilets, initialize_database
from app.settings import settings


CSV_RENAME_MAP = {
    "개방자치단체코드": "local_government_code",
    "관리번호": "management_number",
    "구분명": "toilet_type_name",
    "근거법령명": "legal_basis_name",
    "화장실명": "name",
    "소재지도로명주소": "road_address",
    "소재지지번주소": "lot_address",
    "남성용-대변기수": "male_toilet_count",
    "남성용-소변기수": "male_urinal_count",
    "남성용-장애인용대변기수": "male_disabled_toilet_count",
    "남성용-장애인용소변기수": "male_disabled_urinal_count",
    "남성용-어린이용대변기수": "male_child_toilet_count",
    "남성용-어린이용소변기수": "male_child_urinal_count",
    "여성용-대변기수": "female_toilet_count",
    "여성용-장애인용대변기수": "female_disabled_toilet_count",
    "여성용-어린이용대변기수": "female_child_toilet_count",
    "관리기관명": "management_agency",
    "전화번호": "phone_number",
    "개방시간": "opening_hours_type",
    "개방시간상세": "opening_hours_detail",
    "설치연월": "installation_year_month",
    "WGS84위도": "latitude",
    "WGS84경도": "longitude",
    "화장실소유구분명": "ownership_type_name",
    "오물처리방식": "sewage_process_type_name",
    "안전관리시설설치대상여부": "safety_target_flag",
    "비상벨설치여부": "emergency_bell_flag",
    "비상벨설치장소": "emergency_bell_location",
    "화장실입구CCTV설치유무": "entrance_cctv_flag",
    "기저귀교환대유무": "diaper_changing_table_flag",
    "기저귀교환대장소": "diaper_changing_table_location",
    "리모델링연월": "remodeling_year_month",
    "데이터기준일자": "reference_date",
    "최종수정시점": "last_modified_at",
}


TEXT_COLUMNS = [
    "local_government_code",
    "management_number",
    "toilet_type_name",
    "legal_basis_name",
    "name",
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
]

COUNT_COLUMNS = [
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

FLAG_COLUMNS = [
    "safety_target_flag",
    "emergency_bell_flag",
    "entrance_cctv_flag",
    "diaper_changing_table_flag",
]


def _normalize_year_month(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    digits = "".join(character for character in text if character.isdigit())
    if len(digits) != 6:
        return None
    year = int(digits[:4])
    month = int(digits[4:])
    if year < 1900 or month < 1 or month > 12:
        return None
    return digits


def _read_csv(csv_path: Path) -> pd.DataFrame:
    dataframe = pd.read_csv(csv_path, encoding="cp949")
    dataframe = dataframe.rename(columns=CSV_RENAME_MAP)
    dataframe = dataframe.where(pd.notnull(dataframe), None)

    for column in TEXT_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].apply(
                lambda value: str(value).strip() if value is not None else None
            )
            dataframe[column] = dataframe[column].replace({"": None, "nan": None})

    for column in ["installation_year_month", "remodeling_year_month"]:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].apply(_normalize_year_month)

    dataframe["local_government_code"] = dataframe["local_government_code"].astype(str)
    dataframe["management_number"] = dataframe["management_number"].astype(str)
    dataframe["latitude"] = pd.to_numeric(dataframe["latitude"], errors="coerce")
    dataframe["longitude"] = pd.to_numeric(dataframe["longitude"], errors="coerce")

    for column in COUNT_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce").fillna(0).astype(int)

    for column in FLAG_COLUMNS:
        dataframe[column] = dataframe[column].map({"Y": 1, "N": 0}).fillna(0).astype(int)

    dataframe = dataframe[
        dataframe["local_government_code"].notna()
        & dataframe["toilet_type_name"].notna()
        & dataframe["management_number"].notna()
        & dataframe["name"].notna()
        & dataframe["latitude"].notna()
        & dataframe["longitude"].notna()
        & dataframe["latitude"].between(33.0, 39.5)
        & dataframe["longitude"].between(124.0, 132.5)
        & (dataframe["road_address"].notna() | dataframe["lot_address"].notna())
    ].copy()
    dataframe = dataframe.drop_duplicates(subset=["management_number"], keep="last")
    return dataframe


def import_csv_to_database(csv_path: Path | None = None, replace_existing: bool = False) -> int:
    initialize_database()
    path = csv_path or settings.csv_path
    dataframe = _read_csv(path)

    municipalities = sorted(
        {
            (row.local_government_code,)
            for row in dataframe.itertuples(index=False)
            if row.local_government_code
        }
    )
    toilet_types = sorted(
        {
            (row.toilet_type_name,)
            for row in dataframe.itertuples(index=False)
            if row.toilet_type_name
        }
    )
    ownership_types = sorted(
        {
            (row.ownership_type_name,)
            for row in dataframe.itertuples(index=False)
            if row.ownership_type_name
        }
    )
    sewage_process_types = sorted(
        {
            (row.sewage_process_type_name,)
            for row in dataframe.itertuples(index=False)
            if row.sewage_process_type_name
        }
    )

    with get_connection() as connection:
        if replace_existing:
            connection.execute("DELETE FROM toilet_stall_counts")
            connection.execute("DELETE FROM toilets")
            connection.execute("DELETE FROM municipalities")
            connection.execute("DELETE FROM toilet_types")
            connection.execute("DELETE FROM ownership_types")
            connection.execute("DELETE FROM sewage_process_types")

        connection.executemany(
            "INSERT OR IGNORE INTO municipalities (local_government_code) VALUES (?)",
            municipalities,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO toilet_types (name) VALUES (?)",
            toilet_types,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO ownership_types (name) VALUES (?)",
            ownership_types,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO sewage_process_types (name) VALUES (?)",
            sewage_process_types,
        )

        toilet_type_ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM toilet_types").fetchall()
        }
        ownership_type_ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM ownership_types").fetchall()
        }
        sewage_process_type_ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM sewage_process_types").fetchall()
        }

        toilets_payload = []
        stall_payload = []

        for row in dataframe.to_dict(orient="records"):
            toilets_payload.append(
                {
                    "management_number": row["management_number"],
                    "local_government_code": row["local_government_code"],
                    "toilet_type_id": toilet_type_ids[row["toilet_type_name"]],
                    "ownership_type_id": ownership_type_ids.get(row["ownership_type_name"]),
                    "sewage_process_type_id": sewage_process_type_ids.get(
                        row["sewage_process_type_name"]
                    ),
                    "legal_basis_name": row["legal_basis_name"],
                    "name": row["name"],
                    "road_address": row["road_address"],
                    "lot_address": row["lot_address"],
                    "management_agency": row["management_agency"],
                    "phone_number": row["phone_number"],
                    "opening_hours_type": row["opening_hours_type"],
                    "opening_hours_detail": row["opening_hours_detail"],
                    "installation_year_month": row["installation_year_month"],
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "safety_target_flag": int(row["safety_target_flag"]),
                    "emergency_bell_flag": int(row["emergency_bell_flag"]),
                    "emergency_bell_location": row["emergency_bell_location"],
                    "entrance_cctv_flag": int(row["entrance_cctv_flag"]),
                    "diaper_changing_table_flag": int(row["diaper_changing_table_flag"]),
                    "diaper_changing_table_location": row["diaper_changing_table_location"],
                    "remodeling_year_month": row["remodeling_year_month"],
                    "reference_date": row["reference_date"],
                    "last_modified_at": row["last_modified_at"],
                }
            )
            stall_payload.append(
                {
                    "management_number": row["management_number"],
                    "male_toilet_count": int(row["male_toilet_count"]),
                    "male_urinal_count": int(row["male_urinal_count"]),
                    "male_disabled_toilet_count": int(row["male_disabled_toilet_count"]),
                    "male_disabled_urinal_count": int(row["male_disabled_urinal_count"]),
                    "male_child_toilet_count": int(row["male_child_toilet_count"]),
                    "male_child_urinal_count": int(row["male_child_urinal_count"]),
                    "female_toilet_count": int(row["female_toilet_count"]),
                    "female_disabled_toilet_count": int(row["female_disabled_toilet_count"]),
                    "female_child_toilet_count": int(row["female_child_toilet_count"]),
                }
            )

        connection.executemany(
            """
            INSERT OR REPLACE INTO toilets (
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
            toilets_payload,
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO toilet_stall_counts (
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
            stall_payload,
        )
    return len(dataframe)


def seed_database_if_empty() -> int:
    if count_toilets() > 0:
        return 0
    if not settings.csv_path.exists():
        return 0
    return import_csv_to_database(settings.csv_path, replace_existing=False)
