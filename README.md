# Capstone Project Proposal

## F1 Safety Car Impact Analysis

### 1. Abstract

I want to study how much Safety Cars actually change the outcome of a Formula 1 race. When a Safety Car is deployed, the field can become more compressed, gaps between drivers can decrease, and teams may have new opportunities to gain positions through strategy and pit stops.

My project will analyze Formula 1 race data from 2018–2026 to measure which drivers and teams benefit the most from Safety Car periods. I will compare driver positions before and after Safety Car interventions and examine factors such as pit-stop timing, track location, and race circumstances.

The final goal is to create an interactive dashboard that allows users to explore the data and understand which races and drivers were most affected by Safety Car events.

---

### 2. What Are the Goals?

My main research question is:

> **How much does a Safety Car change the outcome of an F1 race, and which drivers and teams benefit the most?**

#### What I Want to Find

* How many positions drivers gain or lose, on average, after a Safety Car intervention
* Which racing circuits are most affected by Safety Car events
* Whether the timing of a pit stop during a Safety Car period affects the final result
* Which drivers and teams benefit most consistently from Safety Car interventions
* Specific races where a Safety Car may have had a major impact on the final result
* Clear charts and visualizations that explain these patterns

#### What I Will Deliver

1. An interactive website or dashboard where users can explore and filter the data
2. All project code on GitHub so the data-processing and analysis methods are transparent
3. A presentation slide deck showing the main findings
4. A complete explanation of the data, methodology, analysis, and results

---

### 3. Where Will I Get the Data?

I will use free and publicly accessible Formula 1 data sources.

#### FastF1 Library

FastF1 is a free, open-source Python library that provides access to Formula 1 timing and session data. I plan to use it as one of the primary sources for race and lap-level information.

#### Data I Need to Collect

* Final race position for each driver in each race
* Starting grid position
* Qualifying position
* Safety Car events and the laps during which they occurred
* Pit-stop information and pit-stop laps
* Lap times
* Driver and constructor/team information
* Race status, including finishes and retirements (DNFs)

#### Other Data Sources

I may also use public F1 datasets from sources such as Kaggle or the Jolpica F1 API to supplement or validate the data collected through FastF1.

These additional sources will be used to cross-check important fields and improve data quality where necessary.

---

### 4. Project Approach

The project will follow a simple data engineering pipeline:

**Data Collection → Data Cleaning → Data Transformation → SQL Database → Analysis → Interactive Dashboard**

Python will be used to collect and clean the data, SQL will be used to organize and analyze the data, and a visualization tool will be used to create the final interactive dashboard.

The analysis will focus on measuring position changes before and after Safety Car interventions and identifying patterns across drivers, teams, circuits, and races.

---

### 5. Expected Outcome

The final project will provide a data-driven view of how Safety Car interventions can influence Formula 1 race outcomes.

Rather than simply identifying which drivers gained positions, the project will examine whether those gains were associated with Safety Car timing, pit-stop decisions, circuit characteristics, and other race circumstances.

The project will demonstrate how raw sports data can be transformed through a data engineering pipeline into meaningful and interactive insights.
