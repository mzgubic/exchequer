include("src/Exchequer.jl")

using ArgParse
using .Exchequer


function parse()

    s = ArgParseSettings()

    @add_arg_table! s begin
        "--currency"
            help = "choose which currency to report in"
            arg_type = String
            default = "EUR"
            range_tester = x -> x in ["EUR", "GBP"]
    end

    return parse_args(s)

end

function main()

    # parse arguments
    args = parse()
    println(args)

    # update the downloaded files
    Exchequer.move_downloads()

    # load the dataframes
    df_expenses = Exchequer.load_expenses()
    df_incomes = Exchequer.load_incomes()
    df_fxs = Exchequer.load_fxs()

    # exchange the currencies
    Exchequer.exchange!(df_expenses, args["currency"], df_fxs)
    Exchequer.exchange!(df_incomes, args["currency"], df_fxs)

    # plot away
    Exchequer.plot_categories(df_expenses)
    Exchequer.plot_monthly(df_expenses, df_incomes)
    Exchequer.plot_weekly(df_expenses)

    return nothing

end

main()

nothing
