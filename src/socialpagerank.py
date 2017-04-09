from typing import Dict, Tuple, List
from cmath import log, phase
from data import (get_user_rank, get_neighbours)


def query_expansion(query: List[str], aa: Dict[Tuple[str, str], float]):
    query_score = {}
    for t in query:
        neighbours = get_neighbours(t)
        for neighbour in neighbours:
            query_score[neighbour] = rank(aa, neighbour)


def simstep(accUser: str, unaccUser: str,
            mat: Dict[Tuple[str, str], int], stepValue: float) -> float:
    for u in accUser:
        if u not in unaccUser:
            stepValue = stepValue / phase(min(mat[accUser, u],
                                              mat[unaccUser, u] *
                                              (-log(get_user_rank(u)))))
    return stepValue


def rank(aa: Dict[Tuple[str, str], float], term: str, y=0.5) -> float:
    return 0.5


def sim(term1: str, term2: str,
        uterm1: str, uterm2: str,
        termusermat: Dict[Tuple[str, str], int]) -> float:

    simrank = simstep(uterm1, uterm2, termusermat, 1.0)
    simrank = simstep(uterm2, uterm1, termusermat, simrank)
    return simrank


def step_spr_trasposed(mat: Dict[str, Dict[str, int]],
                       v: Dict[str, float],
                       matxv: Dict[str, float]) -> Dict[str, float]:
    for k in mat.keys():
        sum: float = 0
        for kk in mat[k]:
            sum = sum + mat[k][kk] * v[k]
        matxv[kk] = sum

    return matxv


def step_spr_regular(mat: Dict[str, Dict[str, int]],
                     v: Dict[str, float]) -> Dict[str, float]:
    matxv: Dict[str, float] = {}
    for k in mat.keys():
        for kk in mat[k]:
            val = mat[k][kk] * v[kk]
            if kk not in matxv:
                matxv[k] = val
            else:
                matxv[k] += val

    return matxv


def socialpagerank(matpageuser: Dict[str, Dict[str, int]],
                   matannotationpage: Dict[str, Dict[str, int]],
                   matuserannotation: Dict[str, Dict[str, int]],
                   matp: Dict[str, float], maxIt: int) \
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
