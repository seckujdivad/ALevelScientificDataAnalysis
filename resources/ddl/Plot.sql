CREATE TABLE "Plot" (
	"PlotID"	INTEGER NOT NULL,
	"VariableXID"	INTEGER,
	"VariableYID"	INTEGER,
	"VariableXTitle"	TEXT,
	"VariableYTitle"	TEXT,
	"ShowRegression"	INTEGER,
	PRIMARY KEY("PlotID")
)