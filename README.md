# YahooQAGeter
Get from QA comunity (cQA) Yahoo Answer! question, answer and metadata to xml or json.  Just using QID. Python code

Require lxml lib (sudo apt-get install python-lxml)

Example, from https://answers.yahoo.com/question/index?qid=20150715065224AAL3wcg question:

---- Code ----
from crawler import question

test = question("20150715065224AAL3wcg")
test.makeFinalXML()


#Show you all xml as string, ready to make a file
print test.finalXMLString
#Show you all xml parsed as JSON format
print test.final

#Alternatives
#you can use test.getAll(), only for class and atribute objects
#makeFinalXML()

#test.xml got parsed xml from page
#test.finalXML #got a lxml object with all pages and metadata, cleared.

----- end code ----
