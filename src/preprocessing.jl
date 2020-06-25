
function move_downloads()

    dl_dir = "/Users/mzgubic/Downloads/"
    for fname in readdir(dl_dir) # TODO: change to ~

        # order matters
        if occursin("Income", fname)
            println(fname)
            mv(dl_dir*fname, "data/income/"*fname)

        elseif occursin("Expenses", fname)
            println(fname)
            mv(dl_dir*fname, "data/expense/"*fname)

        elseif occursin("exchange", fname)
            println(fname)
            mv(dl_dir*fname, "data/fx/"*fname)
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
            println(date)
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

