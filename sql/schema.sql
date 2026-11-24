-- tables for the f1 safety car database
-- rebuilt from scratch every time load_database.py runs

drop view if exists v_driver_impact;
drop view if exists v_team_impact;
drop view if exists v_circuit_sc;
drop view if exists v_pit_effect;
drop view if exists v_gain_by_position;
drop view if exists v_pit_short_vs_final;
drop view if exists v_lead_changes;
drop view if exists v_biggest_swings;
drop table if exists team_color;
drop table if exists driver_sc_impact;
drop table if exists sc_event;
drop table if exists race;

-- one row per grand prix (sprints not included)
create table race (
    session_key   integer primary key,
    season        integer not null,
    round         integer not null,
    country       text,
    circuit       text not null,
    race_date     text,
    sc_count      integer not null default 0
);

-- one row per full safety car, vsc is not in here
create table sc_event (
    session_key        integer not null references race(session_key),
    sc_event_number    integer not null,
    deploy_lap         integer,
    deployed_time      text,
    end_type           text check (end_type in ('restart', 'red_flag', 'race_end', 'missing')),
    restart_lap        integer,
    end_time           text,
    duration_seconds   real,
    validation_status  text check (validation_status in ('ok', 'review')),
    flags              text,
    primary key (session_key, sc_event_number)
);

-- one row per driver per safety car
create table driver_sc_impact (
    session_key        integer not null,
    sc_event_number    integer not null,
    driver_number      integer not null,
    driver             text not null,
    team               text,
    position_before    integer,
    position_after     integer,
    position_gain      integer,
    pitted_during_sc   integer not null check (pitted_during_sc in (0, 1)),
    finish_position    integer,
    race_status        text check (race_status in ('finished', 'dnf', 'dns', 'dsq')),
    eligible           integer not null check (eligible in (0, 1)),
    exclusion_reason   text,
    primary key (session_key, sc_event_number, driver_number),
    foreign key (session_key, sc_event_number) references sc_event(session_key, sc_event_number)
);

-- official team colors from openf1, per season since liveries change
create table team_color (
    season      integer not null,
    team        text not null,
    team_colour text not null,
    primary key (season, team)
);
