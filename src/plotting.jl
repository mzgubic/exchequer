
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

function plot_monthly(expenses::DataFrame, incomes::DataFrame)

    # sort the categories by total spent
    categories = Exchequer.aggregate(expenses, "category")
    sort!(categories, :amount_sum, rev=true)

    # sort expenses by year and month and category
    exp_groups = Exchequer.aggregate(expenses, "year", "month", "category")
    fill_zeros!(exp_groups)

    # sort incomes by year and month and category
    inc_groups = Exchequer.aggregate(incomes, "year", "month")
    fill_zeros!(inc_groups)

    # make sure they have the same starting and ending point in time
    fill_zeros!(exp_groups, inc_groups)

    # make figures
    currency = expenses.currency[1]
    plot_unstacked(categories, exp_groups, currency)
    plot_stacked(categories, exp_groups, inc_groups, currency)

    return inc_groups

end

function plot_unstacked(categories::DataFrame, groups::DataFrame, currency::String)
    
    # clear the figure
    plot()

    # and show every category separately
    spending = groups[groups.category .== "sport", :]
    xpos = [i for i in 1:1:nrow(spending)]
    for (cat, color) in zip(categories.category, COLORS)
        # select the spending and construct dates
        spending = groups[groups.category .== cat, :]
        plot!(xpos, spending.amount_sum, label=cat, color=color, linewidth=2)
    end

    # xticks cosmetics
    yearmonths = zip(spending.year, spending.month)
    labels = [m == 1 ? "$(MONTHS[m])\n$y" : "$(MONTHS[m])" for (y,m) in yearmonths]
    xticks!(xpos, labels)

    # other
    ylabel!("Monthly spending ($currency)")
    ylims!(0, ylims()[2])
    xlims!(1, xlims()[2])

    # save
    savefig("figures/monthly_unstacked.pdf")

end

function plot_stacked(categories::DataFrame,
                      exp_groups::DataFrame,
                      inc_groups::DataFrame,
                      currency::String)

    # clear the figure
    plot()

    # get the upper and lower limits for each category
    ncat = nrow(categories)
    nmonth = nrow(exp_groups) ÷ ncat
    ys = zeros(ncat+1, nmonth)
    for (i, c) in enumerate(categories.category)
        ys[i+1, :] = exp_groups[exp_groups.category .== c, "amount_sum"]
    end
    cs = cumsum(ys, dims=1)
    lowers = cs[1:end-1, :]
    uppers = cs[2:end, :]

    total_expense = uppers[end,:]
    total_income = inc_groups.amount_sum

    # plot mains
    xpos = [i for i in 1:1:nmonth]
    for (i, c) in enumerate(categories.category)
        plot!(xpos, lowers[i, :], fillrange=uppers[i, :],
              label=c, color=COLORS[i], alpha=0.8)
    end

    # plot income
    plot!(xpos, inc_groups.amount_sum,
          linewidth=2, linecolor="black", linestyle=:dot, label="income")

    # plot net numbers
    net = [trunc(Int, n) for n in total_income - total_expense]
    ypos = [max(a, b)+50 for (a, b) in zip(total_income, total_expense)]
    texts = [(x, y, text(n, 7, :left, n > 0 ? :green : :red,))
             for (x, y, n) in zip(xpos, ypos, net)]
    annotate!(texts)

    # xticks cosmetics
    spending = exp_groups[exp_groups.category .== "sport", :]
    yearmonths = zip(spending.year, spending.month)
    labels = [m == 1 ? "$(MONTHS[m])\n$y" : "$(MONTHS[m])" for (y,m) in yearmonths]
    xticks!(xpos, labels)

    # other cosmetics
    ylabel!("Monthly spending ($currency)")
    ylims!(0, ylims()[2])
    xlims!(1, xlims()[2])

    savefig("figures/monthly_stacked.pdf")

end





