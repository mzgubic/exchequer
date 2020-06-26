include("src/Exchequer.jl")

using .Exchequer

Exchequer.move_downloads()
df_expenses = Exchequer.load_expenses()
df_incomes = Exchequer.load_incomes()
df_fxs = Exchequer.load_fxs()

Exchequer.exchange!(df_expenses, "EUR", df_fxs)

nothing
