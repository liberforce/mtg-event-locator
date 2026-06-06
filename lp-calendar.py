#!/usr/bin/env python
import pprint
import enum
import json

import dotenv
import requests


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
    raw_events = (line[line.index("["):].strip(";") for line in lines if "const events = [" in line)
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


def main():
    config = load_config()
    raw_data = get_lp_calendar_raw_data(config)
    events = import_json_calendar(raw_data)
    league = get_league(config)
    events = filter_league_events(events, league)
    pprint.pprint(events)


if __name__ == "__main__":
    main()
