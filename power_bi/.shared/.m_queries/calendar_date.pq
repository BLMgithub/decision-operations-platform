let
    SourceFact = // fact table,
    MaxDateInFact = Date.From(List.Max(SourceFact[week_start_date])),

    // List of dates
    StartDate = #date(2022, 12, 26),
    EndDate = MaxDateInFact,
    CalendarList = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1, 0, 0, 0)),
    
    // Convert to table
    #"Converted to Table" = Table.FromList(CalendarList, Splitter.SplitByNothing(), {"Date"}, null, ExtraValues.Error),
    #"Changed Type" = Table.TransformColumnTypes(#"Converted to Table",{{"Date", type date}}),
    
    // Date format columns
    #"Added Year" = Table.AddColumn(#"Changed Type", "Year", each Date.Year([Date]), Int64.Type),
    #"Added Month" = Table.AddColumn(#"Added Year", "Month", each Date.Month([Date]), Int64.Type),
    #"Added Month Name" = Table.AddColumn(#"Added Month", "Month Name", each Date.MonthName([Date]), type text),
    #"Added Year Month" = Table.AddColumn(#"Added Month Name", "Year Month", each Text.From([Year]) & "-" & Text.PadStart(Text.From([Month]), 2, "0"), type text),
    #"Added Week Number" = Table.AddColumn(#"Added Year Month", "Week Number", each " W" & Text.PadStart(Text.From(Date.WeekOfYear([Date])), 2, "0"), type text),
    // #"Added Year Week" = Table.AddColumn(#"Added Year Month", "Year Week", each Text.From([Year]) & " W" & Text.PadStart(Text.From(Date.WeekOfYear([Date])), 2, "0"), type text),
    #"Added Week Start Date" = Table.AddColumn(#"Added Week Number", "Week Start Date", each Date.StartOfWeek([Date], Day.Monday), type date)
in
    #"Added Week Start Date"