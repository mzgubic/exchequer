include("src/Exchequer.jl")

using .Exchequer

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
    #Exchequer.plot_categories(df_expenses)
    return Exchequer.plot_monthly(df_expenses, df_incomes)

end

main()

nothing
