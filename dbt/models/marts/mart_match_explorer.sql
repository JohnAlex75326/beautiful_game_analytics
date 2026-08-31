with matches as (

    select *
    from {{ ref('stg_matches') }}

),

teams as (

    select *
    from {{ ref('stg_teams') }}

),

final as (

    select

        m.match_id,
        m.competition_id,
        m.competition_code,
        m.season_id,
        m.matchday,
        m.stage,
        m.utc_date,
        m.status,

        m.home_team_id,
        home_team.team_name as home_team_name,
        home_team.short_name as home_team,
        home_team.tla as home_tla,

        m.away_team_id,
        away_team.team_name as away_team_name,
        away_team.short_name as away_team,
        away_team.tla as away_tla,

        m.home_score,
        m.away_score,
        m.result,

        case
            when m.status = 'FINISHED'
                then cast(m.home_score as varchar)
                     || ' – '
                     || cast(m.away_score as varchar)

            when m.status in ('IN_PLAY', 'PAUSED')
                and m.home_score is not null
                and m.away_score is not null
                then cast(m.home_score as varchar)
                     || ' – '
                     || cast(m.away_score as varchar)

            else '–'
        end as scoreline,

        case
            when m.status = 'FINISHED' then 'Finished'
            when m.status in ('IN_PLAY', 'PAUSED') then 'Live'
            when m.status in ('TIMED', 'SCHEDULED') then 'Upcoming'
            else 'Other'
        end as match_state,

        m.source_last_updated,
        m.source_snapshot_date,
        m.loaded_at

    from matches m

    inner join teams home_team
        on m.home_team_id = home_team.team_id

    inner join teams away_team
        on m.away_team_id = away_team.team_id

)

select *
from final