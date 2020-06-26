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
