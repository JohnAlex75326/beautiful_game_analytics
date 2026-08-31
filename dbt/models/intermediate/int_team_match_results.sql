with finished_matches as (

    select *
    from {{ ref('stg_matches') }}

    where status = 'FINISHED'

),

home_team_results as (

    select

        concat(
            cast(match_id as varchar),
            '-',
            cast(home_team_id as varchar)
        ) as team_match_key,

        match_id,
        competition_id,
        competition_code,
        season_id,
        matchday,
        utc_date,

        home_team_id as team_id,
        away_team_id as opponent_team_id,

        'HOME' as venue,

        home_score as goals_for,
        away_score as goals_against,

        case
            when result = 'H' then 'W'
            when result = 'D' then 'D'
            when result = 'A' then 'L'
        end as team_result,

        case
            when result = 'H' then 3
            when result = 'D' then 1
            when result = 'A' then 0
        end as points_earned,

        source_snapshot_date,
        loaded_at

    from finished_matches

),

away_team_results as (

    select

        concat(
            cast(match_id as varchar),
            '-',
            cast(away_team_id as varchar)
        ) as team_match_key,

        match_id,
        competition_id,
        competition_code,
        season_id,
        matchday,
        utc_date,

        away_team_id as team_id,
        home_team_id as opponent_team_id,

        'AWAY' as venue,

        away_score as goals_for,
        home_score as goals_against,

        case
            when result = 'A' then 'W'
            when result = 'D' then 'D'
            when result = 'H' then 'L'
        end as team_result,

        case
            when result = 'A' then 3
            when result = 'D' then 1
            when result = 'H' then 0
        end as points_earned,

        source_snapshot_date,
        loaded_at

    from finished_matches

),

combined as (

    select *
    from home_team_results

    union all

    select *
    from away_team_results

)

select *
from combined