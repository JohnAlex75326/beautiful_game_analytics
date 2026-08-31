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
        crest_url,
        competition_code,
        loaded_at

    from source

)

select *
from renamed