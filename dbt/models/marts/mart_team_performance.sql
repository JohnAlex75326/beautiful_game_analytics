with team_results as (

    select *
    from {{ ref('int_team_match_results') }}

),

aggregated as (

    select

        competition_id,
        competition_code,
        season_id,
        team_id,

        count(*) as played,

        sum(
            case
                when team_result = 'W' then 1
                else 0
            end
        ) as won,

        sum(
            case
                when team_result = 'D' then 1
                else 0
            end
        ) as drawn,

        sum(
            case
                when team_result = 'L' then 1
                else 0
            end
        ) as lost,

        sum(points_earned) as points,

        sum(goals_for) as goals_for,
        sum(goals_against) as goals_against,

        sum(goals_for)
            - sum(goals_against)
            as goal_difference,

        round(
            sum(points_earned) * 1.0
            / nullif(count(*), 0),
            3
        ) as points_per_game,

        round(
            avg(goals_for),
            3
        ) as goals_for_per_game,

        round(
            avg(goals_against),
            3
        ) as goals_against_per_game,

        sum(
            case
                when venue = 'HOME' then 1
                else 0
            end
        ) as home_played,

        sum(
            case
                when venue = 'HOME'
                then points_earned
                else 0
            end
        ) as home_points,

        sum(
            case
                when venue = 'AWAY' then 1
                else 0
            end
        ) as away_played,

        sum(
            case
                when venue = 'AWAY'
                then points_earned
                else 0
            end
        ) as away_points

    from team_results

    group by
        competition_id,
        competition_code,
        season_id,
        team_id

),

final as (

    select

        concat(
            a.competition_code,
            '-',
            cast(a.season_id as varchar),
            '-',
            cast(a.team_id as varchar)
        ) as team_performance_key,

        a.competition_id,
        a.competition_code,
        a.season_id,

        a.team_id,
        t.team_name,
        t.short_name,
        t.tla,

        a.played,
        a.won,
        a.drawn,
        a.lost,

        a.points,

        a.goals_for,
        a.goals_against,
        a.goal_difference,

        a.points_per_game,
        a.goals_for_per_game,
        a.goals_against_per_game,

        a.home_played,
        a.home_points,

        a.away_played,
        a.away_points

    from aggregated a

    inner join {{ ref('stg_teams') }} t
        on a.team_id = t.team_id

)

select *
from final