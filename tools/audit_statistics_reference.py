#!/usr/bin/env python3
"""Reference analytical calculations for independent Sätila method regression.

This module deliberately does not modify the production JS or the published
bundles. It provides a small, readable statistical oracle for the Codex app.
All source observations must already have been validated and all distances
here are public TIMING-axis distances, never GPX-display coordinates.
"""
from __future__ import annotations
import math
import statistics

def empirical_quantile(values, q, minimum_n=5):
    """Linear interpolation, sorted observations, q in [0,1]; no synthetic rows."""
    xs=sorted(x for x in values if isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x))
    if len(xs)<minimum_n or not 0<=q<=1:
        return None
    index=(len(xs)-1)*q
    lo=int(index);hi=min(len(xs)-1,lo+1)
    return xs[lo]+(xs[hi]-xs[lo])*(index-lo)

def readiness(values):
    xs=[x for x in values if isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) and x>0]
    return {
        "n":len(xs),
        "median":empirical_quantile(xs,.5,minimum_n=5),
        "q25":empirical_quantile(xs,.25,minimum_n=10),
        "q75":empirical_quantile(xs,.75,minimum_n=10),
        "q10":empirical_quantile(xs,.10,minimum_n=20),
        "q90":empirical_quantile(xs,.90,minimum_n=20),
    }

def source_anchored_segment(start_time,finish_time):
    """Return None unless two REAL public times form a positive pair.

    Only the genuine race start is allowed to have an explicitly supplied zero.
    Missing intermediate station times must never be replaced by zero.
    """
    if any(type(t) not in (float,int) or not math.isfinite(t) for t in (start_time,finish_time)):
        return None
    diff=finish_time-start_time
    return diff if start_time>=0 and finish_time>0 and diff>0 else None

def observed_goal_fraction(segment_seconds,runner_finish_seconds):
    """A positive measured segment as a fraction of this runner's real finish."""
    if any(type(t) not in (float,int) or not math.isfinite(t) or t<=0 for t in (segment_seconds,runner_finish_seconds)):
        return None
    if segment_seconds>runner_finish_seconds:
        return None
    return segment_seconds/runner_finish_seconds

def goal_plan_exact(target_seconds, measured_fractions, timing_kms, n_min=5):
    """Separate observed relative pacing and declared distance fallback.

    measured_fractions is a list (one list for each *effective* segment) of
    per-finisher s_i / F, not an array of invented checkpoint observations.
    Return integer seconds that sum exactly to the target. Largest-remainder
    rounding prevents silent cumulative rounding drift.
    """
    if type(target_seconds) is not int or target_seconds<=0:
        raise ValueError("Positive integral finish goal required")
    if len(measured_fractions)!=len(timing_kms) or not timing_kms:
        raise ValueError("One positive timing-axis distance for each segment")
    weights=[];methods=[];sample_sizes=[]
    total_km=sum(timing_kms)
    if any(type(d) not in (float,int) or not math.isfinite(d) or d<=0 for d in timing_kms):
        raise ValueError("Every effective segment distance must be positive")
    for fractions,distance in zip(measured_fractions,timing_kms):
        good=[x for x in fractions if type(x) in (int,float) and math.isfinite(x) and 0<x<=1]
        n=len(good)
        sample_sizes.append(n)
        if n>=n_min:
            weights.append(statistics.median(good))
            methods.append("observed_relative_median")
        else:
            weights.append(distance/total_km)
            methods.append("distance_only_planning_fallback")
    weight_sum=sum(weights)
    if weight_sum<=0 or not math.isfinite(weight_sum):
        raise ValueError("Cannot allocate a nonpositive pacing weight")
    floats=[target_seconds*w/weight_sum for w in weights]
    times=[math.floor(x) for x in floats]
    remaining=target_seconds-sum(times)
    order=sorted(range(len(times)),key=lambda i:(-(floats[i]-times[i]),i))
    for idx in order[:remaining]:
        times[idx]+=1
    assert all(t>=0 for t in times)
    assert sum(times)==target_seconds
    cumulative=[];sofar=0
    for t in times:
        sofar+=t;cumulative.append(sofar)
    return [{"segment_seconds":times[i],
             "cumulative_seconds":cumulative[i],
             "source_n":sample_sizes[i],
             "method":methods[i],
             "timing_km":timing_kms[i]} for i in range(len(times))]

def observed_podium(observations,minimum_size=1,max_results=3):
    """Sorted real segment observations, no synthetic third result."""
    good=[o for o in observations if type(o.get("seconds")) in (int,float) and o["seconds"]>0 and math.isfinite(o["seconds"])]
    good.sort(key=lambda o:(o["seconds"],str(o.get("id",""))))
    # Collapsing duplicate result identifiers avoids two medals for the same athlete.
    seen=set();distinct=[]
    for o in good:
        identity=o.get("id")
        if identity is None or identity in seen:continue
        seen.add(identity);distinct.append(o)
    return distinct[:max_results] if len(distinct)>=minimum_size else []

def observed_rank_progression(checkpoints):
    """No placement is assigned at a race's starting line."""
    p=[(c["name"],c["place"]) for c in checkpoints if type(c.get("place")) is int and c["place"]>0]
    if len(p)<2:return None
    return {"first_observed":p[0],"last_observed":p[-1],
            "net_places_gained":p[0][1]-p[-1][1],
            "observation_count":len(p)}
