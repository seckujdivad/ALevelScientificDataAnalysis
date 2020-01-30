import typing

import sciplot.database

def get_composite_id(database: sciplot.database.DataFile, unit_table: typing.List[typing.Tuple[int, float]]):
    unitcomposite_ids = [tup[0] for tup in database.query(sciplot.database.Query("SELECT UnitCompositeID FROM UnitComposite", [], 1))[0]]

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
    

def prune_unused_composites():
    pass