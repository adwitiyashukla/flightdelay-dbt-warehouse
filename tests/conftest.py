import textwrap
from pathlib import Path

import pytest

FLIGHTS_CSV = textwrap.dedent(
    """\
    rownames,year,month,day,dep_time,sched_dep_time,dep_delay,arr_time,sched_arr_time,arr_delay,carrier,flight,tailnum,origin,dest,air_time,distance,hour,minute,time_hour
    1,2013,1,1,517,515,2,830,819,11,UA,1545,N14228,EWR,IAH,227,1400,5,15,2013-01-01T10:00:00Z
    2,2013,1,2,533,529,4,850,830,20,UA,1714,N24211,LGA,IAH,227,1416,5,29,2013-01-02T10:00:00Z
    3,2013,2,1,,600,,,,,AA,1141,N619AA,JFK,MIA,,1089,6,0,2013-02-01T11:00:00Z
    """
)

WEATHER_CSV = textwrap.dedent(
    """\
    rownames,origin,year,month,day,hour,temp,dewp,humid,wind_dir,wind_speed,wind_gust,precip,pressure,visib,time_hour
    1,EWR,2013,1,1,5,39.02,26.06,59.37,270,10.35702,,0,1012,10,2013-01-01T10:00:00Z
    2,LGA,2013,1,2,5,39.92,24.98,54.81,250,15.89,,0.02,1011,8,2013-01-02T10:00:00Z
    3,JFK,2013,2,1,6,41.0,26.96,57.33,260,1048.36058,,0,1010,10,2013-02-01T11:00:00Z
    """
)

PLANES_CSV = textwrap.dedent(
    """\
    rownames,tailnum,year,type,manufacturer,model,engines,seats,speed,engine
    1,N14228,1999,Fixed wing multi engine,BOEING,737-824,2,149,,Turbo-fan
    2,N24211,1998,Fixed wing multi engine,BOEING,737-824,2,149,,Turbo-fan
    """
)

AIRLINES_CSV = textwrap.dedent(
    """\
    rownames,carrier,name
    1,UA,United Air Lines Inc.
    2,AA,American Airlines Inc.
    """
)

AIRPORTS_CSV = textwrap.dedent(
    """\
    rownames,faa,name,lat,lon,alt,tz,dst,tzone
    1,EWR,Newark Liberty Intl,40.6925,-74.168667,18,-5,A,America/New_York
    2,LGA,La Guardia,40.777245,-73.872608,22,-5,A,America/New_York
    3,JFK,John F Kennedy Intl,40.639751,-73.778925,13,-5,A,America/New_York
    4,IAH,George Bush Intercontinental,29.984433,-95.341442,97,-6,A,America/Chicago
    """
)

OURAIRPORTS_CSV = textwrap.dedent(
    """\
    id,ident,type,name,latitude_deg,longitude_deg,elevation_ft,continent,iso_country,iso_region,municipality,scheduled_service,icao_code,iata_code,gps_code,local_code,home_link,wikipedia_link,keywords
    3661,KEWR,large_airport,Newark Liberty International Airport,40.6925,-74.168667,18,NA,US,US-NJ,Newark,yes,KEWR,EWR,KEWR,EWR,,,
    3697,KLGA,large_airport,La Guardia Airport,40.777245,-73.872608,20,NA,US,US-NY,New York,yes,KLGA,LGA,KLGA,LGA,,,
    3687,KJFK,large_airport,John F Kennedy International Airport,40.639447,-73.779317,13,NA,US,US-NY,New York,yes,KJFK,JFK,KJFK,JFK,,,
    3550,KIAH,large_airport,George Bush Intercontinental Airport,29.984433,-95.341442,97,NA,US,US-TX,Houston,yes,KIAH,IAH,KIAH,IAH,,,
    6019,TJMZ,medium_airport,Eugenio Maria de Hostos Airport,18.255699,-67.148499,28,NA,PR,PR-U-A,Mayaguez,yes,TJMZ,MAZ,TJMZ,MAZ,,,
    """
)

OPENFLIGHTS_DAT = textwrap.dedent(
    """\
    5209,"United Air Lines Inc.",\\N,"UA","UAL","UNITED","United States","Y"
    24,"American Airlines Inc.",\\N,"AA","AAL","AMERICAN","United States","Y"
    137,"Dormant Air",\\N,"UA","OLD","OLD","United States","N"
    """
)

RESPONSES = {
    "flights.csv": FLIGHTS_CSV,
    "weather.csv": WEATHER_CSV,
    "planes.csv": PLANES_CSV,
    "airlines.csv": AIRLINES_CSV,
    "airports.csv": AIRPORTS_CSV,
    "ourairports_airports.csv": OURAIRPORTS_CSV,
    "openflights_airlines.dat": OPENFLIGHTS_DAT,
}

CONFIG_TEMPLATE = """
[warehouse]
path = "data/flightdelay.duckdb"

[ingest]
raw_dir = "data/raw"
months = ["2013-01", "2013-02"]

[http]
timeout_s = 5.0
retries = 2
backoff_s = 0.0

[[sources]]
name = "flights"
url = "https://example.test/flights.csv"
file = "flights.csv"
monthly = true

[[sources]]
name = "weather"
url = "https://example.test/weather.csv"
file = "weather.csv"
monthly = true

[[sources]]
name = "planes"
url = "https://example.test/planes.csv"
file = "planes.csv"

[[sources]]
name = "airlines"
url = "https://example.test/airlines.csv"
file = "airlines.csv"

[[sources]]
name = "airports"
url = "https://example.test/airports.csv"
file = "airports.csv"

[[sources]]
name = "ourairports_airports"
url = "https://example.test/ourairports_airports.csv"
file = "ourairports_airports.csv"

[[sources]]
name = "openflights_airlines"
url = "https://example.test/openflights_airlines.dat"
file = "openflights_airlines.dat"
header = false
columns = ["airline_id", "name", "alias", "iata", "icao", "callsign", "country", "active"]
"""


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(CONFIG_TEMPLATE)
    return path


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "data" / "raw"
    directory.mkdir(parents=True)
    for name, body in RESPONSES.items():
        (directory / name).write_text(body)
    return directory
