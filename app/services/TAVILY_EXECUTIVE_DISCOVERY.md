# TavilyExecutiveDiscoveryService

## Overview

Sophisticated executive discovery using Tavily search API and Gemini AI extraction. Designed for discovering executives from commercial property requirement signals extracted from LinkedIn posts.

## Tasks Implemented

1. Query Series Generation: Generic to specific queries, stops at evidence quality threshold (2+ title/role pieces)
2. URL Deduplication: Preserves distinct domain pages (company.com/about vs /leadership)
3. Result Prioritization: LinkedIn > company > news > other (non-destructive)
4. Gemini Extraction: Strict evidence only, no hallucination
5. Source-Weighted Confidence: Base 0.65 + source bonuses, capped at 1.0
6. Executive Deduplication: Fuzzy name matching (0.8 threshold), merges evidence

## Configuration

Environment variables:
- TAVILY_API_KEY
- GEMINI_API_KEY

Tunable parameters:
- GEMINI_BASE_CONFIDENCE = 0.65
- EVIDENCE_QUALITY_THRESHOLD = 2
- SOURCE_BONUSES: linkedin=0.15, company=0.10, news=0.05
- MULTI_SOURCE_BONUS = 0.10
