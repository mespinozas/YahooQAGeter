from crawler import question

with open('ids.txt','rU') as f:
    qids = f.readlines();
    for qid in qids:
        # print(qid)
        test = question(qid)
        test.makeFinalXML()
