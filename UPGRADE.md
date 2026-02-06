# UPGRADE: Real Estate Project Intelligence

This document outlines the next major capability upgrade for the WhatsApp real estate agent: **first-class project management** and **dynamic, contextual recommendations** tailored to the real estate domain.

## Why this upgrade matters

The system is being optimized specifically for real estate sales. To behave like a skilled human agent, the AI must understand structured project information, reason over it, and provide personalized guidance within WhatsApp conversations.

## Core concept: Project

A **project** represents a real estate offering such as a residential building, gated community, villa project, or condominium (e.g., Kalpataru). Each project should encapsulate structured, queryable information:

- Project name and brand
- Location/address and neighborhood context
- Property type (apartment, villa, condo, mixed-use, etc.)
- Available units and configurations (2BHK, 3BHK, penthouse, etc.)
- Pricing ranges (min/max or per configuration)
- Carpet and built-up area ranges
- Amenities (pool, gym, kids play area, parking, security, turf, etc.)
- Images/media for units and views
- Availability and status (ready, under construction, sold out, etc.)

## Agent behavior requirements

### 1) Intelligent project recommendations
When a lead initiates a conversation, the agent must infer preferences and recommend suitable projects based on:
- Budget constraints
- Location preference
- Unit size/configuration
- Lifestyle needs (amenities, community vibe, etc.)

The agent should **filter and rank projects dynamically** rather than relying on static flows or hard-coded scripts.

### 2) Deep comparisons within a project
The agent should support rich comparisons **within a single project**, including:
- Differences across unit types (e.g., 2BHK vs 3BHK)
- Floor levels and view quality
- Layout variations
- Pricing differences
- Availability across units

### 3) Visual comparisons in WhatsApp
The agent should be able to present multiple images of the same flat or view, including:
- Multiple angles of the same unit
- Side-by-side view comparisons
- Images of similar flats within the same project

These comparisons should help leads make informed decisions visually, directly within WhatsApp.

### 4) Contextual detail delivery
Critical property details should be surfaced **contextually**, not dumped all at once. The agent must intelligently reveal:
- Pricing
- Carpet/built-up area
- Configuration
- Availability
- Amenities and lifestyle features

The information should be delivered in response to explicit requests or implicit signals of interest.

### 5) Multi-project support per client
Each client may manage multiple projects. The backend must support:
- Efficient lookup across projects
- Dynamic filtering by lead preferences
- Project comparisons across the portfolio

### 6) Retrieval strategy
Retrieval-Augmented Generation (RAG) is a candidate, but hybrid approaches should be considered for **accuracy, performance, and cost**:
- Structured DB queries for hard filters (price, location, configuration)
- Targeted retrieval for descriptive content or marketing narratives
- Caching for popular project matches

### 7) Adaptive style by property type
The agent should alter its questioning, recommendations, and tone based on property type:
- Villas emphasize privacy, land, lifestyle
- Apartments emphasize amenities, security, community
- Condos emphasize convenience and amenities
- Mixed-use emphasizes connectivity and lifestyle

## Goal state

The upgraded agent should replicate the end-to-end behavior of a skilled real estate sales agent, including:
- Discovery and qualification
- Project recommendation
- Unit comparison
- Objection handling
- Follow-ups

All within WhatsApp, with rich, contextual information and visual support.
