allowed_commands = ["SELECT"]
allowed_tables = ["FundManager", "Company", "Deals", "Portfolio", "FM_Deal", "FundManager"]
allowed_columns = {
    "Company": [
        "TargetCompanyId",
        "TargetCompanyName",
        "Country",
        "IncorporationDate",
        "Sector",
        "BusinessDescription",
        "IsPubliclyListed"
    ],
    "Deals": [
        "DealId",
        "TargetCompanyId",
        "Date",
        "TotalAmountInDollarInMillion",
        "AmountInRupeeInCrores",
        "InvestorsNames",
        "DivestorsNames",
        "DealType"
    ],
    "Portfolio": [
        "TargetCompanyId",
        "FundManagerId"
    ],
    "FM_Deal": [
        "DealId",
        "TargetCompanyId",
        "FundManagerId",
        "BuyOrSell",
        "Amount",
        "Stake"
    ],
    "FundManager": [
        "FundManagerId",
        "FundManagerName",
        "Country",
        "InterestedSector",
        "InterestedGeographies"
    ]
}