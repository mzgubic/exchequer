function months(df::DataFrame)::Float64

    dayinmonth = 365.25 / 12
    ndays = Dates.value(maximum(df.date) - minimum(df.date))
    return ndays / dayinmonth
    
end


function plot_categories(expenses::DataFrame)

    # sort the categories by total spent
    categories = Exchequer.aggregate(expenses, "category")
    sort!(categories, :amount_sum, rev=true)

    nmonths = months(expenses)
    currency = expenses.currency[1]

    # figure
    bar(categories.category, categories.amount_sum / nmonths,
        xrotation=20,
        ylabel="Monthly spending ($currency)",
        fillcolor=Exchequer.colors,
        legend=nothing)
    ylims!((0, ylims()[2]))

    # save
    savefig("figures/categories.pdf")

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

    return groups
end

function plot_monthly(expenses::DataFrame)

    # sort the categories by total spent
    categories = Exchequer.aggregate(expenses, "category")
    sort!(categories, :amount_sum, rev=true)

    # sort by year and month and category
    groups = Exchequer.aggregate(expenses, "year", "month", "category")
    fill_zeros!(groups)

    #return groups

end


