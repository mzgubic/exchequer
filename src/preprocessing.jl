
function move_downloads()

    dl_dir = "/Users/mzgubic/Downloads/"
    for fname in readdir(dl_dir) # TODO: change to ~

        # order matters
        if occursin("Income", fname)
            println(fname)
            mv(dl_dir*fname, "data/income/"*fname, force=true)

        elseif occursin("Expenses", fname)
            println(fname)
            mv(dl_dir*fname, "data/expense/"*fname, force=true)

        elseif occursin("exchange", fname)
            println(fname)
            mv(dl_dir*fname, "data/fx/"*fname, force=true)
        end

    end

end

function is_individual(fpath)::Bool
    return !occursin("Repeated", fpath)
end

function step(row)
    if row.frequency == "DAILY"
        return Dates.Day(1)
    elseif row.frequency == "MONTHLY"
        return Dates.Month(1)
    else
        throw("Error")
    end
end

function load_repeated(fpath::String)::DataFrame

    # repeated df
    rep_df = DataFrame(CSV.File(fpath))

    # individual df
    df = DataFrame(date=Date[],
                   amount=Float64[],
                   currency=String[],
                   category=String[],
                   description=String[])

    # loop over repeated and extract individuals
    for row in eachrow(rep_df)
        datestep = step(row)
        daterange = range(row.start, row.end, step=datestep)
        amount = row.amount / length(daterange)
        for date in daterange
            push!(df, [date, amount, row.currency, row.category, row.description])
        end
    end

    return df

end

function load_expenses(fpath::String)::DataFrame

    # treat individual and repeated expenses separately
    println(fpath)
    if is_individual(fpath)
        return DataFrame(CSV.File(fpath))
    else
        return load_repeated(fpath)
    end

end

function load_expenses()::DataFrame
    expense_dir = "data/expense/"
    dfs = [load_expenses(expense_dir*fname) for fname in readdir(expense_dir)]
    reverse!(dfs)
    return vcat(dfs...)
end

function load_incomes()::DataFrame
    income_dir = "data/income/"
    return DataFrame(CSV.File(income_dir*"Expenses - Income.csv"))
end

function parse_from_to(fpath::String)::Tuple{String, String}

    fname = split(fpath, "/")[end]
    currencies = split(fname, "-exchange-rate")[1]

    first = split(currencies, "-")[1]
    second = split(currencies, "-")[2]

    d = Dict("euro"=>"EUR",
             "british"=>"GBP",
             "dollar"=>"USD")

    return d[first], d[second]
end

function load_fxs(fpath::String)::DataFrame

    # load the raw file
    header = 16 # ignore the first 15 lines in the file
    df = DataFrame(CSV.File(fpath, header=header))
    rename!(df, Dict(Symbol(" value")=>:value))

    # ignore old exchange rates
    old = Date(2015, 01, 01) # make this optional input (supply from expenses/income data)
    df = df[df[:, "date"] .> old, :]

    # add from to info
    from, to = parse_from_to(fpath)
    insertcols!(df, 3, :to_curr=>repeat([to], size(df)[1]))
    insertcols!(df, 3, :from_curr=>repeat([from], size(df)[1]))

    # add a df with reverse exchange rate as well
    df_reverse = copy(df)
    df_reverse[:, "value"] = 1 ./ df[:, "value"]
    rename!(df_reverse, Dict(:to_curr=>:from_curr, :from_curr=>:to_curr))

    return vcat(df, df_reverse)

end

function load_fxs()::DataFrame
    fx_dir = "data/fx/"
    dfs = [load_fxs(fx_dir*fname) for fname in readdir(fx_dir)]
    return vcat(dfs...)
end


function xchange_rate(from_curr::String, to_curr::String, date::Date, fx::DataFrame)::Float64

    # get the subset of rates from the particular currency combination
    xrates = @from i in fx begin
        @where (i.from_curr == from_curr) && (i.to_curr == to_curr)
        @select i
        @collect DataFrame
    end

    # if currency pairs do not exist
    if size(xrates)[1] == 0
        println("WARNING: No exchange rate between $(from_curr) and $(to_curr), using 1.")
        return 1.0
    end

    # try getting an exact rate
    exact_rate = xrates[xrates.date .== date, "value"]
    if length(exact_rate) == 1
        return exact_rate[1]

    # otherwise get an estimate from the closest available day
    else
        days = [abs(Dates.value(d)) for d in xrates.date-date]
        return xrates.value[argmin(days)]
    end

end

function exchange!(exp_df::DataFrame, to_curr::String, fx::DataFrame)::DataFrame

    # loop over all expenses
    for exp in eachrow(exp_df)

        # and convert the spending if needed
        if exp.currency != to_curr

            # determine the xchange rate
            xrate = xchange_rate(exp.currency, to_curr, exp.date, fx)

            # change the amount and the currency
            exp.amount = exp.amount * xrate
            exp.currency = to_curr

        end

    end

    return exp_df
end





