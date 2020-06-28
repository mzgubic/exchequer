module Exchequer

using CSV
using ColorSchemes
using DataFrames
using Dates
using Plots
using Query

export move_downloads
export load_expenses, load_incomes, load_fxs
export exchange!
export aggregate
export plot_categories, plot_monthly, plot_weekly

COLORS = colorschemes[:Paired_12][1:end]
MONTHS = Dict(1=>"Jan", 2=>"Feb", 3=>"Mar", 4=>"Apr", 5=>"May", 6=>"Jun",
             7=>"Jul", 8=>"Aug", 9=>"Sep", 10=>"Oct", 11=>"Nov", 12=>"Dec")

include("preprocessing.jl")
include("aggregation.jl")
include("plotting.jl")

end
