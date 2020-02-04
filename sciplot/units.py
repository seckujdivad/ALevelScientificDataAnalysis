import typing

import sciplot.database

def get_composite_id(database: sciplot.database.DataFile, unit_table: typing.List[typing.Tuple[int, float]]):
    unitcomposite_ids = [tup[0] for tup in database.query(sciplot.database.Query("SELECT UnitCompositeID FROM UnitComposite;", [], 1))[0]]

    match_found = False
    i = 0
    while i < len(unitcomposite_ids) and not match_found:
        scan_units = database.query(sciplot.database.Query("SELECT UnitCompositeDetails.UnitID, UnitCompositeDetails.Power FROM UnitComposite INNER JOIN UnitCompositeDetails ON UnitCompositeDetails.UnitCompositeID = UnitComposite.UnitCompositeID WHERE UnitComposite.UnitCompositeID = (?);", [unitcomposite_ids[i]], 1))[0]
        
        if set(scan_units) == set(unit_table):
            match_found = True

        i += 1

    if match_found:
        return unitcomposite_ids[i - 1]
    
    else:
        return -1

def create_composite(database: sciplot.database.DataFile, symbol: str, unit_table: typing.List[typing.Tuple[int, float]]):
    primary_key = database.query([sciplot.database.Query("INSERT INTO UnitComposite (`Symbol`) VALUES ((?))", [symbol], 0),
                                  sciplot.database.Query("SELECT last_insert_rowid();", [], 2)])[0][0]
    
    queries = []
    
    for unit_id, power in unit_table:
        queries.append(sciplot.database.Query("INSERT INTO UnitCompositeDetails (`UnitCompositeID`, `UnitID`, `Power`) VALUES ((?), (?), (?))", [primary_key, unit_id, power], 0))

    database.query(queries)

    return primary_key

def rename_composite(database: sciplot.database.DataFile, primary_key: int, symbol: str):
    database.query(sciplot.database.Query("UPDATE UnitComposite SET Symbol = (?) WHERE UnitCompositeID = (?);", [symbol, primary_key], 0))

def remove_composite(database: sciplot.database.DataFile, primary_key: int):
    database.query(sciplot.database.Query("DELETE FROM UnitComposite WHERE UnitCompositeID = (?)", [primary_key], 0))

def update_composite(database: sciplot.database.DataFile, primary_key: int, unit_table: typing.List[typing.Tuple[int, float]]):
    queries = [sciplot.database.Query("DELETE FROM UnitCompositeDetails WHERE UnitCompositeID = (?)", [primary_key], 0)]
    for unit_id, power in unit_table:
        queries.append(sciplot.database.Query("INSERT INTO UnitCompositeDetails (`UnitCompositeID`, `UnitID`, `Power`) VALUES ((?), (?), (?))", [primary_key, unit_id, power], 0))