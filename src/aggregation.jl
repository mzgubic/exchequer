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

function fill_zeros!(groups::DataFrame)::DataFrame

    # get the earliest and latest months
    e_year = minimum(groups.year)
    e_month = minimum(groups.month[groups.year .== e_year])
    l_year = maximum(groups.year)
    l_month = maximum(groups.month[groups.year .== l_year])

    # get all distinct categories
    categories = unique(groups.category)

    # loop over all years and months
    for date in Date(e_year, e_month):Dates.Month(1):Date(l_year, l_month)
        y, m = year(date), month(date)
        #println(y, m)
        for category in categories
            cut = (groups.year.==y) .& (groups.month.==m) .& (groups.category.==category)
            #println(groups[cut, :])
            if nrow(groups[cut, :]) == 0
                #println("missing")
                push!(groups, (year=y, month=m, category=category, amount_sum=0))
            end
        end
    end

    sort!(groups)

    return groups
end


