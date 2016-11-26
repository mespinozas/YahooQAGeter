from crawler import question
with open('notFounded.txt','w+') as of:
	with open('ids.txt','rU') as f:
	    qids = f.readlines();
	    for qid in qids:
	        # print(qid)
	        try: 
	    		test = question(qid)
	    		test.makeFinalXML()
	    	except IndexError:
	    		text = '{},0,0'.format(qid)
	    		of.write(text)
