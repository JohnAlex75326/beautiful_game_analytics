with source as (

    select *
    from {{ source(
        'football_warehouse',
        'fact_standing_snapshot'
    ) }}

),

renamed as (

    select

        competition_id,
        competition_code,
        season_id,

        snapshot_matchday,
        snapshot_date,

        team_id,
        position,

        played,
        won,
        drawn,
        lost,

        goals_for,
        goals_against,
        goal_difference,

        points,
        form,

        loaded_at

    from source

)

select *
from renamed