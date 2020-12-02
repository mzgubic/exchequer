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
MONTHS = Dict(1=>"J", 2=>"F", 3=>"M", 4=>"A", 5=>"M", 6=>"J",
             7=>"J", 8=>"A", 9=>"S", 10=>"O", 11=>"N", 12=>"D")

include("preprocessing.jl")
include("aggregation.jl")
include("plotting.jl")

end
