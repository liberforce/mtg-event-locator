#!/usr/bin/env python

import datetime
import enum
import json
import pathlib
import pprint

import dotenv
import icalendar
import requests


class Stores(enum.Enum):
    GOUPIYA = "Goupiya"
    LETROLLA2TETES = "Le Troll à 2 Têtes"
    PARKAGE = "Parkage (Épée de Bois)"
    QUEIMADA = "Queimada"


class Leagues(enum.Enum):
    LPAlpesMaritimes = 29
    LPBesak = 21
    LPBordeaux = 15
    LPCalais = 13
    LPCantal = 6
    LPCarcassonne = 30
    LPChambéry = 10
    LPClermont = 8
    LPLimogesPoitiers = 23
    LPLorient = 17
    LPLyon = 1
    LPMontaigu = 25
    LPMontpellier = 9
    LPNord = 19
    LPParis = 12
    LPRennes = 26
    LPRoanne = 11
    LPRouen = 7
    LPStrasbourg = 14
    LPToulon = 18
    LPToulouse = 24
    LPTours = 27
    LPVirtuelle = 20
    LPVitrolles = 22
    xHorsLigue = 16


def load_config():
    return dotenv.dotenv_values("lp.env")


def get_lp_calendar_raw_data(config) -> str:
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


def import_json_calendar(raw_events):
    events = json.loads(raw_events)
    return events


def get_league(config):
    return getattr(Leagues, config["LEAGUE_NAME"])


def filter_league_events(events, league: Leagues):
    filtered_events = []

    for event in events:
        if int(event["ligue_id"]) == league.value:
            filtered_events.append(event)

    return filtered_events


def infer_organizer(lp_event):
    desc = lp_event["rawDescription"].lower()
    title = lp_event["title"].lower()

    for store in Stores:
        for field in [desc, title]:
            if store.name.lower() in field:
                return store

    return None


def to_ical_event(event):
    # FIXME: extract URL from description?
    organizer = infer_organizer(event)
    ical_event = icalendar.Event.new(
        summary=event["title"],
        start=datetime.date.fromisoformat(event["start"]),
        color=event["color"],
        description=event["rawDescription"],
        organizer=organizer.value if organizer else None,
        # url=event["url"],
    )

    return ical_event


def create_ical(events):
    calendar = icalendar.Calendar.new()

    for event in events:
        ical_event = to_ical_event(event)
        calendar.add_component(ical_event)

    return calendar.to_ical()

def main():
    config = load_config()
    raw_data = get_lp_calendar_raw_data(config)
    lp_events = import_json_calendar(raw_data)
    league = get_league(config)
    my_league_events = filter_league_events(lp_events, league)
    ical_calendar = create_ical(my_league_events)
    #pprint.pprint(my_league_events)

    path = pathlib.Path("LiguePauper.ics")
    with path.open("wb") as f:
        f.write(ical_calendar)


if __name__ == "__main__":
    main()
