"""Semantic ranking module for candidate-job matches."""

from .ranker import rank_matches, RankedMatch

__all__ = ["rank_matches", "RankedMatch"]
