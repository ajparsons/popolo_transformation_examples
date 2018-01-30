#Devolved Government Popolo Workflow

Previously I showed [how to analyse EveryPolitician data in R](https://github.com/ajparsons/everypoliticianR). This repository contains three examples of how to use Python to patch holes in [EveryPolitician data](http://everypolitician.org/) so the same cross-analysis tools can be used on incomplete datasets.

In this case, my goal was to have a single analysis process for the Scottish Parliament, the National Assembly for Wales and the London Assembly. The first step in this is to have all the data in the same format - but while most of the data I needed was in EveryPolitician, in all cases it was slightly incomplete for my purposes. 

Rather than convert the json-popolo file EveryPolitician provides the data in into a CSV and joining it with other information there, I decided to modify the popolo files to include the new information to keep the advantage of popolo specific libraries and methods. 

As the end result is three json files - this can be easily be accessed by Python or R analysis libraries. 

##Why use popolo in a research workflow

EveryPolitician publishes information as CSVs, but also as json files using the [popolo format](http://www.popoloproject.com/).
 
This makes popolo files very useful as a single-structured store of information for use in future analysis. It can contain term dates, bibliographic information, constituency information and - mostly conceptually useful is that it has the concept of 'memberships'. A membership is a relationship between a person, a legislative body, a party and a time-period. This means that an MP who is re-elected in a new legislative term has two memberships, and also if an MP changes party they will have two memberships.

While this is sometimes over-precise, as a basic building block it enables lots of different forms of analysis and is a generally useful way to have raw political data stored - the nuance can be thrown away later in the workflow depending on the question under investigation. 

##Data fixes

###Scottish Parliament

[scottish_parliament.py](scottish_parliament.py): For the Scottish Assembly, EveryPolitician [covers the entire history](http://everypolitician.org/scotland/parliament/download.html) - but it's missing some birth dates for MSPs. This script downloads the Scottish Parliament data from EveryPolitician and infills the popolo file to infill the missing dates.

###London Assembly

[london_assembly.py](london_assembly.py): Creates a popolo file from scatch, given a CSV of membership information and term information. 

###National Assembly for Wales

[welsh_assembly.py](welsh_assembly.py): Creates a new popolo file for the first three terms of the National Assembly for Wales (currently not in EveryPolitician) and then merges that with the [EveryPolitician popolo](http://everypolitician.org/wales/assembly/download.html) to create one file. 


##Read-write popolo from Python

The ability to write back to the file haven't been fed back into the main version of the popolo-python package yet, but if you want to do an exercise like the above you can install the package directly from git:

```
pip install git+https://github.com/ajparsons/everypolitician-popolo-python.git@export_merge_function#egg=everypolitician-popolo
```

#Using this data

This data can then be accessed using the popolo packages for [Python](https://github.com/everypolitician/everypolitician-popolo-python), [Ruby](https://github.com/everypolitician/everypolitician-popolo) and [R](https://github.com/ajparsons/everypoliticianR). 
