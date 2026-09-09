# 🏎️ F1 Safety Car Impact Analysis

**Project Status:** Proposal / Planning

## Capstone Project Proposal

### 1. Abstract

I want to study how much Safety Cars actually change the outcome of a Formula 1 race. When a Safety Car is deployed, the field can become more compressed, gaps between drivers can decrease, and teams may have new opportunities to gain positions through strategy and pit stops.

My project will analyze Formula 1 race data from 2018–2026 to measure which drivers and teams benefit the most from Safety Car periods. I will compare driver positions before and after Safety Car interventions and look at factors such as pit-stop timing, track location, and race circumstances.

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
2. All project code on GitHub so people can see how the data was collected, cleaned, and analyzed
3. A presentation slide deck showing the main findings
4. A complete explanation of the data, methodology, analysis, and results

---

### 3. Where Will I Get the Data?

I will use free and publicly accessible Formula 1 data sources.

#### FastF1 Library

FastF1 is a free, open-source Python library that provides access to Formula 1 timing and session data. I plan to use it as one of the main sources for race and lap-level information.

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

These additional sources will be used to cross-check important information and improve data quality where necessary.

---

### 4. Project Approach

The project will follow a simple data engineering process:

**Data Collection → Data Cleaning → Data Transformation → SQL Database → Analysis → Interactive Dashboard**

Python will be used to collect and clean the data. SQL will be used to organize and analyze the data. A visualization tool will be used to create the final interactive dashboard.

The analysis will focus on measuring position changes before and after Safety Car interventions and looking for patterns across drivers, teams, circuits, and races.

---

### 5. Expected Outcome

The final project will provide a data-based view of how Safety Car interventions can influence Formula 1 race outcomes.

Instead of only looking at which drivers gained positions, I will look at whether those gains were related to Safety Car timing, pit-stop decisions, circuit characteristics, and other race situations.

The project will show how raw sports data can be collected, cleaned, organized, and turned into useful and interactive insights.

---

### 6. Project Timeline

| Week        | What I Will Work On                                                              | What I Hope to Finish                |
| ----------- | -------------------------------------------------------------------------------- | ------------------------------------ |
| **Week 1**  | Finalize the project idea, research question, and goals                          | Final project proposal               |
| **Week 2**  | Look at the available F1 data sources and decide which ones I will use           | Final data sources                   |
| **Week 3**  | Collect the F1 race, driver, lap, pit stop, and Safety Car data                  | Raw data                             |
| **Week 4**  | Clean the data and deal with missing or incorrect information                    | Cleaned data                         |
| **Week 5**  | Build the Python ETL process to collect, clean, and organize the data            | Working ETL process                  |
| **Week 6**  | Create the SQL database and organize the data into tables                        | Working SQL database                 |
| **Week 7**  | Create the calculations I need, such as position changes and Safety Car impact   | Analysis-ready data                  |
| **Week 8**  | Explore the data and look for interesting patterns and races                     | Initial results and charts           |
| **Week 9**  | Start building the interactive dashboard                                         | First version of the dashboard       |
| **Week 10** | Test the data, check my calculations, and make improvements to the dashboard     | Final dashboard                      |
| **Week 11** | Finish the analysis and work on the presentation                                 | Final results and presentation draft |
| **Week 12** | Put everything together and prepare the final GitHub submission and presentation | Completed capstone project           |
