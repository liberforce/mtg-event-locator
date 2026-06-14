#!/usr/bin/env python

import datetime
import enum
import json
import pathlib
import re
import uuid

import dotenv
import icalendar
import requests


class LocalGameStore(enum.Enum):
    GOUPIYA = "Goupiya"
    LETROLLA2TETES = "Le Troll à 2 Têtes"
    PARKAGE = "Parkage (Épée de Bois)"
    QUEIMADA = "Queimada"


class League(enum.Enum):
    LPLyon = 1
    LPCantal = 6
    LPRouen = 7
    LPClermont = 8
    LPMontpellier = 9
    LPChambéry = 10
    LPRoanne = 11
    LPParis = 12
    LPCalais = 13
    LPStrasbourg = 14
    LPBordeaux = 15
    xHorsLigue = 16
    LPLorient = 17
    LPToulon = 18
    LPNord = 19
    LPVirtuelle = 20
    LPBesak = 21
    LPVitrolles = 22
    LPLimogesPoitiers = 23
    LPToulouse = 24
    LPMontaigu = 25
    LPRennes = 26
    LPTours = 27
    LPAlpesMaritimes = 29
    LPCarcassonne = 30


def load_config() -> dict[tuple[str, str]]:
    return dotenv.dotenv_values("lp.env")


def get_lp_calendar_raw_data(config: dict[tuple[str, str]]) -> str:
    response = requests.get(
        "https://www.pauper-france.fr/calendrier.php?date=2026-06-01",
    )
    lines = response.text.splitlines()
    raw_events = (
        line[line.index("[") :].strip(";")
        for line in lines
        if "const events = [" in line
    )
    return next(raw_events)


def import_json_calendar(raw_events: str) -> dict:
    events = json.loads(raw_events)
    return events


def get_league(config: dict[tuple[str, str]]) -> League:
    return getattr(League, config["LEAGUE_NAME"])


def filter_league_events(events, league: League) -> dict:
    filtered_events = []

    for event in events:
        if int(event["ligue_id"]) == league.value:
            filtered_events.append(event)

    return filtered_events


def infer_store(lp_event: dict) -> LocalGameStore | None:
    desc = lp_event["rawDescription"].lower()
    title = lp_event["title"].lower()

    for store in LocalGameStore:
        for field in [desc, title]:
            if store.name.lower() in field:
                return store

    return None


def infer_url(lp_event: dict) -> str | None:
    desc = lp_event["rawDescription"]
    urls = re.findall(r'http[s]://[^ "<]*', desc, flags=re.MULTILINE)

    if urls:
        # Trust the longest URL is several provided.
        # Longer URLs may lead to event-specific pages.
        length, url = sorted({len(url): url for url in urls}.items())[-1]
        return url

    return None


def to_ical_event(event: dict, league: League) -> icalendar.Event:
    lgs = infer_store(event)
    ical_event = icalendar.Event.new(
        uid=uuid.UUID(int=int(event["id"])),
        summary=event["title"],
        start=datetime.date.fromisoformat(event["start"]),
        color=event["color"],
        description=event["rawDescription"],
        organizer=league.name if league is not None else None,
        categories=(event["categorie"]),
        location=lgs.value if lgs else None,
        url=infer_url(event),
    )

    return ical_event


def create_ical(events: dict, league=None) -> icalendar.Calendar:
    calendar = icalendar.Calendar.new()

    for event in events:
        ical_event = to_ical_event(event, league)
        calendar.add_component(ical_event)

    return calendar.to_ical()


def save_calendar(ical_calendar: icalendar.Calendar) -> None:
    path = pathlib.Path("LiguePauper.ics")
    with path.open("wb") as f:
        f.write(ical_calendar)


def main() -> None:
    config = load_config()
    raw_data = get_lp_calendar_raw_data(config)
    lp_events = import_json_calendar(raw_data)
    league = get_league(config)
    my_league_events = filter_league_events(lp_events, league)
    ical_calendar = create_ical(my_league_events, league)
    save_calendar(ical_calendar)

    # import pprint
    # pprint.pprint(my_league_events)


if __name__ == "__main__":
    main()
