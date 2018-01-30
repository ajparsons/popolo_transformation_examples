"""
Creates a popolo file for the London Assembly from CSVs
"""
import hashlib, unidecode

import sys

from popolo_data.importer  import Popolo
from popolo_data.models import Person, Area,Membership, Organization, Event

reload(sys)
sys.setdefaultencoding('cp1252')

from useful_inkleby.files import QuickGrid

def get_hash(v):
    """
    create a hash to function as an id
    """
    m = hashlib.sha256()
    combo = [v]
    combo = [str(unidecode.unidecode(x)) for x in combo if x]
    combo = "".join(combo)
    m.update(combo)
    return m.hexdigest()

def csv_to_popolo(organisation,membership_file,term_dates_file):
    """
    given a organisation name, a csv file with membership information
    and a file with the relevant term dates - creates a popolo.
    """
    unique = lambda x: list(set(x))
    
    if isinstance(organisation,tuple):
        org_id, org_name = organisation
    else:
        org_name = organisation
        org_id = get_hash(org_name)
    
    qg = QuickGrid().open(membership_file)
    dates = QuickGrid().open(term_dates_file)
        
    pop = Popolo()
    
    org = Organization(classification = "legislature",
                       id = org_id,
                       name = org_name
                       )
    
    pop.add(org)
    
    for d in dates:
        e = Event()
        e.classification = "legislative period"
        e.id = "term/{0}".format(d["term"])
        if d["start_date"]:  
            e.start_date = d["start_date"]
        if d["end_date"]:  
            e.end_date = d["end_date"]
        e.organization = org
        pop.add(e)
    
    groups = unique(qg.get_column("group"))
    areas = unique(qg.get_column("area"))
    
    for g in groups:
        o = Organization(classification="party",name=g,id=get_hash(g))
        pop.add(o)
        
    for a in areas:
        n = Area(name=a,id=get_hash(a),type="constituency")
        pop.add(n)
        
    qg.generate_col("l_name", lambda x:x["name"].strip().lower().replace(" ",""))
        
    for k,nqg in qg.split_on_unique("l_name"):
        sources = unique([x["source"] for x in nqg])
        alternates = []
        if "other_names" in qg.header:
            alt_names = [x["other_names"] for x in nqg]
            alternates = []
            for al in alt_names:
                if al:
                    for a in al.split(";"):
                        alternates.append({"name":a,
                                            "lang":"en",
                                            "note":"altname"
                                            })
    
        p = Person(name = nqg[0]["name"],
                   id = get_hash(k),
                   sources = sources
                   )
        
        if "gender" in nqg.header:
            p.gender = nqg[0]["gender"]
            
        
        if alternates:
            p.other_names = alternates
        pop.add(p)
        
    for r in qg:
        m = Membership()
        m.person = pop.persons.lookup_from_key[get_hash(r["l_name"])]
        m.area = pop.areas.lookup_from_key[get_hash(r["area"])]
        m.on_behalf_of = pop.organizations.lookup_from_key[get_hash(r["group"])]
        m.legislative_period = pop.events.lookup_from_key["term/{0}".format(r["term"])]
        m.organization = org
        m.role = "member"
        
        if r["start_date"]:
            m.start_date = r["start_date"]
        
        if r["end_date"]:
            m.end_date = r["end_date"]    
            
        pop.add(m)
      
    return pop  


def create_popolo_london():
    """
    create london assembly json from csv files of term dates and memberships
    """
    pop = csv_to_popolo(
           "London Assembly",
           r"london_assembly\london_assembly.csv",
           r"london_assembly\london_assembly_dates.csv")
    pop.to_filename(r"london_assembly\london_assembly.json")

        
if __name__ == "__main__":
    create_popolo_london()
