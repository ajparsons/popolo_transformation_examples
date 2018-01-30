"""
Update scottish parliament popolo with birthdates
Also
"""
import hashlib, unidecode

import datetime
import requests
import sys

from popolo_data.importer  import Popolo
from popolo_data.models import Person, Area,Membership, Organization, Event
import wikipedia
from everypolitician import EveryPolitician

reload(sys)
sys.setdefaultencoding('cp1252')

from useful_inkleby.files import QuickGrid

def download(country,legislature,destination):
    """
    download current info from ep to file
    """
    ep = EveryPolitician()
    country, leg = ep.country_legislature(country,legislature)
    url = leg.popolo_url
    js = requests.get(url).content
    with open(destination, 'w') as f:
        f.write(js)

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
    #create legislature
    org = Organization(classification = "legislature",
                       id = org_id,
                       name = org_name
                       )
    
    pop.add(org)
    
    #create periods
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
    
    #create parties
    for g in groups:
        o = Organization(classification="party",name=g,id=get_hash(g))
        pop.add(o)
        
    #create constituencies
    for a in areas:
        n = Area(name=a,id=get_hash(a),type="constituency")
        pop.add(n)
        
    qg.generate_col("l_name", lambda x:x["name"].strip().lower().replace(" ",""))
    
    #create people
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
    
    #create memberships
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

def get_wikipedia_from_wikidata(id):
    """
    given a wikidata id - retrieve the english wikipage
    """
    import urllib, json
    form = "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=sitelinks&ids={0}&sitefilter=enwiki"    
    q = form.format(id.strip())
    response = urllib.urlopen(q)
    data = json.loads(response.read())
    if "entities" in data:
        site = data["entities"][id.strip()]["sitelinks"]
        if site:
            return site["enwiki"]["title"]

    return None

def get_birthdates_from_wikidata():
    """
    for scottish parliament - look up and extract birthdates from wikipedia
    where absence
    """
        
    def extract_date(v):
        if "(born" not in v:
            return "missing"
        start = v.find("(born")
        end = v.find(")",start)
        date = v[start+6:end]
        try:
            d = datetime.datetime.strptime(date,"%d %B %Y")
            return d.isoformat()
        except ValueError:
            return date
        
    def get_from_html(v):
        if "Born</th><td>" not in v:
            return "missing"
        start = v.find("Born</th><td>")
        end = v.find("</td>",start)
        date = v[start+len("Born</th><td>"):end].strip()
        try:
            d = datetime.datetime.strptime(date,"%d %B %Y")
            return d.isoformat()
        except ValueError:
            return date
        
        qg = QuickGrid().open(r"scottish_parliament\missing_birthdates.csv")
        for r in qg:
            if r["birth_date"] in ["",None,"missing"]:
                title = get_wikipedia_from_wikidata(r["wikidata"])
                print title
                if title:
                    try:
                        page = wikipedia.page(title)
                    except:
                        page = None
                    if page:
                        content = page.content
                        #print content
                        date = extract_date(content)
                        if date == "missing":
                            date = get_from_html(page.html())
                        print date
                    else:
                        date = "missing"
                    r["birth_date"] = date
                    qg.save()
                
def update_birthdates_from_file(popolo,update,output):
    """
    join updated birthdate information with the popolo file
    """
    qg = QuickGrid().open(update)
    pop = Popolo.from_filename(popolo)
    
    for r in qg:
        p = pop.persons.lookup_from_key[r["id"]]
        if r["birth_date"]:
            p.birth_date = r["birth_date"]
            print p.birth_date
    pop.to_filename(output)
    
def update_scottish_parliament():
    """
    download the ep data and update with missing birthdates
    (for creating age variables)
    """
    source = r"scottish_parliament\current_ep_scotland.json"
    update = r"scottish_parliament\missing_birthdates.csv"
    output = r"scottish_parliament\current_ep_scotland_with_birthdates.json"

    download("Scotland","Parliament",source)

    update_birthdates_from_file(source,update,output)

if __name__ == "__main__":
    update_scottish_parliament()