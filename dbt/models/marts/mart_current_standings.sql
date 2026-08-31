with standings_with_latest_date as (

    select

        *,

        max(snapshot_date) over (
            partition by
                competition_code,
                season_id
        ) as latest_snapshot_date

    from {{ ref('stg_standings') }}

),

latest_standings as (

    select *

    from standings_with_latest_date

    where snapshot_date = latest_snapshot_date

),

final as (

    select

        concat(
            s.competition_code,
            '-',
            cast(s.season_id as varchar),
            '-',
            cast(s.team_id as varchar),
            '-',
            cast(s.snapshot_date as varchar)
        ) as standings_key,

        s.competition_id,
        s.competition_code,
        s.season_id,

        s.snapshot_date,
        s.snapshot_matchday,

        s.team_id,
        t.team_name,
        t.short_name,
        t.tla,

        -- Club artwork reference
        t.sportsdb_badge_url,

        s.position,
        s.played,
        s.won,
        s.drawn,
        s.lost,

        s.goals_for,
        s.goals_against,
        s.goal_difference,

        s.points,
        s.form,

        r.is_reconciled,
        r.played_delta,
        r.points_delta,
        r.goals_for_delta,
        r.goals_against_delta

    from latest_standings s

    inner join {{ ref('stg_teams') }} t
        on s.team_id = t.team_id

    left join {{ ref('int_standings_reconciliation') }} r
        on s.competition_code = r.competition_code
        and s.season_id = r.season_id
        and s.team_id = r.team_id
        and s.snapshot_date = r.snapshot_date

)

select *
from final