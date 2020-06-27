
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
        fillcolor=COLORS,
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

    # make figures
    currency = expenses.currency[1]
    plot_unstacked(categories, groups, currency)

end

function plot_unstacked(categories::DataFrame, groups::DataFrame, currency::String)
    
    # clear the figure
    plot()

    # and show every category separately
    for (cat, color) in zip(categories.category, COLORS)

        # select the spending and construct dates
        spending = groups[groups.category .== cat, :]
        xpos = [i for i in 1:1:nrow(spending)]

        plot!(xpos, spending.amount_sum, label=cat, color=color, linewidth=2)
    end

    # xticks cosmetics
    spending = groups[groups.category .== "sport", :]
    xpos = [i for i in 1:1:nrow(spending)]
    yearmonths = zip(spending.year, spending.month)
    labels = [m == 1 ? "$(MONTHS[m])\n$y" : "$(MONTHS[m])" for (y,m) in yearmonths]
    xticks!(xpos, labels)

    # ylabel
    ylabel!("Monthly spending ($currency)")

    # save
    savefig("figures/monthly_unstacked.pdf")

end





