with latest_standing_snapshot as (

    select *
    from {{ ref('stg_standings') }}

    where snapshot_date = (
        select max(snapshot_date)
        from {{ ref('stg_standings') }}
    )

),

derived_match_performance as (

    select

        team_id,

        count(*) as derived_played,

        sum(
            case when team_result = 'W' then 1 else 0 end
        ) as derived_won,

        sum(
            case when team_result = 'D' then 1 else 0 end
        ) as derived_drawn,

        sum(
            case when team_result = 'L' then 1 else 0 end
        ) as derived_lost,

        sum(points_earned) as derived_points,
        sum(goals_for) as derived_goals_for,
        sum(goals_against) as derived_goals_against

    from {{ ref('int_team_match_results') }}

    group by team_id

),

reconciled as (

    select

        s.competition_id,
        s.competition_code,
        s.season_id,
        s.snapshot_date,
        s.snapshot_matchday,
        s.team_id,

        s.played as official_played,
        coalesce(d.derived_played, 0) as derived_played,

        s.won as official_won,
        coalesce(d.derived_won, 0) as derived_won,

        s.drawn as official_drawn,
        coalesce(d.derived_drawn, 0) as derived_drawn,

        s.lost as official_lost,
        coalesce(d.derived_lost, 0) as derived_lost,

        s.points as official_points,
        coalesce(d.derived_points, 0) as derived_points,

        s.goals_for as official_goals_for,
        coalesce(
            d.derived_goals_for,
            0
        ) as derived_goals_for,

        s.goals_against as official_goals_against,
        coalesce(
            d.derived_goals_against,
            0
        ) as derived_goals_against,

        s.played
            - coalesce(d.derived_played, 0)
            as played_delta,

        s.points
            - coalesce(d.derived_points, 0)
            as points_delta,

        s.goals_for
            - coalesce(d.derived_goals_for, 0)
            as goals_for_delta,

        s.goals_against
            - coalesce(d.derived_goals_against, 0)
            as goals_against_delta,

        case

            when
                s.played = coalesce(d.derived_played, 0)
                and s.points = coalesce(d.derived_points, 0)
                and s.goals_for = coalesce(
                    d.derived_goals_for,
                    0
                )
                and s.goals_against = coalesce(
                    d.derived_goals_against,
                    0
                )

            then true

            else false

        end as is_reconciled

    from latest_standing_snapshot s

    left join derived_match_performance d
        on s.team_id = d.team_id

)

select *
from reconciled