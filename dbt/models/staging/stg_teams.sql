with source as (

    select *
    from {{ source('football_warehouse', 'dim_team') }}

),

renamed as (

    select

        team_id,
        team_name,
        short_name,
        tla,
        country,
        venue_name,
        founded,
        club_colors,

        -- football-data.org source metadata
        crest_url,

        -- manually reviewed seasonal artwork reference
        sportsdb_team_id,
        sportsdb_team_name,
        sportsdb_badge_url,
        sportsdb_source,
        sportsdb_resolution_method,
        sportsdb_fetched_at,

        competition_code,
        loaded_at

    from source

)

select *
from renamed