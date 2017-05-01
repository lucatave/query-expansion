from typing import Dict, Tuple, Set
from cmath import log, phase
from functools import lru_cache
from data import (get_annotation_neighbours,
                  get_users_from_term, get_terms,
                  get_term_count, dict_k_add_item,
                  query_from_dict_to_str, tf_iuf,
                  normalize_data, joined_dict_transpose,
                  dict_mat_x_dict, get_user_count)


def query_expansion(query: str, k: int = 4) -> str:
    query_set = normalize_data(query)
    na = int(get_term_count())
    nu = int(get_user_count())
    print("query_set", query_set)
    query_score: Dict[str, Set[str]] = {}
    candidates: Dict[str, float] = {}
    for t in query_set:
        print(t)
        neighbours = get_annotation_neighbours(t)
        for neighbour in neighbours:
            if neighbour not in candidates:
                candidates = dict_k_add_item(candidates, k,
                                             neighbour, rank(na, nu,
                                                             t, neighbour))
        print(candidates.keys())
        query_score[t] = set(candidates.keys())
        candidates.clear()
    return query_score


def simstep(term1: str, term2: str,
            accUser: Set[str], unaccUser: Set[str],
            mat: Dict[Tuple[str, str], int], stepValue: float) -> float:
    for (u, r) in accUser:
        if u not in unaccUser:
            stepValue = stepValue / phase(min(mat[term1, u],
                                              mat[term2, u] *
                                              phase(-log(r))))
    return stepValue


@lru_cache(maxsize=None)
def rank(na: int, nu: int, query_term: str, term: str, y=0.5) -> float:
    semantic_part = y * sim(query_term, term)
    social_part = 0.0
    for t in get_terms():
        social_part += sim(t.id, term) * tf_iuf(na, nu, t)
    social_part = social_part * (1 - y) / na
    return semantic_part + social_part


@lru_cache(maxsize=None)
def sim(term1: str, term2: str) -> float:
    uterm1 = get_users_from_term(term1)
    u1 = set()
    uterm2 = get_users_from_term(term2)
    u2 = set()

    matannotationuser: Dict[Tuple[str, str], int] = {}
    for (u, r, c) in uterm1:
        matannotationuser[term1, u] = c
        u1.add((u, r))
    for (u, r, c) in uterm2:
        matannotationuser[term2, u] = c
        u2.add((u, r))
    for (u, r) in u1:
        if (u, r) not in u2:
            matannotationuser[term2, u] = 0
    for (u, r) in u2:
        if (u, r) not in u1:
            matannotationuser[term1, u] = 0

    simrank = simstep(term1, term2, u1, u2, matannotationuser, 1.0)
    simrank = simstep(term1, term2, u2, u1, matannotationuser, simrank)
    return simrank


def step_spr_trasposed(mat: Dict[str, Dict[str, int]],
                       v: Dict[str, float],
                       matxv: Dict[str, float]) -> Dict[str, float]:
    return dict_mat_x_dict(joined_dict_transpose(mat), v, matxv)


def step_spr_regular(mat: Dict[str, Dict[str, int]],
                     v: Dict[str, float]) -> Dict[str, float]:
    return dict_mat_x_dict(mat, v)


def socialpagerank(matpageuser: Dict[str, Dict[str, int]],
                   matannotationpage: Dict[str, Dict[str, int]],
                   matuserannotation: Dict[str, Dict[str, int]],
                   matp: Dict[str, float],
                   maxIt=100) \
                   -> Tuple[Dict[str, float],
                            Dict[str, float],
                            Dict[str, float]]:
    matu: Dict[str, float] = {}
    mata: Dict[str, float] = {}

    for i in range(1, maxIt):
        matu = step_spr_trasposed(matpageuser, matp, matu)
        mata = step_spr_trasposed(matuserannotation, matu, mata)
        matpt = step_spr_trasposed(matannotationpage, mata, {})
        matat = step_spr_regular(matannotationpage, matpt)
        matut = step_spr_regular(matuserannotation, matat)
        matp = step_spr_regular(matpageuser, matut)

    return (matp, matu, mata)
