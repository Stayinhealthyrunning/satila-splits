#!/usr/bin/env python3
"""Reference contract: illustrative route replay from REAL public timing anchors.

Distance in a public GPX display is NOT the public timing distance. Mapping
nominal km onto display km is an explicit visual convention, available only
for an edition with the authorized official route. No runner GPS track exists.
Missing public checkpoints are ignored, never assigned invented TIME values.
"""
from __future__ import annotations
import math

def is_number(x):
    return type(x) in (float,int) and math.isfinite(x)

def build_anchors(race,route,runner):
    if not route or not race.get("route_file"):
        return []
    if runner["status"]!="FINISHED":
        return []
    if route["family"]!=race["family"] or race["year"] not in route["edition_references"]:
        return []
    route_max=route["points"][-1][0]
    nominal=race["nominal_km"]
    if not is_number(nominal) or nominal<=0 or not is_number(route_max) or route_max<=0:
        return []
    observations={s["station_uid"]:s for s in race["splits"] if s["result_id"]==runner["id"]}
    anchors=[{"display_km":0.0,"timing_km":0.0,"seconds":0.0,"name":"Race start",
              "kind":"start_origin","station_uid":None}]
    for st in sorted(race["stations"],key=lambda s:(s.get("km") or 0,s["sort"],s["uid"])):
        if not st["is_analysis_boundary"] or not is_number(st.get("km")) or st["km"]<=0:
            continue
        observed=observations.get(st["uid"])
        if not observed or not is_number(observed.get("elapsed_seconds")):
            continue
        seconds=observed["elapsed_seconds"]
        display=min(route_max,st["km"]/nominal*route_max)
        last=anchors[-1]
        if seconds>last["seconds"] and display>last["display_km"]+1e-8:
            anchors.append({"display_km":display,"timing_km":st["km"],
                            "seconds":seconds,"name":st["name"],
                            "kind":"source_observation","station_uid":st["uid"]})
    return anchors

def time_at_display_km(anchors,km):
    """Return (estimated_time, provenance_label) only inside observed anchors.

    Intermediate value is always an *illustrative time estimate*; it must
    never be treated as a real checkpoint measurement.
    """
    if not anchors or not is_number(km) or km<0:return None
    if km>anchors[-1]["display_km"]+1e-8:return None
    for anchor in anchors:
        if abs(km-anchor["display_km"])<=1e-8:
            return anchor["seconds"],anchor["kind"]
    for a,b in zip(anchors,anchors[1:]):
        if a["display_km"]<km<b["display_km"]:
            frac=(km-a["display_km"])/(b["display_km"]-a["display_km"])
            return a["seconds"]+(b["seconds"]-a["seconds"])*frac,"illustrative_between_observed_anchors"
    return None

def duel_time_gap(first_anchors,second_anchors,display_km):
    """Positive = first is later at that same illustrative display position."""
    a=time_at_display_km(first_anchors,display_km)
    b=time_at_display_km(second_anchors,display_km)
    if a is None or b is None:return None
    return a[0]-b[0]

def position_at_display_km(route_points,km):
    """Interpolation on SANITIZED track, no wall clock, no athlete identity."""
    if len(route_points)<2 or not is_number(km):return None
    low,high=route_points[0][0],route_points[-1][0]
    if km<low or km>high:return None
    for first,last in zip(route_points,route_points[1:]):
        if first[0]<=km<=last[0]:
            f=(km-first[0])/(last[0]-first[0])
            lat=first[1]+(last[1]-first[1])*f
            lon=first[2]+(last[2]-first[2])*f
            ele=(first[3]+(last[3]-first[3])*f
                 if is_number(first[3]) and is_number(last[3]) else None)
            return [km,lat,lon,ele]
    return None
