include("src/Exchequer.jl")

using .Exchequer


function plot_categories(expenses::DataFrame)

    # sort the categories by total spent
    categories = Exchequer.aggregate(df_expenses, "category")
    sort!(categories, :amount_sum, rev=true)

    println(categories)

    # figure
    bar(1:nrow(categories), categories.amount_sum)

    # label xaxis
    # legend
    # colors
    # divide by month
    # save
    

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
    plot_categories(df_expenses)

end

main()
