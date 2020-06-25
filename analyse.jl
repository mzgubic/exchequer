include("src/Exchequer.jl")

using .Exchequer

Exchequer.move_downloads()
df_expenses = Exchequer.load_expenses()
