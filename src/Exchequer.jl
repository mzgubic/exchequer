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
export plot_categories, plot_monthly

colors = colorschemes[:Paired_12][1:end]

include("preprocessing.jl")
include("aggregation.jl")
include("plotting.jl")

end
