-- summary views the streamlit app reads from
-- only eligible rows (normal restart, driver running before and after) count toward gains

-- each driver across all safety cars
create view v_driver_impact as
select
    driver,
    count(*) as sc_count,
    round(avg(position_gain), 2) as avg_gain,
    sum(position_gain) as total_gain,
    round(100.0 * sum(position_gain > 0) / count(*), 1) as pct_gained,
    round(100.0 * sum(position_gain = 0) / count(*), 1) as pct_no_change,
    round(100.0 * sum(position_gain < 0) / count(*), 1) as pct_lost
from driver_sc_impact
where eligible = 1
group by driver;

-- each team per season, team names change between seasons so keep season in
create view v_team_impact as
select
    r.season,
    d.team,
    count(*) as driver_sc_count,
    round(avg(d.position_gain), 2) as avg_gain,
    sum(d.position_gain) as total_gain,
    round(100.0 * sum(d.position_gain > 0) / count(*), 1) as pct_gained
from driver_sc_impact d
join race r on r.session_key = d.session_key
where d.eligible = 1
group by r.season, d.team;

-- how often each circuit gets a safety car, share of races is fairer than raw count
create view v_circuit_sc as
select
    circuit,
    count(*) as races,
    sum(sc_count) as sc_total,
    sum(sc_count > 0) as races_with_sc,
    round(100.0 * sum(sc_count > 0) / count(*), 1) as pct_races_with_sc,
    round(1.0 * sum(sc_count) / count(*), 2) as sc_per_race
from race
group by circuit;

-- did pitting under the sc go with gaining or losing places
create view v_pit_effect as
select
    case when pitted_during_sc = 1 then 'pitted' else 'stayed out' end as pit_choice,
    count(*) as observations,
    round(avg(position_gain), 2) as avg_gain,
    round(100.0 * sum(position_gain > 0) / count(*), 1) as pct_gained,
    round(100.0 * sum(position_gain < 0) / count(*), 1) as pct_lost
from driver_sc_impact
where eligible = 1
group by pitted_during_sc;

-- who gains depends on where you were running when the sc came out
create view v_gain_by_position as
select
    case
        when position_before <= 3 then 'P1-3'
        when position_before <= 6 then 'P4-6'
        when position_before <= 10 then 'P7-10'
        when position_before <= 15 then 'P11-15'
        else 'P16+'
    end as position_band,
    min(position_before) as band_order,
    count(*) as observations,
    round(avg(position_gain), 2) as avg_gain,
    round(100.0 * sum(position_gain > 0) / count(*), 1) as pct_gained
from driver_sc_impact
where eligible = 1
group by position_band;

-- pit call measured right after the restart vs at the chequered flag
-- final = position before the sc minus finishing position, only drivers who finished
create view v_pit_short_vs_final as
select
    case when pitted_during_sc = 1 then 'pitted' else 'stayed out' end as pit_choice,
    count(*) as observations,
    round(avg(position_gain), 2) as avg_gain_restart,
    round(avg(position_before - finish_position), 2) as avg_gain_finish
from driver_sc_impact
where eligible = 1 and race_status = 'finished' and finish_position is not null
group by pitted_during_sc;

-- did the sc change who was leading
create view v_lead_changes as
select
    i.session_key,
    i.sc_event_number,
    r.season,
    r.circuit,
    i.driver as leader_before,
    case when i.position_after = 1 then 0 else 1 end as lead_changed
from driver_sc_impact i
join race r on r.session_key = i.session_key
where i.eligible = 1 and i.position_before = 1;

-- biggest single sc swings, both directions
create view v_biggest_swings as
select
    r.season,
    r.circuit,
    i.sc_event_number,
    i.driver,
    i.team,
    i.position_before,
    i.position_after,
    i.position_gain,
    i.pitted_during_sc,
    i.finish_position
from driver_sc_impact i
join race r on r.session_key = i.session_key
where i.eligible = 1;
