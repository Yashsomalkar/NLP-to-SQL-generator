ddl_list = [
    "CREATE TABLE Company (TargetCompanyId SERIAL PRIMARY KEY,TargetCompanyName VARCHAR(255) NOT NULL,Country VARCHAR(100),IncorporationDate DATE,Sector VARCHAR(100),BusinessDescription TEXT,IsPubliclyListed BOOLEAN);",
    "CREATE TABLE Deals (DealId SERIAL PRIMARY KEY,TargetCompanyId INT REFERENCES Company(TargetCompanyId),Date DATE NOT NULL,TotalAmountInDollarInMillion DECIMAL(18, 2),AmountInRupeeInCrores DECIMAL(18, 2),InvestorsNames TEXT[],DivestorsNames TEXT[],DealType VARCHAR(10) CHECK (DealType IN ('credit', 'equity')));",
    "CREATE TABLE Portfolio (TargetCompanyId INT REFERENCES Company(TargetCompanyId),FundManagerId INT REFERENCES FundManager(FundManagerId),PRIMARY KEY (TargetCompanyId, FundManagerId));",
    "CREATE TABLE FM_Deal (DealId INT REFERENCES Deals(DealId),FundManagerId INT REFERENCES FundManager(FundManagerId),BuyOrSell VARCHAR(4) CHECK (BuyOrSell IN ('buy', 'sell')),Amount DECIMAL(18, 2),Stake DECIMAL(5, 2),PRIMARY KEY (DealId, FundManagerId));",
    "CREATE TABLE FundManager (FundManagerId SERIAL PRIMARY KEY,FundManagerName VARCHAR(255) NOT NULL,Country VARCHAR(100),InterestedSector TEXT[],InterestedGeographies TEXT[]);"
]