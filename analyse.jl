include("src/Exchequer.jl")

using .Exchequer

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

function plot_monthly(expenses::DataFrame)

    # sort the categories by total spent
    categories = Exchequer.aggregate(expenses, "category")
    sort!(categories, :amount_sum, rev=true)

    # sort by year and month and category
    groups = Exchequer.aggregate(expenses, "year", "month", "category")
    fill_zeros!(groups)
    
    return groups

end

function main()

    # update the downloaded files
    Exchequer.move_downloads()

    # load the dataframes
    df_expenses = Exchequer.load_expenses()
    df_incomes = Exchequer.load_incomes()
    df_fxs = Exchequer.load_fxs()

    # exchange the currencies
    Exchequer.exchange!(df_expenses, "EUR", df_fxs)

    # plot away
    #plot_categories(df_expenses)
    return plot_monthly(df_expenses)


end

main()
