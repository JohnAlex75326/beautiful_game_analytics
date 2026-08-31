with source as (

    select *
    from {{ source('football_warehouse', 'fact_match') }}

),

renamed as (

    select

        match_id,
        competition_id,
        competition_code,
        season_id,
        matchday,
        stage,
        utc_date,
        status,

        home_team_id,
        away_team_id,

        home_score,
        away_score,

        result,

        source_last_updated,
        source_snapshot_date,
        loaded_at

    from source

)

select *
from renamed