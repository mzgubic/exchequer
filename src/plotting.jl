
function plot_categories(expenses::DataFrame)

    # sort the categories by total spent
    categories = Exchequer.aggregate(expenses, "category")
    sort!(categories, :amount_sum, rev=true)

    nmonths = months(expenses)
    currency = expenses.currency[1]

    # figure
    bar(categories.category, categories.amount_sum / nmonths,
        xrotation=20, fillcolor=COLORS, legend=nothing, width=0.5)

    # cosmetics
    ylabel!("Monthly spending ($currency)")
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
              label=c, color=COLORS[i], alpha=0.8, width=0.01)
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

function plot_weekly(expenses::DataFrame)

    # sort the categories by total spent
    categories = Exchequer.aggregate(expenses, "category")
    sort!(categories, :amount_sum, rev=true)

    # day of week, normalised to per day spend
    day_exp = Exchequer.aggregate(expenses, "category", "dayofweek")
    ndays = Dates.value(maximum(expenses.date) - minimum(expenses.date))  
    day_exp.amount_sum /= (ndays/7)
    
    # prepare data for plotting
    data = zeros(7, nrow(categories))
    for (i, c) in enumerate(categories.category)
        for d in 1:1:7
            cut = (day_exp.category.==c) .& (day_exp.dayofweek.==d)
            if nrow(day_exp[cut, :]) != 0
                data[d, i] = day_exp[cut, "amount_sum"][1]
            end
        end
    end

    # plot histograms
    bins = [i for i in 0.5:1:7.5]
    lowers = bins[1:end-1]
    highers = bins[2:end]
    centres = 0.5*(lowers+highers)

    ncat = nrow(categories)
    width = 0.8 / ncat

    plot()
    for (i, c) in enumerate(categories.category)
        shift = (-(ncat/2)+(i-0.5))*width
        histogram!(centres.+shift, bins=bins.+shift, weights=data[:, i],
                   bar_width=width, label=c, color=COLORS[i], width=0.5)
    end

    # total spend
    plot!(centres, sum(data, dims=2), color="black", label="total")

    # cosmetics
    currency = expenses.currency[1]
    ylabel!("Daily spending ($currency)")
    days = Dict(1=>"Mon", 2=>"Tue", 3=>"Wed", 4=>"Thu", 5=>"Fri", 6=>"Sat", 7=>"Sun")
    xticks!(centres, [days[d] for d in centres])
    savefig("figures/weekly.pdf")

end





