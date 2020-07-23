"""
Add explicit year, month, and dayofweek columns to the df
"""
function _precompute!(df::DataFrame)::DataFrame

    df[!, "year"] = [Dates.year(d) for d in df.date]
    df[!, "month"] = [Dates.month(d) for d in df.date]
    df[!, "dayofweek"] = [Dates.dayofweek(d) for d in df.date]

    return df
end

function aggregate(df::DataFrame, columns...)
    
    # precompute some utilities for dates
    _precompute!(df)

    # group by and combine
    gdf = groupby(df, [c for c in columns])
    res = combine(gdf, :amount => sum)

    return res
    
end

function months(df::DataFrame)::Float64

    dayinmonth = 365.25 / 12
    ndays = Dates.value(maximum(df.date) - minimum(df.date))
    return ndays / dayinmonth
    
end

function fill_zeros!(groups::DataFrame)

    if "month" in names(groups)
        return fill_zeros_ym!(groups)
    else
        return fill_zeros_y!(groups)
    end
end

function fill_zeros_y!(groups::DataFrame)

    # earliest and latest year
    e_year = minimum(groups.year)
    l_year = maximum(groups.year)

    for year in e_year:1:l_year
        for c in unique(groups.category)
            cut = (groups.year .== year) .& (groups.category .== c)
            if nrow(groups[cut, :]) == 0
                push!(groups, (year=year, category=c, amount_sum=0))
            end
        end
    end

end

function fill_zeros_ym!(groups::DataFrame)

    # get the earliest and latest months
    e_year = minimum(groups.year)
    e_month = minimum(groups.month[groups.year .== e_year])
    l_year = maximum(groups.year)
    l_month = maximum(groups.month[groups.year .== l_year])

    # get all distinct categories
    has_categories = "category" in names(groups)
    if has_categories
        categories = unique(groups.category)
    end

    # loop over all years and months
    for date in Date(e_year, e_month):Dates.Month(1):Date(l_year, l_month)

        # extract the year and date
        y, m = year(date), month(date)

        # if has categories treat them separately
        if has_categories
            for cat in categories
                cut = (groups.year.==y) .& (groups.month.==m) .& (groups.category.==cat)
                if nrow(groups[cut, :]) == 0
                    push!(groups, (year=y, month=m, category=cat, amount_sum=0))
                end
            end
        # otherwise just one
        else
            cut = (groups.year.==y).&(groups.month.==m)
            if nrow(groups[cut, :]) == 0
                push!(groups, (year=y, month=m, amount_sum=0))
            end
        end
    end

    sort!(groups)

end


function fill_zeros!(exp::DataFrame, inc::DataFrame)

    # construct dates from years and months
    dates1 = unique([Date(y, m) for (y, m) in zip(exp.year, exp.month)])
    dates2 = unique([Date(y, m) for (y, m) in zip(inc.year, inc.month)])

    # determine the earliest and latest date
    earliest = minimum(vcat(dates1, dates2))
    latest = maximum(vcat(dates1, dates2))

    # check each year month combination to see if it is in both arrays
    for date in earliest:Dates.Month(1):latest

        y, m = year(date), month(date)

        # fill in expenses
        cut1 = (exp.year.==y) .& (exp.month.==m)
        if nrow(exp[cut1, :]) == 0
            push!(exp, (year=y, month=m, category="sport", amount_sum=0))
        end

        # fill in incomes
        cut2 = (inc.year.==y) .& (inc.month.==m)
        if nrow(inc[cut2, :]) == 0
            push!(inc, (year=y, month=m, amount_sum=0))
        end

    end

    return nothing

end




